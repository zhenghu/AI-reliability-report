# AI 可靠性研究报告

本仓库用于归档 AI 服务可靠性研究报告及配套阅读材料。

## OpenAI · 2026-09-27 · v1.1

**《OpenAI 服务可靠性与历史事故分析报告》——年度趋势增强版**

归档目录：[`OpenAI/2026-09-27/v1.1/`](OpenAI/2026-09-27/v1.1/)

| 材料 | 入口 |
| --- | --- |
| 完整 Markdown 原稿 | [在线阅读](OpenAI/2026-09-27/v1.1/OpenAI_Reliability_Report_2026-09-27_v1.1.md) |
| HTML 阅读副本 | [下载后离线打开](OpenAI/2026-09-27/v1.1/OpenAI_Reliability_Report_2026-09-27_v1.1_github.html) |
| 阅读资料包 | [报告、配图及图表数据 ZIP](OpenAI/2026-09-27/v1.1/OpenAI_Reliability_Reading_Package_2026-09-27_v1.1.zip) |
| 9 张年度与同期趋势图 | [SVG / PNG 图表目录](OpenAI/2026-09-27/v1.1/OpenAI_Reliability_Trends_2026-09-27/) |
| 年度图表数据 | [CSV](OpenAI/2026-09-27/v1.1/annual_trend_data.csv) |
| 同期图表数据 | [CSV](OpenAI/2026-09-27/v1.1/matched_window_trend_data.csv) |
| 文件核验 | [出版清单与 SHA-256](OpenAI/2026-09-27/v1.1/publication_manifest.json) |

报告快照截止于 **2026-09-26 22:51:22 UTC**（德国时间 2026-09-27 00:51:22）；归档操作不自动延长数据覆盖日期。

### 原稿与 GitHub 阅读副本的区别

Markdown 原稿与资料库版本按 SHA-256 核对。9 张年度趋势图使用原 v1.1 绘图脚本及冻结数据重新渲染；数据、事故判级与截止时间不变，字体和图像元数据可能因运行环境不同而变化。

**本仓库的 `_github.html` 是从原稿生成的阅读副本，不是资料库原始 HTML 的逐字节上传。** 它保留完整正文、表格与配图，但不含原始 HTML 的 1,006 起事故交互索引。

**`Reading_Package` 是阅读资料包，不是原始完整审计 ZIP。** 资料库原始交互 HTML、完整原始事故 CSV、逐事故/阶段明细及完整复算包尚未同步至本仓库；原文件仍保存在资料库的“科技新闻解读/AI可靠性研究/OpenAI”目录中。

> 本报告的可用性为基于公开事故记录、重分类和去重时间区间的估计，不是 OpenAI 官方 uptime、合同 SLA、真实请求成功率或单个用户的可用率。方法、服务范围、未知区间与推断限制见报告正文。

### 图表重现

安装 Matplotlib 3.10.8 和可用的中文字体后，在仓库根目录执行：

```sh
python scripts/render_openai_trends.py \
  --data OpenAI/2026-09-27/v1.1/trend_data.json \
  --assets OpenAI/2026-09-27/v1.1/OpenAI_Reliability_Trends_2026-09-27
```

该步骤仅重绘冻结图表，不采集新事故，也不重新计算或改判事故等级。仓库未启用定时更新或 GitHub Pages。

报告及其引用的官方资料保留各自的来源和权利声明。
