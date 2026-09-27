from pathlib import Path
from copy import copy
import json
import math
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter, MaxNLocator

import argparse
script_root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description="Render annual reliability trends from frozen chart data.")
parser.add_argument("--data", type=Path, default=script_root / "trend_data.json")
parser.add_argument("--assets", type=Path, default=script_root / "OpenAI_Reliability_Trends_2026-09-27")
args = parser.parse_args()
chart_dir = args.assets
chart_dir.mkdir(parents=True, exist_ok=True)
trend_data = json.loads(args.data.read_text(encoding="utf-8"))

# 中文字体只用于渲染；图表使用 Matplotlib 默认配色。
font_path = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
if font_path.exists():
    font_manager.fontManager.addfont(str(font_path))
font_names = {f.name for f in font_manager.fontManager.ttflist}
preferred = [f for f in ["Noto Sans CJK SC", "Noto Sans CJK JP", "PingFang SC", "Microsoft YaHei", "SimHei"] if f in font_names]
plt.rcParams["font.family"] = preferred + ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

groups = ["Overall", "APIs", "ChatGPT", "Codex"]
names = {"Overall": "整体", "APIs": "API", "ChatGPT": "ChatGPT", "Codex": "Codex"}
markers = {"Overall": "s", "APIs": "o", "ChatGPT": "^", "Codex": "D"}
annual_lookup = {(r["year"], r["group"]): r for r in trend_data["annual"]}
years = list(range(2021, 2027))

specifications = [
    ("01_annual_incidents", "各服务年度事故数量", "事故记录数（起）", "incident_count", 1, (0, 385)),
    ("02_incidents_per_30_days", "每 30 天事故频次", "事故记录数 / 30 天", "incidents_per_30_days", 1, (0, 33)),
    ("03_full_hours", "年度影响时长：仅全部中断", "已知影响时间并集（小时）", "full_hours", 1, (0, 57)),
    ("04_full_partial_hours", "年度影响时长：全部＋部分中断", "已知影响时间并集（小时）", "full_partial_hours", 1, (0, 550)),
    ("05_all_hours", "年度影响时长：全部三个等级", "已知影响时间并集（小时）", "all_hours", 1, (0, 2450)),
    ("06_availability_full", "年度可用性：仅扣除全部中断", "可用性估计（%）", "availability_full", 100, (99.35, 100.065)),
    ("07_availability_full_partial", "年度可用性：扣除全部＋部分中断", "可用性估计（%）", "availability_full_partial", 100, (94.0, 100.55)),
    ("08_availability_all", "年度可用性：扣除全部三个等级", "可用性估计（%）", "availability_all", 100, (70.0, 102.2)),
]

def format_value(value, key):
    if key.startswith("availability"):
        return f"{value:.4f}%"
    if key == "incident_count":
        return str(int(value))
    return f"{value:,.2f}"

def save_chart(fig, name, mobile):
    suffix = "_mobile" if mobile else ""
    fig.savefig(chart_dir / f"{name}{suffix}.svg", bbox_inches="tight")
    if not mobile:
        fig.savefig(chart_dir / f"{name}.png", dpi=170, bbox_inches="tight")
    plt.close(fig)

for name, title, ylabel, key, multiplier, ylim in specifications:
    for mobile in (False, True):
        fig, ax = plt.subplots(figsize=(4.6, 5.4) if mobile else (11.6, 5.65))
        fig.subplots_adjust(left=0.20 if mobile else 0.10, right=0.98 if mobile else 0.77,
                            bottom=0.23 if mobile else 0.20, top=0.71 if mobile else 0.79)
        endpoints = []
        for group in groups:
            values = [
                (annual_lookup[y, group].get(key) * multiplier
                 if annual_lookup[y, group].get(key) is not None else math.nan)
                for y in years
            ]
            # 2026 是年内快照：末段用虚线，不把它画成完整自然年结果。
            line, = ax.plot(years, values[:-1] + [math.nan],
                            marker=markers[group], markersize=6, linewidth=2,
                            label=names[group])
            complete_indices = [
                i for i, y in enumerate(years[:-1])
                if annual_lookup[y, group].get("partial_year") is False
            ]
            line.set_markevery(complete_indices)
            if not math.isnan(values[-2]):
                last_segment = copy(line)
                last_segment.set_data(years[-2:], values[-2:])
                last_segment.set_linestyle("--")
                last_segment.set_marker("")
                last_segment.set_label("_nolegend_")
                ax.add_line(last_segment)
            partial_indices = [
                i for i, y in enumerate(years)
                if annual_lookup[y, group].get("partial_year") is True
            ]
            partial_markers = copy(line)
            partial_markers.set_data([years[i] for i in partial_indices],
                                     [values[i] for i in partial_indices])
            partial_markers.set_markevery(None)
            partial_markers.set_linestyle("None")
            partial_markers.set_fillstyle("none")
            partial_markers.set_markeredgewidth(1.8)
            partial_markers.set_label("_nolegend_")
            ax.add_line(partial_markers)
            endpoints.append((group, values[-1]))

        ax.set_xlim(2020.8, 2026.2)
        ax.set_ylim(*ylim)
        ax.set_xticks(years, [str(y) + ("*" if y in (2021, 2026) else "") for y in years])
        ax.tick_params(labelsize=12 if mobile else 11)
        ax.set_ylabel(ylabel, fontsize=12 if mobile else 11)
        ax.grid(axis="y", alpha=0.20)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(loc="lower left", bbox_to_anchor=(-0.04 if mobile else 0, 1.04),
                  ncol=2 if mobile else 4, frameon=False, fontsize=12 if mobile else 11)
        fig.suptitle(title.replace("：", "：\n") if mobile else title, x=0.03 if mobile else 0.065, ha="left",
                     fontsize=17 if mobile else 18, fontweight="bold", y=0.98)
        if key.startswith("availability"):
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.2f}"))
            if key == "availability_full":
                ax.set_yticks([99.4, 99.5, 99.6, 99.7, 99.8, 99.9, 100.0])
            elif key == "availability_full_partial":
                ax.set_yticks([94, 95, 96, 97, 98, 99, 100])
            else:
                ax.set_yticks([70, 75, 80, 85, 90, 95, 100])
        else:
            ax.yaxis.set_major_locator(MaxNLocator(6, integer=key == "incident_count"))
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))

        # 桌面图直接标注最新值；手机图保留更大的绘图区，精确数值在报告表格中。
        if not mobile:
            ordered = sorted(endpoints, key=lambda item: item[1], reverse=True)
            ceiling = 0.94
            for group, value in ordered:
                fraction = (value - ylim[0]) / (ylim[1] - ylim[0])
                target = min(ceiling, max(0.05, fraction))
                ceiling = target - 0.105
                ax.annotate(f"{names[group]}  {format_value(value, key)}",
                            xy=(2026, value), xycoords="data",
                            xytext=(1.025, target), textcoords="axes fraction",
                            fontsize=10.5, va="center", annotation_clip=False,
                            arrowprops={"arrowstyle": "-", "linewidth": 0.7, "alpha": 0.6})

        footer = (
            "空心点＝非完整年；末段虚线＝2026 年内快照。\n"
            "2021 从 2 月起；产品首年为短窗口；未纳入年份留空。"
            if mobile else
            "空心点表示非完整年；末段虚线为 2026 年内快照。2021 从 2 月起；产品首年为短窗口；未纳入年份留空。"
        )
        if key.startswith("availability"):
            footer += "\n纵轴局部放大；公开事故记录估计，非请求成功率或官方 SLA。"
        elif key == "incidents_per_30_days":
            footer += "\n观察期长度标准化，不是请求失败率，也不是全年预测。"
        else:
            footer += "\n次数及累计时长不宜直接用于完整年度与短年度的同比。"
        fig.text(0.03 if mobile else 0.065, 0.018, footer, fontsize=10 if mobile else 9.5, va="bottom")
        save_chart(fig, name, mobile)

# 同期数量：Codex 在两个年份都从 5 月 16 日起比较，避免首年短窗口偏差。
for mobile in (False, True):
    fig, ax = plt.subplots(figsize=(4.6, 5.4) if mobile else (11.6, 5.65))
    fig.subplots_adjust(left=0.11 if mobile else 0.08, right=0.98,
                        bottom=0.26 if mobile else 0.22, top=0.72 if mobile else 0.79)
    positions = list(range(4))
    for year, offset in [(2025, -0.19), (2026, 0.19)]:
        counts = [
            next(r["incident_count"] for r in trend_data["matched_windows"]
                 if r["group"] == group and r["year"] == year)
            for group in groups
        ]
        bars = ax.bar([x + offset for x in positions], counts, width=0.36, label=str(year))
        ax.bar_label(bars, padding=4, fontsize=11)
    ax.set_xticks(positions, [names[g] + ("\n05/16 起" if g == "Codex" else "\n01/01 起") for g in groups])
    ax.set_ylim(0, 300)
    ax.set_ylabel("同期事故公告数（起）", fontsize=11)
    ax.grid(axis="y", alpha=0.20)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.025), frameon=False, ncol=2, fontsize=11)
    fig.suptitle("2025 与 2026：\n相同日期窗口对比" if mobile else "2025 与 2026：相同日期窗口对比",
                 x=0.03 if mobile else 0.065, ha="left", y=0.98,
                 fontsize=16 if mobile else 18, fontweight="bold")
    fig.text(0.03 if mobile else 0.065, 0.03,
             ("两年均截至 9 月 26 日 22:51:22 UTC；\nCodex 两年均从 5 月 16 日起。\n按公告时间计数；产品数量不能直接相加。" if mobile else "两年均截至 9 月 26 日 22:51:22 UTC；Codex 两年均从 5 月 16 日起。\n按公告时间计数；同一事故可归属多个服务，产品数量不能直接相加。"),
             fontsize=10 if mobile else 10)
    save_chart(fig, "09_matched_window_counts", mobile)

print("已生成 9 张年度与同期趋势图，并为每张图制作了手机排版。")
