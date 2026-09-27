# 通用 AI 可靠性报告构建管线

## 范围

`publish_report.py` 与 `render_trends.py` 面向任意公司。公司、报告日期、版本、服务名称、输入路径、输出目录和输入校验值来自 JSON 配置；年份范围、观察窗口、图表范围来自数据。**脚本只构建冻结研究结果的阅读版本，不采集新事故、不重新判级、不从原始事故重算可用性。** 不同供应商的采集与口径映射应在上游完成，不能仅凭字段同名就认定可横向比较。

原 `publish_openai_report.py`、`render_openai_trends.py` 和专用发布工作流已由通用入口替代。没有保留内嵌 OpenAI 默认参数的旧入口。原有 `OpenAI/2026-09-27/v1.1/` 报告、图表与冻结 JSON 保持不变；新的构建默认写入 `build/`，不反向覆盖历史归档。

## 快速使用

需要 Python 3.10 或更新版本。当前测试依赖固定在 `requirements.txt`；中文绘图建议安装 Noto Sans CJK，脚本也会尝试系统已有的苹方、微软雅黑或黑体。字体不随资料包分发。

在仓库根目录执行：

```sh
python -m venv .venv
# macOS/Linux
. .venv/bin/activate
# Windows PowerShell 使用 .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# 只验证配置、数据及可选 SHA-256，不写入任何输出
python scripts/publish_report.py --config configs/openai-2026-09-27-v1.1.json --validate-only

# 完整构建：Markdown副本、HTML、图表、CSV、校验清单和阅读ZIP
python scripts/publish_report.py --config configs/openai-2026-09-27-v1.1.json

# 仅生成图表，要求目标目录不存在或为空
python scripts/render_trends.py --config configs/openai-2026-09-27-v1.1.json --output build/openai-charts

# 指定其它输出位置
python scripts/publish_report.py --config configs/example-provider.json --output build/example-test

# 重建同一公司此前生成的目录；不会覆盖不属于构建器的文件
python scripts/publish_report.py --config configs/example-provider.json --output build/example-test --overwrite

python -m unittest discover -s tests -v
```

`--config` 可为绝对路径；配置里的输入和输出目录相对于配置文件所在目录解析，不随工作目录改变。命令行 `--output` 相对于当前工作目录。`--overwrite` 只允许替换同一公司、含本构建器清单且没有额外文件的目录；输出包含任意输入文件、未知目录、符号链接或未受管理文件时拒绝覆盖。完整构建使用临时目录，全部成功后才替换输出，失败时原输出保留。

## 新增一家公司

复制 `configs/example-provider.json` 为新配置，准备该公司的 Markdown 报告与 `trend_data.json`，修改 `company`、`report`、`inputs`、`output`、`groups` 和 `overall_group`，更新输入 SHA-256，然后运行同一个通用命令。无需复制或修改 Python 核心。

`examples/sample-provider/` 是 **ExampleAI 合成测试数据**，不是对真实公司的研究；例子包含缺失的 2023 年和服务首年的短窗口。接入真实公司时必须替换全部示例数据与正文，删除或设定 `synthetic: false`，不能把改名后的示例当成真实研究。

```json
{
  "schema_version": 1,
  "company": {"id": "provider-id", "name": "公司显示名"},
  "report": {"date": "2026-09-27", "version": "v1.0", "title": "公司可靠性研究报告"},
  "inputs": {"markdown": "../YourCompany/2026-09-27/v1.0/report.md", "data": "../YourCompany/2026-09-27/v1.0/trend_data.json"},
  "output": {"directory": "../build/YourCompany/2026-09-27/v1.0", "stem": "YourCompany_Reliability_Report_2026-09-27_v1.0", "charts_directory": "charts"},
  "groups": [{"id": "Total", "label": "整体"}, {"id": "Inference", "label": "推理服务"}],
  "overall_group": "Total"
}
```

这是字段示意，不是自带数据的可运行新公司配置。可直接运行的示例是 `configs/example-provider.json`。

### 配置字段

| 字段 | 含义 |
| --- | --- |
| `schema_version` | 当前为 1，未知版本报错 |
| `company.id` / `company.name` | 稳定机器标识 / 图表显示名 |
| `report.date` / `version` / `title` | 报告元数据，不自动更改统计截止日期 |
| `inputs.markdown` / `data` | 原稿和已计算的冻结统计数据 |
| `output.directory` / `stem` | 输出根目录和文件名前缀 |
| `output.charts_directory` | 默认 `charts`；兼容原稿已有相对图片路径 |
| `output.overview_counts_file` | 可选，默认 `annual_incidents.png` |
| `output.overview_modes_file` | 可选，默认 `availability_modes.png`；可映射历史原稿中的文件名 |
| `groups` | 任意数量的服务组，`id` 对应数据，`label` 用于图例 |
| `overall_group` | 指定汇总组；必须由上游提供并集结果，不自动相加子服务 |
| `overview_groups` | 可选，概览图选用的组；默认排除汇总组 |
| `integrity.markdown_sha256` / `data_sha256` | 可选但正式归档推荐必填；填写后严格校验，绝不修补原文件 |
| `synthetic` | 默认 false；示例数据为 true，HTML和图表显示明显提示 |

生成校验值可使用：

```sh
python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('你的文件路径').read_bytes()).hexdigest())"
```

未固定校验值时仍记录实际输入哈希，但不会声称已对照原始归档验证。所有输入只读。打包时生成的便携配置会固定本次实际输入哈希，方便独立校验与重画。

## 统一统计数据契约 v1

兼容已有 OpenAI `trend_data.json`：没有 `schema_version` 的旧文件按 v1 处理。顶层为：

```json
{
  "schema_version": 1,
  "cutoff_utc": "2026-09-26T22:51:22Z",
  "annual": [],
  "matched_windows": []
}
```

`annual` 至少包含一条有效观察记录；`matched_windows` 可省略。每个数组内 `(year, group)` 不得重复，所有 group 都必须在配置中声明。截止时间及观察窗口必须包含时区，比较和验证统一转成 UTC。

### 有效年度行

必须提供 `year`、`group`、`window_start`、`window_end`、`incident_count`，以及以下累计去重时长和可用性：

| 字段 | 含义 |
| --- | --- |
| `full_hours` | Full 时间并集（小时） |
| `full_partial_hours` | Full ∪ Partial 时间并集（小时） |
| `all_hours` | Full ∪ Partial ∪ Degraded 时间并集（小时） |
| `availability_full` | `1 − full_hours × 3600 / denominator_seconds` |
| `availability_full_partial` | `1 − full_partial_hours × 3600 / denominator_seconds` |
| `availability_all` | `1 − all_hours × 3600 / denominator_seconds` |

**可用性必须是 0—1 比率，不是 0—100 百分数。** 核心验证数值有限且非负、小时并集单调、小时数不超出观察时长、三个比率与分母相符。显示时才乘以100。配置里的 `report.date` 不充当可用性分母。

可选字段：`denominator_seconds`、`observation_days`、`partial_year`、`incidents_per_30_days`、`unknown_time_count`，其余分析字段也会在 CSV 保留。前四项若提供则验证，若省略则从明确窗口导出显示用数据；它们不用于补造事故。不允许 NaN、Infinity、字符串数字、负数或小数事故数量。

年度窗口必须落在 `year` 对应的 UTC 年内，且不超过 `cutoff_utc`。`partial_year` 根据窗口自动判定，不固定将最后一年视为未完成，也不固定年份为 2021—2026。闰年按实际秒数处理。

### 缺失、未上线、未知区间

缺少某个服务年份可以省略该行；图中保持断点。也可显式给出 `incident_count: null, denominator_seconds: 0`，其它时长和比率必须省略或为 null。**零事故是观测结果，null 是没有可用观察结果，不能混用。** 没有精确时间的事故可以包含在事故数量中，同时使用 `unknown_time_count` 披露；不得伪造时间加入小时并集。

### 同期行

与有效年度行相同，另需提供 `count_basis`（例如 `published_at_utc`）。同一服务各年的窗口须具有相同的起止月日、时分秒以及相同计数口径；否则拒绝绘制“同期”比较。闰年天数不同是允许的，因为使用相同日历范围而非硬凑同样天数。不同产品可以采用不同起始月日。缺少的组/年份不补零；有至少两个有效年份时才生成第9张图。

## 构建产物及安全边界

8 张年度图始终生成；第9张为可选同期图，每张都有桌面/手机版 SVG 及桌面 PNG，另有两张概览 PNG。横轴年份和纵轴范围自动适配；不跨缺失年份连线；任何非完整年度使用空心点，相邻线段使用虚线。图例数量不固定。当前图注语言为中文。

HTML 内嵌配图并保留响应式排版。原稿的图片必须使用相对本地路径，支持 SVG、PNG、JPEG、WebP；脚本不会从远程 URL 下载图片。路径越界、符号链接越界或编码后的 `../` 均拒绝。用户提供的原始 HTML 被转义；本地图片作为图像嵌入，不作为页面脚本执行。

阅读 ZIP 包括原稿副本、冻结 JSON、生成图表、两份 CSV、便携配置、构建器源码、依赖版本与校验清单。解压后运行 `python tools/publish_report.py --config report.config.json` 可重新生成阅读版。压缩包只包含本次临时目录中明确生成的文件，不打包相邻的旧文件。该包**不冒充包含原始事故 CSV 的完整审计包**。

## GitHub Actions

`Build reliability reports` 对脚本/配置/数据相关的 push 与 PR 运行测试和构建；也可以手动运行，`config` 填 `all` 或 `configs/` 中的文件名，例如 `openai-2026-09-27-v1.1.json`。新增配置自动被 `all` 发现，不必修改工作流。输入只能匹配已存在的配置文件名，不拼接到 shell 命令。

工作流只有 `contents: read` 权限，不自动向 `main` 提交新图、不改已有归档、不启用定时抓取或 GitHub Pages。生成材料作为 Actions artifact 保存14天，正式长期归档仍需明确提交。这与旧工作流直接把新图写回 v1.1 的方式不同，避免一次通用脚本修改悄悄改变已发表历史快照。

## 模块

```text
scripts/
  publish_report.py            # 完整构建 CLI
  render_trends.py             # 单独绘图 CLI
  reliability/
    model.py                  # 配置、时间、数值、哈希和数据契约校验
    charts.py                 # 通用图表
    publisher.py              # HTML、CSV、便携ZIP、原子输出与文件校验
configs/                      # 每家公司/日期/版本一个配置
examples/sample-provider/     # 明确标记的合成示例
```

上游未来可增加供应商采集适配器、统一事故结构和可用性计算模块；它们输出上述契约即可复用本构建管线。当前不会宣称这些上游能力已经实现。
