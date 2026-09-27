# Incident Research：从状态网站到可靠性研究输入

版本：1.0.0。新增上游 Skill，不改变已发表的 OpenAI v1.1 报告及其冻结数据。

## 入口和交付

```text
公开状态网站 URL
  → 平台识别/历史发现
  → 逐窗口或逐页采集，原始响应落盘、可断点续传
  → 覆盖检查、原文/详情/复盘核验
  → 智能体分析等级、服务、时间与根因；保存可追溯校正
  → 一个 incidents.csv + 辅助 validation.json
  → [可选] 显式服务观察窗口 + 时间并集 → trend_data.json
  → 现有 publish_report.py + 研究正文 → 图文报告
```

**Skill 不只是提示词**：包含 SKILL.md、四个标准库 Python 模块、适配/方法/CSV契约参考、UI元数据和合成示例。
机械脚本不能完成任意事故描述的事实判断；该判断由加载 Skill 的智能体执行并形成有证据的 analysis.json。未分析记录明确标 needs_review，未知记录不丢弃。

## 使用

在克隆后的仓库中，显式输入：

```text
$incident-research 从 https://status.openai.com 搜集2021年2月至今的公开事故历史，
核验覆盖、分析实际影响与等级，导出一个CSV作为可靠性报告输入。
```

其它公司改入口网站即可，不复用 OpenAI 的组件ID、日期或等级。没有指定日期时，发现最早公开历史并冻结当前 UTC 截止。

Skill 目录：`.agents/skills/incident-research/`。仓库本地的支持 Agent Skills 的客户端可发现；这不是已安装到用户所有 ChatGPT 会话中的插件。独立使用可复制整个目录到客户端支持的技能目录。核心 SKILL.md 格式参考官方 Agent Skills 文档，见 references/ADAPTERS.md 的来源。

命令行（仓库根目录）：

```sh
python scripts/collect_incidents.py --help
python scripts/collect_incidents.py collect https://status.openai.com \
  --company-id openai --company-name OpenAI \
  --start 2021-02-01T00:00:00Z --output work/openai-run

# analysis.json 由智能体依据保存的原始材料生成，格式见 CSV_CONTRACT.md
python scripts/collect_incidents.py export \
  --snapshot work/openai-run/snapshot.json --analysis work/openai-run/analysis.json \
  --output work/openai-run/incidents.csv
python scripts/collect_incidents.py validate work/openai-run/incidents.csv

# 对接既有图文报告构建器
python scripts/collect_incidents.py aggregate \
  --csv work/openai-run/incidents.csv --windows work/openai-run/service_windows.json \
  --output work/openai-run/trend_data.json
```

只运行 export、没有 analysis 参数时是官方数据初步底表，不宣称语义分析已完成。`aggregate` 默认拒绝未核对/未知证据；研究者接受公开记录估计时才显式加 `--allow-estimates`，不完整采集还需 `--allow-incomplete`。正文必须披露这些限制。

退出码：0=当前阶段成功，1=输入/验证/发现错误，2=采集部分成功但覆盖不完整。成功导出CSV只代表结构校验通过；枚举和语义质量单独披露。

## 能力边界

| 已实现 | 边界 |
|---|---|
| incident.io 自定义域名 JSON 发现与时间窗口遍历 | 依赖经核对的公开前端路由；共享域名子路径或接口变更需浏览器/适配更新 |
| Statuspage JSON 分页与维护分离 | 遇重复页/不支持分页/字段变更/错误不能声称完整；需界面交叉检查 |
| generic/native 快照导入 | 非原生页面由智能体保存证据，不伪造官方组件阶段 |
| 字段、哈希、引用、时区、区间、重复ID校验 | 引文存在只证明可追溯；不能替代语义正确性判断 |
| 三等级与 unknown 分离 | 单组件Full不是全产品/全公司Full |
| 单 CSV 与报告数据桥接 | 不是请求成功率、SLA或实时可用性监控；不自动写研究正文 |
| 断点、限速、有界重试、安全URL和不覆盖输出 | 不是面向不可信租户的完整网络沙箱，部署时还需出站隔离 |

日期选择为首次公开发布时间窗口。为全年影响研究必须检查carry-in事故；公开接口没有记录不等于真实无故障。对 Statuspage critical/major/minor 的映射仅作初步等级，必须保留原值和映射说明。

## 最小离线演示

全部使用合成 ExampleAI 事故，不涉及任何真实厂商：

```sh
python scripts/collect_incidents.py export \
  --snapshot .agents/skills/incident-research/examples/snapshot.json \
  --analysis .agents/skills/incident-research/examples/analysis.json \
  --output work/example/incidents.csv
python scripts/collect_incidents.py aggregate \
  --csv work/example/incidents.csv \
  --windows .agents/skills/incident-research/examples/service_windows.json \
  --output work/example/trend_data.json
python -m unittest discover -s tests -v
```

本次新增测试覆盖本地模拟的两平台响应、重复分页、失败/恢复边界、维护、未结束、结案后复盘、重开、跨年、闰年、未知时长、引文与哈希不符、超长中文/换行、CSV公式注入、与现有报告数据校验器的衔接。
已有 1,007 行 OpenAI 冻结CSV仅用于离线解析和往返验证；没有迁移历史报告的所有专项校正，也没有重新采集至新日期。测试结果不是对所有状态站点兼容性或当前网络可达性的保证。

## 文件索引

- [Skill 入口](../.agents/skills/incident-research/SKILL.md)
- [方法与评估](../.agents/skills/incident-research/references/METHODOLOGY.md)
- [平台适配](../.agents/skills/incident-research/references/ADAPTERS.md)
- [CSV与分析契约](../.agents/skills/incident-research/references/CSV_CONTRACT.md)
- [命令行模块](../.agents/skills/incident-research/scripts/incident_pipeline.py)

公开发表/永久归档需用户授权；采集任务本身不会自动提交数据或向第三方临时服务器上传文件。当前工作流仅离线测试，不开启定时爬取。
