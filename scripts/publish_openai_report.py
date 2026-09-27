"""Publish a reading copy of the frozen v1.1 report, not a new incident analysis."""
from __future__ import annotations
import base64
import csv
import gzip
import hashlib
import html
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'OpenAI/2026-09-27/v1.1'
STEM = 'OpenAI_Reliability_Report_2026-09-27_v1.1'
CHARTS = DEST / 'OpenAI_Reliability_Trends_2026-09-27'
MD_SHA = 'ddcaa1bf2830002a2dd30c7497221a51a35e1ddb33369f6f856909095acf9598'
DATA_SHA = 'a6076510b063149e2bdf659395caf294addfad060507f94500601be72ccd2b5f'

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> None:
    md_path = DEST / (STEM + '.md')
    md_bytes = md_path.read_bytes()
    # Restore the original final blank line if omitted during the text upload.
    if sha(md_bytes) != MD_SHA and sha(md_bytes + b'\n') == MD_SHA:
        md_bytes += b'\n'
        md_path.write_bytes(md_bytes)
    if sha(md_bytes) != MD_SHA:
        raise ValueError('The report text differs from the archived original.')
    encoded_path = DEST / 'trend_data.json.gz.b64'
    data_path = DEST / 'trend_data.json'
    if encoded_path.exists():
        encoded = encoded_path.read_text().strip()
        # Correct one identified transport typo; the full decoded SHA is mandatory.
        encoded = encoded.replace('O73KdZ5PPW', 'O73KdzZPPW')
        data_bytes = gzip.decompress(base64.b64decode(encoded, validate=True))
    else:
        data_bytes = data_path.read_bytes()
    if sha(data_bytes) != DATA_SHA:
        raise ValueError('The frozen trend dataset failed its original SHA-256 check.')
    data_path.write_bytes(data_bytes)
    if encoded_path.exists():
        encoded_path.unlink()
    data = json.loads(data_bytes)
    annual = data['annual']
    assert len(annual) == 24
    lookup = {(row['year'], row['group']): row for row in annual}
    assert [lookup[y, 'Overall']['incident_count'] for y in range(2021, 2027)] == [10, 43, 172, 187, 339, 255]
    for rows, name in [(annual, 'annual_trend_data.csv'), (data['matched_windows'], 'matched_window_trend_data.csv')]:
        fields = list(dict.fromkeys(key for row in rows for key in row))
        with (DEST / name).open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    subprocess.run([sys.executable, str(ROOT / 'scripts/render_openai_trends.py'), '--data', str(data_path), '--assets', str(CHARTS)], check=True)
    assert len(list(CHARTS.glob('*.svg'))) == 18
    assert len(list(CHARTS.glob('*.png'))) == 9

    # Re-render the two overview figures referenced by the unchanged Markdown.
    import matplotlib.pyplot as plt
    years = list(range(2021, 2027))
    fig, ax = plt.subplots(figsize=(10.8, 4.8), dpi=160)
    bars = ax.bar([str(y) + ('*' if y in (2021, 2026) else '') for y in years],
                  [lookup[y, 'Overall']['incident_count'] for y in years])
    ax.bar_label(bars, padding=5)
    ax.set_title('Publicly reported OpenAI incidents', loc='left', fontsize=17, pad=16)
    ax.set_ylabel('Distinct incident IDs (maintenance excluded)')
    ax.set_ylim(0, 390)
    ax.spines[['top', 'right']].set_visible(False)
    fig.text(0.08, 0.02, '* 2021 starts February 1; 2026 ends September 26, 22:51 UTC. Not a failure-rate measure.', fontsize=9)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(DEST / 'annual_incidents.png', bbox_inches='tight')
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10.8, 5.2), dpi=160)
    keys = ['availability_full', 'availability_full_partial', 'availability_all']
    for group in ['APIs', 'ChatGPT', 'Codex']:
        values = [100 * lookup[2026, group][key] for key in keys]
        ax.plot(range(3), values, marker='o', linewidth=2, label=group)
        ax.annotate(f'{values[-1]:.2f}%', (2, values[-1]), xytext=(8, 0), textcoords='offset points', va='center', fontsize=10)
    ax.set_xticks(range(3), ['Full only', 'Full + Partial', 'All impact levels'])
    ax.set_ylabel('Unimpacted-time proxy (%)')
    ax.set_title('2026: availability depends on the impact definition', loc='left', fontsize=16, pad=16)
    ax.set_ylim(85, 101)
    ax.set_xlim(-0.10, 2.45)
    ax.legend(loc='lower left', frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    fig.text(0.08, 0.02, 'Any affected component in each group; unknown intervals excluded. Not request success or official uptime.', fontsize=9)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(DEST / 'availability_modes_2026.png', bbox_inches='tight')
    plt.close(fig)

    import mistune
    source = md_bytes.decode('utf-8')
    render = mistune.create_markdown(escape=True, plugins=['table'])
    body = render(source)
    def uri(path: Path) -> str:
        mime = 'image/svg+xml' if path.suffix == '.svg' else 'image/png'
        return 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode()
    def embed(match: re.Match[str]) -> str:
        relative, alt = html.unescape(match[1]), match[2]
        image = (DEST / relative).resolve()
        if not image.is_relative_to(DEST.resolve()) or not image.is_file():
            raise ValueError('Missing or unsafe figure path: ' + relative)
        fallback = '<img src="' + uri(image) + '" alt="' + alt + '" loading="lazy">'
        mobile = image.with_name(image.stem + '_mobile.svg')
        if image.suffix == '.svg' and mobile.exists():
            return '<picture><source media="(max-width: 700px)" srcset="' + uri(mobile) + '">' + fallback + '</picture>'
        return fallback
    body = re.sub(r'<img src="([^"]+)" alt="([^"]*)"\s*/?>', embed, body)
    body = body.replace('<table>', '<div class="table-wrap"><table>').replace('</table>', '</table></div>')
    headings = []
    def heading(match: re.Match[str]) -> str:
        level, text = match[1], match[2]
        anchor = 'section-' + str(len(headings) + 1)
        headings.append((anchor, re.sub('<[^>]+>', '', text)))
        return '<h' + level + ' id="' + anchor + '">' + text + '</h' + level + '>'
    body = re.sub(r'<h([23])>(.*?)</h\1>', heading, body)
    toc = '<nav aria-label="报告目录">' + ''.join('<a href="#' + anchor + '">' + html.escape(text) + '</a>' for anchor, text in headings) + '</nav>'
    notice = ('这是 GitHub 阅读副本：由同一 v1.1 Markdown 原稿、冻结绘图数据及原始趋势绘图脚本生成。'
              '正文与数据经原始 SHA-256 验证；配图重新渲染。它不是资料库原始 HTML 的逐字节副本，'
              '不包含原始 HTML 的 1,006 起事故交互索引，也不包含完整事故审计 ZIP。')
    css = 'html{scroll-behavior:smooth}body{font:18px/1.85 system-ui,-apple-system,"Noto Sans CJK SC",sans-serif;max-width:1160px;margin:0 auto;padding:30px;color:#172536;background:#fafbfd}main{background:white;padding:32px;border-radius:16px}h1{font-size:34px;line-height:1.4}h2{font-size:27px;margin-top:55px;scroll-margin-top:20px}h3{font-size:22px;margin-top:30px}a{color:#126b92}aside{padding:18px 24px;border:1px solid #a8bdcc;border-radius:12px;background:#eff6fa;margin-bottom:20px}nav{display:flex;flex-wrap:wrap;gap:8px 20px;margin:25px 0}nav a{font-size:15px}.table-wrap{overflow-x:auto}table{border-collapse:collapse;font-size:14px;width:100%;margin:18px 0}th,td{text-align:left;padding:10px;border-bottom:1px solid #dce4ea;white-space:nowrap}th{background:#eff3f6}blockquote{border-left:4px solid #9eb3c3;padding:5px 18px;background:#f4f7fa;margin:22px 0}code,pre{font-family:ui-monospace,monospace}pre{padding:15px;background:#f1f5f8;overflow:auto}img{max-width:100%;height:auto}picture{display:block}button{font:inherit;padding:8px 15px;cursor:pointer}@media(max-width:700px){body{padding:12px;font-size:17px}main{padding:17px}h1{font-size:28px}h2{font-size:23px}aside{padding:14px}}@media print{nav,button{display:none}body{max-width:none;padding:0}main{padding:0}h2{break-after:avoid}img{break-inside:avoid}}'
    document = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OpenAI 可靠性报告 v1.1 · GitHub 阅读副本</title><style>' + css + '</style></head><body><aside><strong>GitHub 阅读副本</strong><br>' + notice + '</aside><button onclick="window.print()">打印 / 保存 PDF</button>' + toc + '<main>' + body + '</main></body></html>\n'
    reader_name = STEM + '_github.html'
    (DEST / reader_name).write_text(document, encoding='utf-8')
    manifest = {
        'kind': 'GitHub reading copy; not original audit package',
        'version': 'v1.1', 'data_cutoff_utc': data['cutoff_utc'],
        'source_markdown_sha256': sha(md_bytes), 'source_trend_data_sha256': sha(data_bytes),
        'original_markdown_preserved_byte_for_byte': True,
        'charts_rerendered_from_original_script_and_data': True,
        'original_interactive_html_uploaded': False,
        'original_audit_zip_uploaded': False,
        'full_incident_index_included': False,
        'statistics_reclassified_or_refreshed': False,
        'files': {p.relative_to(DEST).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
                  for p in sorted(DEST.rglob('*')) if p.is_file() and p.suffix in {'.md', '.html', '.svg', '.png', '.csv', '.json'}
                  and p.name not in {'publication_manifest.json', 'README.md'}}
    }
    (DEST / 'publication_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    readme = '# OpenAI 可靠性报告 v1.1 · GitHub 归档\n\n' + notice + '\n\n'
    readme += '- [完整 Markdown 原稿](' + STEM + '.md)\n- [单文件 HTML 阅读副本](' + reader_name + ')（下载后打开，无需联网）\n- [阅读资料包](OpenAI_Reliability_Reading_Package_2026-09-27_v1.1.zip)\n- [年度图表数据](annual_trend_data.csv)\n- [同期对比数据](matched_window_trend_data.csv)\n- [文件与数据校验记录](publication_manifest.json)\n\n'
    readme += '本目录的 ZIP 是阅读资料包，不是原始完整审计 ZIP；不包含冻结的 1,007 行原始事故 CSV、逐事故重分类/阶段明细或事故可用性复算脚本。原始完整材料仍保存在资料库。\n\n'
    readme += '图表使用原有数值，不重新采集状态页，不修改事故等级或截止时间。空心点和虚线继续区分短年度与 2026 年内快照。\n'
    (DEST / 'README.md').write_text(readme, encoding='utf-8')
    archive = DEST / 'OpenAI_Reliability_Reading_Package_2026-09-27_v1.1.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(DEST.rglob('*')):
            if path.is_file() and path != archive and path.name != 'reading_package.sha256':
                bundle.write(path, 'OpenAI_v1.1/' + path.relative_to(DEST).as_posix())
        bundle.write(ROOT / 'scripts/render_openai_trends.py', 'OpenAI_v1.1/render_openai_trends.py')
    (DEST / 'reading_package.sha256').write_text(sha(archive.read_bytes()) + '  ' + archive.name + '\n')
    print(json.dumps({'markdown_sha256': sha(md_bytes), 'trend_data_sha256': sha(data_bytes), 'charts': 9, 'svg_files': 18, 'html': reader_name, 'zip': archive.name, 'original_audit_zip_uploaded': False}, ensure_ascii=False))

if __name__ == '__main__':
    main()
