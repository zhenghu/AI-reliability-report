"""Data-driven trends. No provider, year range, axis limits or service count is fixed."""
from __future__ import annotations

from copy import copy
from pathlib import Path
import math

from .model import Report, METRICS, AVAILABILITY, child


def render_charts(report: Report, output: Path) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.ticker import FuncFormatter, MaxNLocator

    available = {f.name for f in font_manager.fontManager.ttflist}
    fonts = [f for f in ("Noto Sans CJK SC", "Noto Sans CJK JP", "PingFang SC", "Microsoft YaHei", "SimHei") if f in available]
    settings = {"font.family": fonts + ["DejaVu Sans"], "axes.unicode_minus": False,
                "svg.hashsalt": "reliability-trends-v2"}
    files: list[Path] = []
    charts = child(output, report.config["output"]["charts_directory"])
    charts.mkdir(parents=True, exist_ok=True)
    labels = {g["id"]: g["label"] for g in report.groups}
    ids = list(labels)
    markers = ("o", "s", "^", "D", "v", "P", "X", "<", ">", "h", "*")
    lookup = {(r["year"], r["group"]): r for r in report.annual}
    cutoff = report.cutoff.strftime("%Y-%m-%d %H:%M:%S UTC")
    experimental = "【合成示例数据】" if report.config.get("synthetic", False) else ""

    def figure(title: str, mobile: bool):
        # Reserve additional vertical space for an arbitrary number of legend rows.
        columns = min(2 if mobile else 4, len(ids))
        legend_height = 0.28 * math.ceil(len(ids) / columns)
        fig, ax = plt.subplots(figsize=(5.6 if mobile else 11.6, 5.3 + legend_height))
        fig.subplots_adjust(left=0.18 if mobile else 0.11, right=0.96,
                            bottom=0.25 if mobile else 0.21, top=1 - (1.1 + legend_height) / fig.get_figheight())
        fig.suptitle(f"{experimental}{report.company}\n{title}", x=0.035, ha="left", y=0.98,
                     fontsize=15 if mobile else 18, fontweight="bold")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.18)
        ax.set_axisbelow(True)
        return fig, ax, columns

    def save(fig, path: Path, mobile: bool, *, svg: bool = True):
        path.parent.mkdir(parents=True, exist_ok=True)
        if svg:
            svg_path = path.with_name(path.name + ("_mobile" if mobile else "")).with_suffix(".svg")
            fig.savefig(svg_path, bbox_inches="tight", metadata={"Date": None})
            files.append(svg_path)
        if not mobile:
            png_path = path.with_suffix(".png")
            fig.savefig(png_path, dpi=160, bbox_inches="tight")
            files.append(png_path)
        plt.close(fig)

    def note(fig, text: str, mobile: bool):
        fig.text(0.035, 0.015, f"数据截止：{cutoff}\n{text}\n公开事故记录估计；不是请求成功率或官方 SLA。",
                 fontsize=9 if mobile else 10, va="bottom")

    with plt.rc_context(settings):
        for filename, title, ylabel, key in METRICS:
            for mobile in (False, True):
                fig, ax, columns = figure(title, mobile)
                observed: list[float] = []
                for index, group in enumerate(ids):
                    rows = [lookup.get((year, group), {}) for year in report.years]
                    values = [(row[key] * (100 if key in AVAILABILITY else 1)) if row.get(key) is not None else math.nan for row in rows]
                    observed.extend(v for v in values if math.isfinite(v))
                    line, = ax.plot([], [], marker=markers[index % len(markers)], linewidth=1.8, label=labels[group])
                    # Do not bridge an unobserved year. Mark every incomplete year, not just the last one.
                    for i in range(1, len(values)):
                        if not all(math.isfinite(v) for v in values[i-1:i+1]):
                            continue
                        segment = copy(line)
                        segment.set_data(report.years[i-1:i+1], values[i-1:i+1])
                        segment.set_marker("")
                        segment.set_linestyle("--" if rows[i-1].get("partial_year") or rows[i].get("partial_year") else "-")
                        segment.set_label("_nolegend_")
                        ax.add_line(segment)
                    for partial in (False, True):
                        indices = [i for i, row in enumerate(rows) if math.isfinite(values[i]) and bool(row.get("partial_year")) == partial]
                        points = copy(line)
                        points.set_data([report.years[i] for i in indices], [values[i] for i in indices])
                        points.set_linestyle("None")
                        points.set_fillstyle("none" if partial else "full")
                        points.set_markeredgewidth(1.6)
                        points.set_label("_nolegend_" )
                        ax.add_line(points)
                ax.set_xlim(report.years[0] - 0.35, report.years[-1] + 0.35)
                step = max(1, math.ceil(len(report.years) / (7 if mobile else 12)))
                ticks = sorted(set(report.years[::step] + [report.years[-1]]))
                ax.set_xticks(ticks, [str(y) for y in ticks])
                ax.set_ylabel(ylabel, fontsize=11)
                ax.tick_params(labelsize=11)
                ax.legend(loc="lower left", bbox_to_anchor=(-0.06, 1.015), ncol=columns, frameon=False, fontsize=10)
                if key in AVAILABILITY:
                    low = min(observed, default=100)
                    span = max(100 - low, 0.01)
                    ax.set_ylim(max(0, low - span * 0.12), 100 + span * 0.07)
                    digits = 4 if span < 0.2 else 2
                    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _, d=digits: f"{value:.{d}f}"))
                else:
                    ax.set_ylim(0, max(observed, default=0) * 1.15 or 1)
                    ax.yaxis.set_major_locator(MaxNLocator(6, integer=key == "incident_count"))
                text = "空心点/虚线＝非完整年；缺失年份留空，不补零。"
                text += "\n纵轴按数据缩放。" if key in AVAILABILITY else "\n累计值的跨年对比须考虑观察期长度。"
                note(fig, text, mobile)
                save(fig, charts / filename, mobile)

        active_matches = [r for r in report.matched if r.get("incident_count") is not None]
        match_years = sorted({r["year"] for r in active_matches})
        if len(match_years) >= 2:
            match_groups = [g for g in ids if any(r["group"] == g for r in active_matches)]
            matched_lookup = {(r["year"], r["group"]): r for r in active_matches}
            for mobile in (False, True):
                fig, ax, _ = figure("相同日期窗口：事故数量对比", mobile)
                width = 0.8 / len(match_years)
                for index, year in enumerate(match_years):
                    present = [(i, matched_lookup.get((year, group))) for i, group in enumerate(match_groups)]
                    present = [(i, row) for i, row in present if row is not None]
                    bars = ax.bar([i - 0.4 + width * (index + 0.5) for i, _ in present],
                                  [row["incident_count"] for _, row in present], width=width, label=str(year))
                    ax.bar_label(bars, padding=3, fontsize=9)
                tick_labels = []
                for group in match_groups:
                    sample = next(r for r in active_matches if r["group"] == group)
                    tick_labels.append(f'{labels[group]}\n{sample["window_start"][5:10]}—{sample["window_end"][5:10]}')
                ax.set_xticks(range(len(match_groups)), tick_labels, rotation=20 if len(match_groups) > 4 else 0)
                ax.set_ylabel("同期事故公告数（起）")
                ax.set_ylim(0, max(r["incident_count"] for r in active_matches) * 1.18 or 1)
                ax.legend(ncol=min(4, len(match_years)), frameon=False)
                note(fig, "每个服务组内的两端日期与计数口径已核验。\n产品数量可能重叠，不能直接相加。", mobile)
                save(fig, charts / "09_matched_window_counts", mobile)

        overall = report.config["overall_group"]
        fig, ax, _ = figure("年度事故记录概览", False)
        entries = [lookup[y, overall] for y in report.years if (y, overall) in lookup and lookup[y, overall].get("incident_count") is not None]
        bars = ax.bar([str(r["year"]) + ("*" if r["partial_year"] else "") for r in entries], [r["incident_count"] for r in entries])
        ax.bar_label(bars, padding=4)
        ax.set_ylim(0, max((r["incident_count"] for r in entries), default=0) * 1.2 or 1)
        ax.set_ylabel("事故记录数（起）")
        note(fig, "* 表示非完整年度。\n数量变化并不直接等于请求失败率变化。", False)
        save(fig, child(output, report.config["output"]["overview_counts_file"]).with_suffix(""), False, svg=False)

        latest = max(r["year"] for r in report.annual if r.get("incident_count") is not None)
        fig, ax, _ = figure(f"{latest} 年：三种可用性口径", False)
        for group in report.config["overview_groups"]:
            row = lookup.get((latest, group), {})
            if row.get("incident_count") is None:
                continue
            values = [row[k] * 100 for k in AVAILABILITY]
            ax.plot(range(3), values, marker="o", linewidth=2, label=labels[group])
        ax.set_xticks(range(3), ["仅 Full", "Full＋Partial", "全部等级"])
        ax.set_ylabel("可用性估计（%）")
        if ax.lines:
            ax.legend(frameon=False, ncol=min(4, len(ax.lines)))
        else:
            ax.text(0.5, 0.5, "所选服务在最新年度没有观测数据", ha="center", transform=ax.transAxes)
        note(fig, "各组取自身受影响时间并集；不按用户比例加权。\n具体观察窗口见年度 CSV。", False)
        save(fig, child(output, report.config["output"]["overview_modes_file"]).with_suffix(""), False, svg=False)
    return files
