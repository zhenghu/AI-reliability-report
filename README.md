# AI 可靠性研究报告

归档 AI 服务可靠性研究报告及配套阅读材料；使用**公司无关的配置化构建管线**生成冻结研究结果的图表、HTML 和阅读资料包。

## 通用脚本

公司、服务分组、版本和输入输出路径放在 `configs/`，不再写进 Python 脚本。年份和图表轴范围根据数据确定。新增公司无需复制或修改核心代码。

```sh
python -m pip install -r requirements.txt
python scripts/publish_report.py --config configs/openai-2026-09-27-v1.1.json --validate-only
python scripts/publish_report.py --config configs/openai-2026-09-27-v1.1.json
# 可运行的第二家公司示例：所有数字都是合成测试数据
python scripts/publish_report.py --config configs/example-provider.json
python -m unittest discover -s tests -v
```

[接入其它公司、数据契约、参数与迁移说明](docs/REPORT_PIPELINE.md) · [配置目录](configs/) · [通用构建器](scripts/publish_report.py) · [通用绘图器](scripts/render_trends.py)

生成文件默认在 `build/公司/日期/版本/`，不会覆盖原有归档。原 `publish_openai_report.py` 和 `render_openai_trends.py` 已替换，旧命令请迁移到 `--config` 入口。

**报告构建器仍是展示与打包层。** 上游新增 [Incident Research Skill](.agents/skills/incident-research/SKILL.md)：从公开状态网站采集、校验与分析事故，输出单一 CSV；可通过显式观察窗口聚合成构建器所需的 `trend_data.json`。语义分级由执行 Skill 的智能体结合证据完成，不把采集脚本的默认映射冒充最终分析。


## Incident Research Skill

当前纯文档安装包：[incident-research v1.0.3](packages/incident-research/v1.0.3/README.md)，新增最终报告开篇的整体及各应用年度可用性同表、同图总结规则；保留分析优先、官方颜色兜底。该分发包与下述仓库研发源码独立维护。

入口：公开状态网站 URL，例如 `https://status.openai.com`。输出：一行一个事故的 `incident-csv-v1`，保留维护、原文、官方与分析等级、影响阶段、证据、原始 JSON、哈希和质量标记。

Skill 位于 `.agents/skills/incident-research/`，可使用 `$incident-research` 显式调用；也提供只依赖 Python 标准库的命令行。

```sh
python scripts/collect_incidents.py collect https://status.openai.com \
  --company-id openai --start 2021-02-01T00:00:00Z --output work/openai-run
# 智能体依据保存的公告与复盘生成 analysis.json 后：
python scripts/collect_incidents.py export \
  --snapshot work/openai-run/snapshot.json --analysis work/openai-run/analysis.json \
  --output work/openai-run/incidents.csv
python scripts/collect_incidents.py validate work/openai-run/incidents.csv
```

支持 incident.io 自定义域名与 Statuspage 公共 JSON 的自动发现；其它页面通过获授权的浏览器采集并导入证据快照。公开接口枚举完成不等于未披露事故或真实影响全量已经证明。

[使用、安装与验证说明](docs/INCIDENT_RESEARCH.md) · [CSV 数据契约](.agents/skills/incident-research/references/CSV_CONTRACT.md)

## OpenAI · 2026-09-27 · v1.1

新增专题（2026-09-29）：[OpenAI 事故根因、故障模式与技术方向](insights/2026-09-29-openai-root-causes/report.md) · [来源与证据边界](insights/2026-09-29-openai-root-causes/sources.md) · [复核数据与复算说明](insights/2026-09-29-openai-root-causes/README.md)。基于冻结数据中的 76 条公开复盘，整理 14 个代表案例与 7 类故障模式；不改变下述可用性统计，也不将复盘样本当作全量根因占比。

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

报告快照截止于 **2026-09-26 22:51:22 UTC**（德国时间2026-09-27 00:51:22）。本次重构没有改变这些归档文件、事故判级或冻结截止时间。新构建器仍校验 OpenAI 原稿和绘图数据的已固定 SHA-256；图形可因通用布局和渲染环境变化而不同，不能声称与归档图像逐字节一致。

### 原稿与 GitHub 阅读副本的区别

Markdown 原稿与资料库版本按 SHA-256 核对。现存 `_github.html` 是阅读副本，不是资料库原始 HTML 的逐字节上传；保留正文、表格与配图，但不含原始 HTML 的1,006起事故交互索引。

**`Reading_Package` 是阅读资料包，不是完整审计 ZIP。** 资料库原始交互 HTML、完整原始事故 CSV、逐事故/阶段明细及完整复算包尚未同步到本仓库，原文件仍在资料库“科技新闻解读/AI可靠性研究/OpenAI”。通用构建器也不会假装补齐这些材料。

> 本报告的可用性基于公开事故记录、重分类和去重时间区间估计，不是官方 uptime、合同 SLA、真实请求成功率或单个用户可用率。方法、服务范围、未知区间与推断限制见报告正文。

## Anthropic / Claude · 2026-09-27 · v1.2

**《Claude 可用性与事故复核报告》——整体与各应用年度趋势版**

- [Markdown 主报告](Anthropic/Anthropic_Claude_Availability_Report_2026-09-27_v1.2.md) · [HTML 主报告（下载后离线打开）](Anthropic/Anthropic_Claude_Availability_Report_2026-09-27_v1.2.html)
- [版本索引与历史归档](Anthropic/README.md) · [事故 CSV](Anthropic/2026-09-27/v1.2/incidents.csv) · [验证结果](Anthropic/2026-09-27/v1.2/verification.json)

快照截止 **2026-09-27 16:10:43 UTC**，包含 916 起事故、4 条维护。开篇用一张表和一张折线图汇总整体及六个应用的年度可用性；采用分析优先、官方颜色兜底，明确标注部分年度与未知证据。最新主报告位于 `Anthropic/` 根目录，旧版位于对应版本目录。

本次同时归档原始公开证据、复核记录、图表及复算程序。Anthropic 使用版本目录内的独立分析和报告脚本，尚未接入上述通用配置构建管线；复算步骤见 [v1.2 说明](Anthropic/2026-09-27/v1.2/README.md)。

## DeepSeek · 2026-09-27 · v1.0

**《DeepSeek 可用性与历史事故分析报告》**

- [HTML 报告（下载后离线打开）](DeepSeek/2026-09-27/v1.0/DeepSeek_Availability_Report_2026-09-27_v1.0.html) · [Markdown 报告](DeepSeek/2026-09-27/v1.0/DeepSeek_Availability_Report_2026-09-27_v1.0.md)
- [事故 CSV](DeepSeek/2026-09-27/v1.0/incidents.csv) · [完整审计资料 ZIP](DeepSeek/2026-09-27/v1.0/DeepSeek_Availability_Audit_2026-09-27_v1.0.zip) · [验证结果](DeepSeek/2026-09-27/v1.0/verification.json)
- [版本索引](DeepSeek/README.md) · [方法与复算说明](DeepSeek/2026-09-27/v1.0/README.md)

冻结截止 **2026-09-27 19:36:20 UTC**，包含 103 起事故、2 条维护与 314 条更新；公开接口按月枚举，并与 17 个重叠 History 页面核对。开篇同表、同图展示整体及四个应用的年度可用性，正文说明历史组件改名、缺失时长及 2025 年两条多日公告的敏感性。采用版本目录内的 Flashduty 适配与复算脚本，尚未接入通用展示管线。

## 自动验证

`Build reliability reports` 工作流运行测试并发现 `configs/*.json` 执行构建；也支持手动指定配置文件名。产物作为 Actions artifact 保存14天，工作流不向 `main` 写回生成文件，不定时抓取，不启用 GitHub Pages。

报告及引用的官方资料保留各自来源和权利声明。
