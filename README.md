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

**这是展示与打包管线，不是自动研究系统。** 不采集新事故、不重新判级、不从原始事故重算可用性。正式研究应先生成经过校验的公司统计数据和报告正文，再由此管线出版。

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

报告快照截止于 **2026-09-26 22:51:22 UTC**（德国时间2026-09-27 00:51:22）。本次重构没有改变这些归档文件、事故判级或冻结截止时间。新构建器仍校验 OpenAI 原稿和绘图数据的已固定 SHA-256；图形可因通用布局和渲染环境变化而不同，不能声称与归档图像逐字节一致。

### 原稿与 GitHub 阅读副本的区别

Markdown 原稿与资料库版本按 SHA-256 核对。现存 `_github.html` 是阅读副本，不是资料库原始 HTML 的逐字节上传；保留正文、表格与配图，但不含原始 HTML 的1,006起事故交互索引。

**`Reading_Package` 是阅读资料包，不是完整审计 ZIP。** 资料库原始交互 HTML、完整原始事故 CSV、逐事故/阶段明细及完整复算包尚未同步到本仓库，原文件仍在资料库“科技新闻解读/AI可靠性研究/OpenAI”。通用构建器也不会假装补齐这些材料。

> 本报告的可用性基于公开事故记录、重分类和去重时间区间估计，不是官方 uptime、合同 SLA、真实请求成功率或单个用户可用率。方法、服务范围、未知区间与推断限制见报告正文。

## 自动验证

`Build reliability reports` 工作流运行测试并发现 `configs/*.json` 执行构建；也支持手动指定配置文件名。产物作为 Actions artifact 保存14天，工作流不向 `main` 写回生成文件，不定时抓取，不启用 GitHub Pages。

报告及引用的官方资料保留各自来源和权利声明。
