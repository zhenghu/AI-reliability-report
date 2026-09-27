# Claude 可用性与历史事故报告

**Anthropic · 2026-09-27 · v1.0 状态记录参考估计版**

冻结截止：**2026-09-27 16:10:43 UTC**（德国时间 18:10:43）。来源：[Claude 官方状态站](https://status.claude.com)、[History](https://status.claude.com/history)、逐事故公开 JSON。

> 本报告已完成公开历史采集与结构校验，但未完成全部事故的逐阶段语义复核。百分比是“已取得并可定位的状态异常区间之外的时间比例”，不是实际请求成功率、官方 uptime 或合同 SLA。请先看口径和质量表，再使用数字。

## 一、可以确认的结论

- 取得 **920 条唯一记录：916 起事故、4 条维护、2,919 条更新**。按公告时间，2023 年 30 起、2024 年 188 起、2025 年 334 起、2026 年截至本次冻结 364 起事故。枚举范围覆盖官方 History 可得历史，不能证明厂商披露了所有真实故障。
- 当前不能负责任地用一个数字宣称“Claude 的真实可用率”。同一条公告可能只影响登录、某个模型、免费用户或某个工具；按“任一功能出现问题”计算，与按“所有请求失败”计算差别很大。
- 2026 年核心服务并集的 **F 参考率为 99.7528%、F∪P 为 84.9102%、全部等级为 80.6169%**。这些 F/P/D 主要沿用官方历史组件状态，只有重点记录做了正文校正；F 并不等于整家公司完全停机。
- 一条指定模型访问暂停公告的生命周期约 **450.60 小时**。排除此项后，2026 年核心服务并集的 F∪P 参考率为 **91.7989%**、全部等级为 **87.2573%**。差值来自重新取时间并集，不是直接减掉 450.60 小时。
- 缺失时间、未完成分级、不同组件历史起点和披露习惯都会影响结果。**本版适合用于定位风险与选择复核重点，不适合作为供应商 SLA 排名或与 OpenAI 报告直接横向排序。**

## 二、历史范围、覆盖与年度数量

| 年份（公告 UTC） | 事故 | 维护 |
| --- | --- | --- |
| 2023 | 30 | 0 |
| 2024 | 188 | 3 |
| 2025 | 334 | 1 |
| 2026 | 364 | 0 |

实际取得最早公告：**2023-03-14T12:00:00Z**；最新公告：**2026-09-22T00:57:26.126000Z**。2026-09-22 后到冻结时刻之间没有取得新的事故公告，不等于这段时间不存在任何真实故障。

History 以连续 3 个月为一页，共保存 **16 页**，从 2026 年第三季度读到 2022 年第四季度。最后一页为空，且早于页面创建时间 **2023-01-25T06:38:50.038Z**。页面没有提供明确的“全部历史可得起点”声明，因此不把页面创建日或第一起事故当作产品上线日。

事故列表 API 的 `page=2` 与第一页重复；维护列表也重复。因此这两个列表接口不作为全量覆盖依据。History 的 920 个 ID 与最终 920 条对象一一对应；其中两个维护 ID 在事故详情接口返回 404，改用公开维护详情接口后取得。最近列表的 50 个 ID 全部包含在 History 枚举中。

**覆盖状态：enumerated（对实际可访问的 History 边界完成枚举）。**交叉检查是 History HTML 内嵌数据与公开详情 JSON 的 ID 对照；未把两个同源接口称为独立信源，也未宣称已执行浏览器逐页视觉核对。每页原始 HTTP 响应体及 SHA-256 已保存在本地证据目录。

## 三、观察窗口与统计定义

| 服务 | 观察起点 UTC | 选择理由 |
| --- | --- | --- |
| 核心服务并集 | 2023-07-11T00:00:00Z | 官方组件 start_date |
| Claude.ai | 2023-07-11T00:00:00Z | 官方组件 start_date |
| 第一方 API | 2023-07-11T00:00:00Z | 官方组件 start_date |
| Console | 2023-07-11T00:00:00Z | 官方组件 start_date |
| Claude Code | 2025-05-23T00:00:00Z | 官方组件 created_at 后首个完整 UTC 日 |
| Cowork | 2026-04-02T00:00:00Z | 官方组件 created_at 后首个完整 UTC 日 |
| Government | 2026-02-18T00:00:00Z | 官方组件 created_at 后首个完整 UTC 日 |

较新组件的官方 `start_date` 有早于组件创建日期的情况，Claude Code 尤为明显。本版保守采用组件创建后的首个完整 UTC 日，不回填组件出现前的“零故障”历史。Cowork 在 2026 年 4 月之前的相关公告仍保留于 CSV，但不用于 Cowork 本版可用性分母。所有窗口截止均为本轮冻结时间。

核心服务并集纳入 Claude.ai、第一方 API、Console、Claude Code、Cowork 和 Government，且每个组件只在自身观察窗口内参与。Vertex/Bedrock、营销网站、文档站、社交账号单独归 External/Other，不计入核心服务并集。未能归属核心组件的公告仍留在 CSV，不能悄悄当成无影响。

- **F**：参考序列中的 `major_outage`，或已核验范围内的 Full。它可能只是组件/功能失效，不能解释成全公司停机。
- **F∪P**：上述区间与 `partial_outage` 的时间并集。
- **F∪P∪D**：再加入 `degraded_performance`，涵盖延迟、质量或功能退化。
- 事故级 `critical / major / minor` 仅在没有可用历史组件阶段时作为候选映射，分别对应 F/P/D，并标为公告代理。`none` 不是正常状态证据。

计算式：**参考率 = 1 − 相应异常时间并集 ÷ 明确观察窗口秒数**。维护排除；跨年裁切；同一事故、组件间和事故间的重叠均去重。Overall 重新对全部纳入阶段取并集，不加总产品小时数。没有精确区间的数据不进入时长，因而剩余时间不能解释成已确认正常。

¹ 各表事故数按公告时间归年、按对应服务归属计数。一个事故可同时计入多个服务，所以各服务次数不能相加。数量表与时间表采用不同的合理边界：迟报事件按公告日计数，但明确影响窗口按真实日期计时。

## 四、2026 年截至冻结时刻的参考结果

| 服务 | 观察起点 | 事件数¹ | F 参考 | F∪P 参考 | F∪P∪D 参考 |
| --- | --- | --- | --- | --- | --- |
| 核心服务并集 | 2026-01-01 | 340 | 99.7528% | 84.9102% | 80.6169% |
| Claude.ai | 2026-01-01 | 300 | 99.7528% | 86.8780% | 83.2640% |
| 第一方 API | 2026-01-01 | 252 | 99.7948% | 88.9042% | 85.9752% |
| Console | 2026-01-01 | 157 | 99.9414% | 98.8793% | 96.8202% |
| Claude Code | 2026-01-01 | 270 | 99.7935% | 90.3988% | 86.8702% |
| Cowork | 2026-04-02 | 149 | 99.8835% | 85.9407% | 83.9659% |
| Government | 2026-02-18 | 21 | 99.9879% | 99.9259% | 99.7828% |

为便于复算，对应的异常并集时长如下：

| 服务 | F 小时 | F∪P 小时 | F∪P∪D 小时 |
| --- | --- | --- | --- |
| 核心服务并集 | 16.00 | 976.64 | 1,254.51 |
| Claude.ai | 16.00 | 849.28 | 1,083.18 |
| 第一方 API | 13.28 | 718.14 | 907.71 |
| Console | 3.79 | 72.53 | 205.80 |
| Claude Code | 13.36 | 621.41 | 849.78 |
| Cowork | 5.00 | 602.89 | 687.57 |
| Government | 0.64 | 3.94 | 11.56 |

API 的统计范围是第一方 API 公告所涉组件，既可能包含核心推理，也可能包含工具、批处理或其他功能。Claude Code 的登录故障可能影响新登录用户，却不阻断已登录会话。Cowork 和 Government 观察窗口短于 2026 年全段；不能把它们的百分比与长窗口产品当成同等实验条件。

## 五、主动暂停对结果的影响

[We’ve suspended access to Claude Mythos 5 and Claude Fable 5](https://status.claude.com/incidents/s9w82lp9dcn9) 于 2026-06-13 公告暂停指定模型访问，7 月 1 日关闭。官方说明指出暂停针对 Fable 5 与 Mythos 5，其他模型不受影响；因此本研究将其视为产品范围的 Partial，而非所有 Claude 服务 Full。它的公告关闭时间并不能独立证明各平台、各用户在同一秒恢复。

来源：[官方暂停说明](https://www.anthropic.com/news/fable-mythos-access)、[官方重新开放说明](https://www.anthropic.com/news/redeploying-fable-5)。本版只分析其服务范围与统计影响，不对政策合法性或背景作判断。

| 服务 | 含暂停 F∪P | 排除暂停 F∪P | 含暂停全部等级 | 排除暂停全部等级 |
| --- | --- | --- | --- | --- |
| 核心服务并集 | 84.9102% | 91.7989% | 80.6169% | 87.2573% |
| Claude.ai | 86.8780% | 93.7668% | 83.2640% | 89.9142% |
| 第一方 API | 88.9042% | 95.8027% | 85.9752% | 92.6317% |
| Console | 98.8793% | 98.8793% | 96.8202% | 96.8202% |
| Claude Code | 90.3988% | 97.2972% | 86.8702% | 93.5324% |
| Cowork | 85.9407% | 96.3526% | 83.9659% | 94.0273% |
| Government | 99.9259% | 99.9259% | 99.7828% | 99.7828% |

主表保留这条事件，因为用户确实可能失去指定模型的访问；对照表排除它，帮助观察技术运行事件。**“排除暂停”仍不是完整技术故障真值**：其他访问政策、未知时间和功能性事件未因此全部消除。

## 六、年度与同期变化

截至相同的 9 月 27 日 16:10:43 UTC，事故公告数量如下。2026 年数字不与 2025 全年直接比较：

| 同期年份 | 全站事故公告数 | 核心服务事故公告数 | 核心服务全部等级参考率 |
| --- | --- | --- | --- |
| 2024 | 130 | 110 | 96.5773% |
| 2025 | 263 | 254 | 91.2034% |
| 2026 | 364 | 340 | 80.6169% |

公告增加可能同时反映产品范围扩大、组件细分和披露方式变化，不能单凭次数推断底层系统同幅度恶化。2026 年的范围又增加 Cowork 和 Government，Overall 的服务集合也发生变化。

完整年度/部分年度服务表：

| 年份 | 服务 | 观察天数 | 公告数¹ | F 小时 | F∪P 小时 | 全部等级小时 | 全部等级参考率 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | 核心服务并集 | 174.00 | 12 | 0.00 | 11.31 | 18.06 | 99.5675% |
| 2024 | 核心服务并集 | 366.00 | 160 | 4.26 | 133.15 | 373.66 | 95.7461% |
| 2025 | 核心服务并集 | 365.00 | 322 | 22.33 | 211.26 | 671.92 | 92.3296% |
| 2026 | 核心服务并集 | 269.67 | 340 | 16.00 | 976.64 | 1,254.51 | 80.6169% |
| 2023 | Claude.ai | 174.00 | 8 | 0.00 | 9.21 | 13.65 | 99.6730% |
| 2024 | Claude.ai | 366.00 | 127 | 3.66 | 91.22 | 245.56 | 97.2045% |
| 2025 | Claude.ai | 365.00 | 288 | 20.83 | 199.44 | 638.79 | 92.7078% |
| 2026 | Claude.ai | 269.67 | 300 | 16.00 | 849.28 | 1,083.18 | 83.2640% |
| 2023 | 第一方 API | 174.00 | 9 | 0.00 | 11.31 | 14.16 | 99.6608% |
| 2024 | 第一方 API | 366.00 | 126 | 0.88 | 122.14 | 316.67 | 96.3949% |
| 2025 | 第一方 API | 365.00 | 234 | 8.45 | 158.62 | 352.93 | 95.9711% |
| 2026 | 第一方 API | 269.67 | 252 | 13.28 | 718.14 | 907.71 | 85.9752% |
| 2023 | Console | 174.00 | 7 | 0.00 | 9.21 | 11.64 | 99.7214% |
| 2024 | Console | 366.00 | 109 | 1.87 | 58.06 | 193.27 | 97.7997% |
| 2025 | Console | 365.00 | 194 | 12.10 | 83.19 | 247.21 | 97.1779% |
| 2026 | Console | 269.67 | 157 | 3.79 | 72.53 | 205.80 | 96.8202% |
| 2025 | Claude Code | 223.00 | 101 | 4.45 | 34.81 | 156.87 | 97.0689% |
| 2026 | Claude Code | 269.67 | 270 | 13.36 | 621.41 | 849.78 | 86.8702% |
| 2026 | Cowork | 178.67 | 149 | 5.00 | 602.89 | 687.57 | 83.9659% |
| 2026 | Government | 221.67 | 21 | 0.64 | 3.94 | 11.56 | 99.7828% |

2023 年仅覆盖核心三组件 7 月 11 日后的窗口；2025 年 Claude Code、2026 年 Cowork/Government 均为部分年度。本版不连接不存在的早期产品数据，也不把缺失年份补成 100%。

## 七、重点事件：哪些细节改变结论

### 1. 部分请求失败，不等于红色标签所暗示的全停

[Elevated error rate on API across all Claude models](https://status.claude.com/incidents/d8v3zr02my00) 的官方严重度是 critical，但正文说明受影响请求比例较小，明确影响窗口为 **2026-02-03 17:52–17:56 UTC**。本次将其按 API 范围的 Partial 处理。仅根据 critical→Full 映射会夸大故障范围。

### 2. 一次长公告中只有部分时段是入口完全不可访问

[Elevated errors on Claude.ai](https://status.claude.com/incidents/7542z654hwl8) 横跨约一天。正文明确 Claude.ai 与 Console 在 **2025-07-09 21:36–21:52 UTC** 无法访问；其他时段涉及少量错误和 Artifacts 发布不可用。CSV 为这一事件保留分段，不能把全天都算作 Full。API 明确未受影响。

### 3. 依赖故障有不同影响路径

[Elevated errors on the API, Console and Claude.ai](https://status.claude.com/incidents/kn7mvrgb0c8m) 将异常归因于 GCP 依赖。图像/文件上传不可用时，部分文本请求仍可成功。它支持“依赖故障会跨入口传播”的结论，但不支持“全部文本推理持续失败”的结论。恢复过程按记录分层，不能把监控状态自动当作完全恢复。

### 4. 输出质量也是可靠性，但没有秒级时间就不能编造

[Claude Sonnet 4 degraded performance quality](https://status.claude.com/incidents/4q9qw2g0nlcb) 明确给出 **2025-07-08 08:45 至 7 月 10 日 02:00 UTC** 的输出质量退化，与推理栈发布有关，计入 Degraded。

[Model output quality](https://status.claude.com/incidents/72f99lh1cj2c) 则引用了多个早于公告的质量问题。官方[技术复盘](https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues)讨论路由、输出损坏和采样计算问题，说明错误率/延迟监测不足以覆盖回答质量。其阶段多以日期表述，本版没有擅自补成 UTC 午夜；也没有把后发复盘的发表时间延长为故障时间。

### 5. 客户端功能失效与核心模型推理分开

[Degraded functionality for Claude Cowork on Windows](https://status.claude.com/incidents/r1pqn1kb4hvk) 描述 Windows 更新导致 Cowork 本地命令失效，而多数用户仍能聊天和读写文件，因此按 Cowork 产品范围 Partial 处理。更新发布日期只精确到日，公告生命周期约 99 小时只是代理，不证明真实影响从公告时才开始。

[Claude Desktop app unresponsive](https://status.claude.com/incidents/pqpgkf52p3tg) 的官方更新说明夏令时跳过的小时引发定时任务定位循环，限定于相应时区和配置的用户。这类事件说明客户端、认证和任务调度需要独立的可靠性指标。

## 八、质量缺口与可信度

| 检查项 | 本轮结果 |
| --- | --- |
| 历史枚举 | 920 个 History ID 全部取得；16 个连续季度窗口；最后窗口早于页面创建 |
| 原始记录 | 916 事故 + 4 维护；2,919 更新；同名不同 ID 未合并 |
| 官方严重度缺失/none | 118 起事故；不视为零影响 |
| 重点语义复核 | 87 条；其余 833 条标 needs_review |
| 语义严重度仍 unknown | 855 起事故，包括未完成分级及证据不足 |
| 完整核验的精确时间线 | 16 条；不能把其余都有起止字段等同于已核验 |
| 语义分析区间未建立 | 869 起事故；含未完成语义复核，并不等于原始公告没有时间 |
| 参考序列无法定位/不采用区间 | 121 起事故；其他参考区间仍包含官方状态边界与公告代理 |
| 当前未结案记录 | 0 |
| 结构校验 | UTF-8 BOM、48 列、唯一 ID、JSON、原始对象 SHA-256、时区、正长度、时长并集、转义复读均通过 |
| 非结构验收 | 未完成所有事件的逐阶段语义验收；未核验未公开故障、实际请求成功率及用户/地区权重 |

CSV 的 **impact_intervals_json** 仅存已做重点判断的分析区间；**evidence_json.reference_intervals** 存本报告参考序列。两者不能混用。`trend_data.json` 明确标记为 `official_state_reference_with_focused_corrections`，不会将待复核的官方映射包装为已分析结果。

需优先复核的时间冲突包括：2024-04-18 公告正文却写 Feb 18；2025-09-12 同时给出的 PT 与 UTC 时长不同；2026-04-15 API 恢复描述的 PT/UTC 换算与发布时间互相不一致。相应 CSV 质量标志已保留，未无声修正成貌似精确的数字。

最早两起事件只披露 1 小时和 30 分钟，不能据此定位时间段。官方组件阶段也是“发布状态变化”的时间，未必等于真实影响时间；代理既可能漏掉公告前影响，也可能包含恢复后的监控。故本报告百分比没有可声称的统计置信区间。

额外技术复盘已通过网页读取工具查看；直接 HTTP 下载该页面返回 403，已停止该下载路径。本地只保留明确标注的摘录/研究笔记，不声称取得其完整原始 HTTP 文件。没有使用登录凭证或绕过访问限制。

## 九、如何使用本报告

可用于：建立公开事故基线；定位功能性和依赖风险；选择需要进一步复核的长事故；设计按调用路径区分的监测目标。

要用于生产选型或承诺 SLO，还需要补齐请求量、成功率、延迟分位数、模型/地域分布、客户端失败、重试后的任务成功率与质量评测。对于应用本身，分别观察“能连接”“能生成”“结果可用”“任务完成”比复用一个供应商状态页百分比更有意义。

本版不提供跨供应商优劣排名。与仓库中的 OpenAI 报告比较前，应先统一观察窗口、服务范围、分类定义、代理时间处理及语义复核程度。

## 十、交付物与复算入口

- [单一事故 CSV](incidents.csv)：UTF-8 BOM、48 列；完整原始对象、更新、证据、未知项均在同一文件。
- [CSV 校验结果](incidents.validation.json)、[历史快照](snapshot.json)、[枚举轨迹](history-index.json)。
- [重点分析](analysis.json)、[服务观察窗口](service_windows.json)、[年度及同期数据](trend_data.json)、[暂停敏感性数据](summary-data.json)。
- [参考区间](reference-intervals.json)、[本地复算脚本](tools/analyze.py)、[报告生成脚本](tools/build_report.py)。

CSV SHA-256：`b50a7d41560e6b95a1976bf5301980dbdc2b0466d587dba0aa05156300282416`。

原始 HTTP 响应体哈希与规范化事故对象哈希分开记录。后者使用键排序、UTF-8、无多余空白 JSON，不冒充网络原始字节。产物只保存在本地工作目录，未提交或推送 GitHub。

## 附录：参考序列无可用时间区间的 121 起事故

下表包括只有事后结案、缺官方严重度、仅有持续时长、时间冲突或实际阶段早于公告而不能定位的记录。缺失不计为零；完整原文可从 CSV 或 HTML 事故索引查看。

| 公告日期 | 事故 | 官方等级 |
| --- | --- | --- |
| 2023-03-14 | [Elevated API Errors](https://status.claude.com/incidents/85cf5bgslwtw) | full_outage |
| 2023-03-15 | [Elevated API Errors](https://status.claude.com/incidents/cpssy4797smx) | full_outage |
| 2023-06-16 | [Some users saw elevated rates of 529s](https://status.claude.com/incidents/7m1st8049qkz) | unknown |
| 2023-06-20 | [Partial outage caused 5xx errors](https://status.claude.com/incidents/rt1kx84m7jvw) | unknown |
| 2023-07-05 | [Intermittent errors with Console and API](https://status.claude.com/incidents/szljggrq2y2f) | unknown |
| 2023-07-18 | [Elevated errors for sign up page](https://status.claude.com/incidents/gy6zjzf1f719) | unknown |
| 2023-08-02 | [529s on claude-instant-v1.1](https://status.claude.com/incidents/w604spz451n2) | unknown |
| 2023-08-10 | [claude.ai and claude-instant-1.2 were partially degraded](https://status.claude.com/incidents/ddcqt95wb9g2) | degraded_performance |
| 2023-11-15 | [Elevated API error rate](https://status.claude.com/incidents/llqq0177mckq) | degraded_performance |
| 2023-12-12 | [API Outage](https://status.claude.com/incidents/z3v941z3z11b) | unknown |
| 2023-12-18 | [API Errors for Claude Instant](https://status.claude.com/incidents/xw2dtvb27gjf) | unknown |
| 2024-01-25 | [Elevated error rates on a subset of models](https://status.claude.com/incidents/ldbx9tw6f7d9) | unknown |
| 2024-01-29 | [Elevated API error rate across all models](https://status.claude.com/incidents/qxdvjb4njp6q) | degraded_performance |
| 2024-01-30 | [brief partial outage of claude-instant-1.2, claude-2.1](https://status.claude.com/incidents/3667134hg62q) | unknown |
| 2024-01-31 | [elevated error rate on claude-2.1](https://status.claude.com/incidents/rqpd1jfqmglp) | unknown |
| 2024-01-31 | [elevated error rates on some models](https://status.claude.com/incidents/w3g5jpznssrd) | unknown |
| 2024-01-31 | [Claude.ai Experienced a Temporary Outage](https://status.claude.com/incidents/shhpbrjb160c) | unknown |
| 2024-02-03 | [Elevated error rate on claude.ai](https://status.claude.com/incidents/h1lxbyszyxrq) | unknown |
| 2024-02-05 | [elevated error rates on claude-instant-1.2](https://status.claude.com/incidents/gr7nb0dwyydw) | unknown |
| 2024-02-13 | [Elevated error rate on Claude-2.0, Claude-2.1](https://status.claude.com/incidents/x5f4s8nvkyqq) | unknown |
| 2024-02-13 | [Elevated error rate on Claude-2.0, Claude-2.1](https://status.claude.com/incidents/t6v85cs8j6jb) | unknown |
| 2024-02-16 | [Elevated error rate on claude.ai](https://status.claude.com/incidents/tmsczhzhjd63) | unknown |
| 2024-03-04 | [Elevated error rate on claude-1.3](https://status.claude.com/incidents/6ffzsdcx4cll) | unknown |
| 2024-03-26 | [Claude Instant 1.2 Partial Outage](https://status.claude.com/incidents/xpc4kjt7t0cw) | unknown |
| 2024-04-01 | [Sonnet Partial Outage](https://status.claude.com/incidents/yk00k5x6jzc3) | unknown |
| 2024-04-09 | [Degraded Performance on Claude Instant 1.1](https://status.claude.com/incidents/86fff0g4f2wh) | unknown |
| 2024-04-18 | [Outage affecting account creation and document upload](https://status.claude.com/incidents/0dv5d8qb9gy2) | unknown |
| 2024-04-18 | [Claude 2.1 partially unavailable](https://status.claude.com/incidents/58vcrhzjsngy) | unknown |
| 2024-04-21 | [Claude 3 Opus partially down](https://status.claude.com/incidents/y4fmbrf3wztd) | unknown |
| 2024-04-22 | [Login and account creation partial outage](https://status.claude.com/incidents/4p353c7twb1k) | unknown |
| 2024-04-30 | [Claude Instant 1.2 Partial Outage](https://status.claude.com/incidents/0qyp857kns2b) | unknown |
| 2024-05-16 | [Claude 3 Haiku Outage](https://status.claude.com/incidents/gkbl04hwljz2) | unknown |
| 2024-05-23 | [Increase error rates on Opus](https://status.claude.com/incidents/mq3nthmx16ly) | unknown |
| 2024-05-29 | [Haiku sampling errors](https://status.claude.com/incidents/dmqg1fbfs0wq) | unknown |
| 2024-06-03 | [Images Cropped to Square](https://status.claude.com/incidents/vyw1vz0h6c1x) | unknown |
| 2024-06-04 | [Opus in Vertex Complete Outage](https://status.claude.com/incidents/ysbg73gy3ctm) | partial_outage |
| 2024-06-20 | [Elevated errors on Console billing UI](https://status.claude.com/incidents/6y3n60jm23w1) | unknown |
| 2024-06-28 | [Claude.ai iOS logins unavailable](https://status.claude.com/incidents/8p49xrt1lmzy) | unknown |
| 2024-07-19 | [API errors elevated](https://status.claude.com/incidents/8mlvgc29rvxg) | partial_outage |
| 2024-08-06 | [Errors when signing up for Claude Pro or Claude Team plans](https://status.claude.com/incidents/s27y0sgpmp75) | unknown |
| 2024-08-28 | [Bug affecting responses in claude.ai](https://status.claude.com/incidents/kygj9sjs8dxr) | partial_outage |
| 2024-09-19 | [3.5-Sonnet Partial Outage](https://status.claude.com/incidents/gg215bzz7rhm) | unknown |
| 2024-10-30 | [Elevated errors for requests to Claude 3.5 Sonnet](https://status.claude.com/incidents/69qlg67hcvzf) | unknown |
| 2024-11-18 | [Connectivity issues to api.anthropic.com via IPv6](https://status.claude.com/incidents/63g2v72fv7nf) | unknown |
| 2024-11-27 | [Elevated errors for requests to Claude 3.5 Sonnet](https://status.claude.com/incidents/nwn20mzh9v1k) | unknown |
| 2024-12-01 | [Elevated errors for requests to Anthropic API](https://status.claude.com/incidents/b3zd1rqxycty) | unknown |
| 2024-12-02 | [Elevated errors for request to Anthropic API](https://status.claude.com/incidents/lq1wnj3bp7sc) | unknown |
| 2024-12-13 | [Elevated errors on the Anthropic API](https://status.claude.com/incidents/nh9j7wwgn40f) | unknown |
| 2024-12-17 | [Unauthorized post from @AnthropicAI X.com account](https://status.claude.com/incidents/mzyhcbn140fg) | unknown |
| 2025-01-09 | [Elevated errors on the API](https://status.claude.com/incidents/fwj5yn2lmbrc) | partial_outage |
| 2025-01-21 | [Some functionality was temporarily unavailable on Claude.ai for Android](https://status.claude.com/incidents/ln4ydqzd19hf) | unknown |
| 2025-01-29 | [Elevated errors on Claude 3 Haiku](https://status.claude.com/incidents/3170lkhmkxr4) | partial_outage |
| 2025-01-31 | [Elevated errors for requests to Claude 3.5 Sonnet](https://status.claude.com/incidents/fx2llhlh4r5x) | unknown |
| 2025-02-03 | [Elevated errors for requests to Claude 3.5 Sonnet](https://status.claude.com/incidents/47prgf2smzt6) | unknown |
| 2025-02-15 | [Elevated errors for requests to Claude 3.5 Sonnet](https://status.claude.com/incidents/bs75nnsf8cyt) | unknown |
| 2025-02-28 | [Elevated errors for requests to Claude 3.5 Sonnet 0620](https://status.claude.com/incidents/72htcpnbt13m) | unknown |
| 2025-03-01 | [Errors when loading or publishing artifacts on Claude.ai](https://status.claude.com/incidents/pk04blzw542b) | unknown |
| 2025-03-05 | [Elevated errors on requests](https://status.claude.com/incidents/69pspdr7qhpx) | unknown |
| 2025-03-12 | [Chats in projects inaccessible for some](https://status.claude.com/incidents/lm8pzk6sgc7y) | unknown |
| 2025-03-13 | [Errors when accessing anthropic.com](https://status.claude.com/incidents/bybj2w3097hm) | unknown |
| 2025-03-24 | [Invalid responses on Claude.ai chats](https://status.claude.com/incidents/v8vxwtcbmhkn) | unknown |
| 2025-04-07 | [Claude 3.5 Sonnet (Oct 2024) Performance Degraded](https://status.claude.com/incidents/vtx2xkfwrk1l) | unknown |
| 2025-04-10 | [Errors when logging into Claude.ai](https://status.claude.com/incidents/2cx6v2tzn93f) | unknown |
| 2025-04-15 | [Elevated errors on June Sonnet 3.5](https://status.claude.com/incidents/n6ymdsbsyyyt) | unknown |
| 2025-04-15 | [Elevated errors on Sonnet 3.5 (new)](https://status.claude.com/incidents/5szs0c4l877d) | unknown |
| 2025-04-21 | [Errors when uploading some filetypes on Claude.ai with analysis tool enabled](https://status.claude.com/incidents/3yqln2w85bbj) | unknown |
| 2025-04-22 | [Elevated errors on October Claude 3.5 Sonnet](https://status.claude.com/incidents/r23nwp7jkb3g) | unknown |
| 2025-04-24 | [Errors with MCP tool calls on the Claude.ai desktop application](https://status.claude.com/incidents/88h6cq32bqm4) | unknown |
| 2025-04-25 | [Elevated errors on request to models](https://status.claude.com/incidents/h4bygm7vgqkj) | unknown |
| 2025-05-01 | [SSO Sign-In Issues](https://status.claude.com/incidents/cbpk1sqc6v9q) | unknown |
| 2025-05-24 | [Incorrect display of 'Legacy Model' on Claude.ai for conversations with Opus 4](https://status.claude.com/incidents/xsz3fc747v2f) | unknown |
| 2025-06-06 | [Claude 3.5 Haiku model unavailability](https://status.claude.com/incidents/z44n21ynfwj1) | unknown |
| 2025-06-24 | [Elevated errors on Claude Opus 4](https://status.claude.com/incidents/jcylpkfhbptn) | unknown |
| 2025-07-03 | [Elevated errors on Claude 4 Sonnet](https://status.claude.com/incidents/1h88fg0hzgnv) | unknown |
| 2025-07-13 | [Elevated errors for requests to Claude 4 Sonnet](https://status.claude.com/incidents/3djkkk0p2778) | unknown |
| 2025-07-29 | [SSO login issue affecting the Claude desktop app](https://status.claude.com/incidents/kmyd15zlf718) | unknown |
| 2025-07-30 | [Claude.ai chats appearing out of chronological order](https://status.claude.com/incidents/qzb538gk5ty7) | unknown |
| 2025-08-18 | [Subscription Upgrade Broken](https://status.claude.com/incidents/32dd02bbkl68) | unknown |
| 2025-08-19 | [Subscription Upgrade Broken](https://status.claude.com/incidents/1wh7f960t9pm) | unknown |
| 2025-08-21 | [Elevated errors on Claude Opus 4.1](https://status.claude.com/incidents/9g1p197bp5rf) | unknown |
| 2025-08-29 | [Claude Opus 4.1 and Opus 4 degraded quality](https://status.claude.com/incidents/h26lykctfnsz) | degraded_performance |
| 2025-09-09 | [Model output quality](https://status.claude.com/incidents/72f99lh1cj2c) | partial_outage |
| 2025-09-10 | [Claude.ai services impacted](https://status.claude.com/incidents/p8pczg3gxg2k) | unknown |
| 2025-09-12 | [Elevated errors on Claude Sonnet 3.7](https://status.claude.com/incidents/mp4tfl9fwdjc) | degraded_performance |
| 2025-09-28 | [claude.ai and Sonnet 4 errors](https://status.claude.com/incidents/ht5r3583n1cs) | unknown |
| 2025-10-03 | [Claude.ai, Claude Code, API, and console are experiencing degraded service](https://status.claude.com/incidents/gr1vrcvz9jd4) | unknown |
| 2025-11-07 | [Elevated errors for requests to Claude 4, 4.5 Sonnet and 4.5 Haiku](https://status.claude.com/incidents/tgtw1sqs9ths) | unknown |
| 2025-11-07 | [Elevated error rates on Files API](https://status.claude.com/incidents/5l56lb3k3p1t) | unknown |
| 2025-11-07 | [Elevated error rates for code execution tool](https://status.claude.com/incidents/tp0pm7zqm5lg) | degraded_performance |
| 2025-11-11 | [Elevated errors on Claude.ai](https://status.claude.com/incidents/4kv6xfjg5cz2) | unknown |
| 2025-11-14 | [Elevated error rates with Sonnet 4.5 and Opus 4.1](https://status.claude.com/incidents/4t6zrdblnxdy) | unknown |
| 2025-11-24 | [Elevated Errors on Claude Code](https://status.claude.com/incidents/j7lh1qm56hwr) | unknown |
| 2025-12-05 | [Elevated Error Rates on Claude API Code Execution and Advanced File Analysis Tools](https://status.claude.com/incidents/s8vj5mn9wvzf) | unknown |
| 2025-12-05 | [iOS Subscription Access Issues](https://status.claude.com/incidents/6rrnsb1y0kbn) | degraded_performance |
| 2025-12-12 | [Unable to start chats on claude.ai](https://status.claude.com/incidents/h140lstlzbw7) | partial_outage |
| 2025-12-12 | [Elevated errors on documentation site in Europe](https://status.claude.com/incidents/vdvhnlkdx045) | unknown |
| 2026-02-03 | [SSO and magic link sign-in degraded on Claude Desktop](https://status.claude.com/incidents/mhxgcgjrjy7k) | degraded_performance |
| 2026-02-06 | [Elevated error rates on claude.ai](https://status.claude.com/incidents/2gjynbb7ydph) | unknown |
| 2026-02-10 | [Elevated errors on Opus 4.6 Fast Mode](https://status.claude.com/incidents/90yshy009sqy) | unknown |
| 2026-02-14 | [Issues with Code Execution Tool](https://status.claude.com/incidents/49s6mwrdyz8j) | unknown |
| 2026-02-17 | [opus 4.6 elevated errors](https://status.claude.com/incidents/bryrpn54npvn) | unknown |
| 2026-02-21 | [Some Windows users unable to use Cowork](https://status.claude.com/incidents/j6qqhxswnpgw) | degraded_performance |
| 2026-04-01 | [Elevated timeouts on requests to Claude Opus 4.6 and Sonnet 4.6](https://status.claude.com/incidents/fvj2fgqrchsj) | partial_outage |
| 2026-04-04 | [Sonnet 4.6 and Opus 4.6 elevated error rate](https://status.claude.com/incidents/7n7xgqws441v) | unknown |
| 2026-04-08 | [Outage affecting Workspace Creation](https://status.claude.com/incidents/z0bqmftj68dr) | unknown |
| 2026-04-08 | [Errors when connecting to Claude.ai](https://status.claude.com/incidents/hsgj6gh6rlck) | unknown |
| 2026-04-10 | [Some Claude.ai share links were inaccessible](https://status.claude.com/incidents/ccm8hy0pld48) | degraded_performance |
| 2026-04-11 | [Email login down](https://status.claude.com/incidents/qcfvv041lb1k) | partial_outage |
| 2026-04-19 | [Elevated errors on Opus 4.6](https://status.claude.com/incidents/34yy5hskyw2v) | unknown |
| 2026-04-25 | [Investigated elevated errors and slower responses on claude.ai](https://status.claude.com/incidents/c3km369dp85h) | unknown |
| 2026-04-27 | [Elevated billing related errors on Claude.ai](https://status.claude.com/incidents/mct55f8gxb7k) | unknown |
| 2026-04-28 | [Claude Code Code Review was intermittently failing](https://status.claude.com/incidents/7bk0ftl0mpny) | unknown |
| 2026-05-25 | [Elevated error rates on Opus 4.7](https://status.claude.com/incidents/44pgyz54d48z) | unknown |
| 2026-06-16 | [Opus 4.8 errors](https://status.claude.com/incidents/8q88rrz9rjd0) | unknown |
| 2026-06-24 | [Elevated errors on Opus 4.8 Fast](https://status.claude.com/incidents/wkzf38t1yh8z) | unknown |
| 2026-06-27 | [elevated errors on Opus 48](https://status.claude.com/incidents/9284yk6xxd0h) | unknown |
| 2026-07-08 | [Issues authorizing to MCP Servers](https://status.claude.com/incidents/4y9nybhbljfc) | degraded_performance |
| 2026-07-10 | [Elevated errors for Claude Opus 4.5 and Claude Sonnet 4.5](https://status.claude.com/incidents/6djcn2k6v8kp) | unknown |
| 2026-07-25 | [Sonnet 4.6 and Sonnet 5 errors elevated](https://status.claude.com/incidents/1019wwb67615) | unknown |
| 2026-08-14 | [Issues reaching status.claude.com](https://status.claude.com/incidents/kmbpgrsszf72) | unknown |
| 2026-09-16 | [Issues with Google Play subscriptions](https://status.claude.com/incidents/t8fpw9vcshl9) | unknown |
