"""Offline reading-copy builder; frozen inputs are never rewritten."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from urllib.parse import unquote, urlsplit
import base64
import csv
import html
import importlib.metadata
import json
import os
import re
import shutil
import tempfile
import zipfile

from . import __version__
from .model import Report, child, relative_path, require, sha256
from .charts import render_charts

FORMAT = "ai-reliability-reading/v1"
NOTICE = ("本文件由冻结报告正文及统计数据生成，是阅读副本，不是新的事故分析。"
          "不采集事故、不重新判级、不重算原始事故时间并集；"
          "不包含完整原始事故数据、逐事故审计材料或事故交互索引。"
          "可用性为公开记录估计，不是官方 SLA 或真实请求成功率。")
CSS = """
body{font:18px/1.85 system-ui,sans-serif;max-width:1160px;margin:auto;padding:28px}
h1{line-height:1.35;font-size:32px}h2{margin-top:45px;font-size:26px}h3{font-size:22px}
aside,blockquote{padding:16px;border:1px solid;border-radius:8px}nav{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}
nav a{font-size:15px}.table-wrap{overflow:auto}table{border-collapse:collapse;font-size:14px;width:100%}
th,td{padding:10px;border-bottom:1px solid;text-align:left;white-space:nowrap}
img{max-width:100%;height:auto}picture{display:block}pre{overflow:auto;padding:14px;border:1px solid}
@media(max-width:700px){body{padding:14px;font-size:17px}h1{font-size:27px}h2{font-size:23px}}
@media print{nav,button{display:none}body{max-width:none;padding:0}img{break-inside:avoid}}
"""


def render_html(report: Report, destination: Path) -> str:
    import mistune
    headings: list[tuple[str, str]] = []

    class Renderer(mistune.HTMLRenderer):
        def heading(self, text: str, level: int, **attrs) -> str:
            anchor = f"section-{len(headings) + 1}"
            headings.append((anchor, re.sub("<[^>]+>", "", text)))
            return f'<h{level} id="{anchor}">{text}</h{level}>\n'

        def image(self, text: str, url: str, title: str | None = None) -> str:
            parsed = urlsplit(url)
            require(not parsed.scheme and not parsed.netloc and not parsed.query and not parsed.fragment,
                    f"Offline images must use local relative paths: {url}")
            relative = unquote(parsed.path)
            target = child(destination, relative)
            if not target.exists():
                source = child(report.markdown_path.parent, relative)
                require(source.is_file(), f"Referenced image does not exist: {relative}")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            def uri(path: Path) -> str:
                types = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
                require(path.suffix.lower() in types, f"Unsupported image format: {path}")
                return "data:" + types[path.suffix.lower()] + ";base64," + base64.b64encode(path.read_bytes()).decode("ascii")
            alt = html.escape(re.sub("<[^>]+>", "", html.unescape(text)), quote=True)
            image = f'<img src="{uri(target)}" alt="{alt}" loading="lazy">'
            mobile = child(destination, str(Path(relative).with_name(Path(relative).stem + "_mobile.svg")))
            if target.suffix == ".svg" and mobile.is_file():
                return f'<picture><source media="(max-width:700px)" srcset="{uri(mobile)}">{image}</picture>'
            return image

    markdown = mistune.create_markdown(renderer=Renderer(escape=True), plugins=["table"])
    body = markdown(report.markdown_bytes.decode("utf-8"))
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    toc = '<nav aria-label="报告目录">' + "".join(f'<a href="#{a}">{html.escape(html.unescape(t))}</a>' for a, t in headings) + "</nav>"
    title = html.escape(report.config["report"]["title"] + " · " + report.config["report"]["version"])
    badge = "【合成示例数据，不代表任何真实公司】" if report.config.get("synthetic", False) else "阅读副本"
    integrity = report.config.get("integrity", {})
    verification = ("已通过配置中固定的两项 SHA-256 校验。" if all(integrity.get(k) for k in ("markdown_sha256", "data_sha256"))
                    else "未同时固定两项输入校验值；实际 SHA-256 见构建清单。")
    return (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{CSS}</style></head><body><aside><strong>{badge}</strong><br>{NOTICE}<br>'
            f'{verification}</aside>{toc}<main>{body}</main></body></html>\n')


def write_csv(path: Path, rows: list[dict]) -> None:
    # Structured values remain JSON; use only the explicit supplied/derived rows.
    fields = list(dict.fromkeys(key for row in rows for key in row))
    if not fields:
        fields = ["year", "group", "incident_count"]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()} for row in rows)


def check_destination(report: Report, output: Path, overwrite: bool) -> None:
    require(not output.is_symlink(), "Output directory cannot be a symlink")
    target = output.resolve()
    for source in (report.markdown_path, report.data_path, report.config_path):
        require(not source.is_relative_to(target), "Output directory cannot contain an input file")
    if not target.exists():
        return
    require(target.is_dir(), "Output is not a directory")
    if not any(target.iterdir()):
        return
    require(overwrite, "Output is non-empty; use --overwrite only for a prior generated reading copy")
    marker = target / "publication_manifest.json"
    require(marker.is_file() and not marker.is_symlink(), "Refusing to overwrite an unowned output directory")
    previous = json.loads(marker.read_text(encoding="utf-8"))
    require(previous.get("artifact_format") == FORMAT and previous.get("company", {}).get("id") == report.config["company"]["id"],
            "Refusing to overwrite another company's output or an archived report")
    owned = set(previous["files"]) | {"publication_manifest.json", previous["archive"], "reading_package.sha256"}
    for entry in target.rglob("*"):
        require(not entry.is_symlink(), "Output contains a symlink; overwrite refused")
        require(not entry.is_file() or entry.relative_to(target).as_posix() in owned, f"Unmanaged file in output: {entry.name}")


def build_report(report: Report, output: Path | None = None, *, overwrite: bool = False) -> dict:
    output = output or report.output
    check_destination(report, output, overwrite)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".reliability-build-", dir=output.parent))
    backup = None
    try:
        md_name = report.stem + ".md"
        html_name = report.stem + "_github.html"
        archive_name = report.stem + "_reading.zip"
        (stage / md_name).write_bytes(report.markdown_bytes)
        (stage / "trend_data.json").write_bytes(report.data_bytes)
        charts = render_charts(report, stage)
        write_csv(stage / "annual_trend_data.csv", report.annual)
        write_csv(stage / "matched_window_trend_data.csv", report.matched)
        (stage / html_name).write_text(render_html(report, stage), encoding="utf-8")
        # Portable, self-contained rendering inputs, not a full incident audit package.
        portable = deepcopy(report.config)
        portable["inputs"] = {"markdown": md_name, "data": "trend_data.json"}
        portable["output"]["directory"] = "rebuild"
        portable["integrity"] = {"markdown_sha256": sha256(report.markdown_bytes), "data_sha256": sha256(report.data_bytes)}
        (stage / "report.config.json").write_text(json.dumps(portable, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        scripts = Path(__file__).resolve().parents[1]
        tools = stage / "tools"
        tools.mkdir()
        for name in ("publish_report.py", "render_trends.py"):
            shutil.copyfile(scripts / name, tools / name)
        shutil.copytree(scripts / "reliability", tools / "reliability", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copyfile(scripts.parent / "requirements.txt", stage / "requirements.txt")
        readme = (f'# {report.company} · {report.config["report"]["version"]} · 阅读资料包\n\n{NOTICE}\n\n'
                  f'- [Markdown]({md_name})\n- [HTML]({html_name})\n- [年度数据](annual_trend_data.csv)\n'
                  '- [同期数据](matched_window_trend_data.csv)\n- [校验记录](publication_manifest.json)\n\n'
                  '解压后重新构建（输出到 rebuild，不改原件）：\n\n```sh\n'
                  'python -m pip install -r requirements.txt\n'
                  'python tools/publish_report.py --config report.config.json\n```\n\n'
                  f'冻结截止时间：{report.data["cutoff_utc"]}。图形可能因字体、渲染环境不同而变化；正文及冻结 JSON 保持逐字节一致。\n')
        if report.config.get("synthetic", False):
            readme = "**合成示例数据，不代表任何真实公司。**\n\n" + readme
        (stage / "README.md").write_text(readme, encoding="utf-8")
        manifest = {
            "artifact_format": FORMAT, "generator_version": __version__,
            "company": report.config["company"], "report": report.config["report"],
            "synthetic": report.config.get("synthetic", False), "data_cutoff_utc": report.data["cutoff_utc"],
            "source_markdown_sha256": sha256(report.markdown_bytes), "source_trend_data_sha256": sha256(report.data_bytes),
            "input_hashes_pinned": {k: bool(report.config.get("integrity", {}).get(k)) for k in ("markdown_sha256", "data_sha256")},
            "original_markdown_preserved_byte_for_byte": True, "statistics_reclassified_or_refreshed": False,
            "full_incident_index_included": False, "original_audit_zip_included": False,
            "years": report.years, "groups": [g["id"] for g in report.groups], "chart_files": len(charts),
            "dependencies": {name: importlib.metadata.version(name) for name in ("matplotlib", "mistune")},
            "archive": archive_name,
            "files": {p.relative_to(stage).as_posix(): {"bytes": p.stat().st_size, "sha256": sha256(p.read_bytes())}
                      for p in sorted(stage.rglob("*")) if p.is_file()},
        }
        (stage / "publication_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # Deterministic archive order/timestamps; never package neighboring or stale files.
        with zipfile.ZipFile(stage / archive_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for path in sorted(stage.rglob("*")):
                if path.is_file() and path.name != archive_name:
                    info = zipfile.ZipInfo(path.relative_to(stage).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    bundle.writestr(info, path.read_bytes())
        (stage / "reading_package.sha256").write_text(sha256((stage / archive_name).read_bytes()) + "  " + archive_name + "\n", encoding="utf-8")
        # Only swap a fully generated and validated directory into place.
        check_destination(report, output, overwrite)
        if output.exists():
            backup = Path(tempfile.mkdtemp(prefix=".reliability-backup-", dir=output.parent))
            backup.rmdir()
            os.replace(output, backup)
        try:
            os.replace(stage, output)
        except Exception:
            if backup is not None:
                os.replace(backup, output)
                backup = None
            raise
        if backup is not None:
            shutil.rmtree(backup)
        return {"company": report.company, "output": str(output), "html": html_name,
                "archive": archive_name, "years": report.years, "chart_files": len(charts),
                "source_markdown_sha256": sha256(report.markdown_bytes), "source_trend_data_sha256": sha256(report.data_bytes)}
    finally:
        if stage.exists():
            shutil.rmtree(stage)
