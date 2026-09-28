## 九、事故根因与可靠性工程方向（2026-09-28补充复核）

916起事故中，原32条vendor_stated仅占3.49%，且并非都有完整技术根因。本次区分：11条机制或直接失效方式、9条触发变更/缺陷、11条故障域定位、1条仅恢复动作；另有880条现有材料未披露原因、3条明确无影响、1条主动暂停。证据不足时不推断为GPU、容量或网络故障。

优先方向为发布与配置安全、语义质量可靠性和可观测性；随后完善依赖隔离与任务恢复、客户端兼容、数据/协议完整性、订阅权益一致性。方向与验收指标基于有明确证据的案例推导，属于研究建议，不是厂商内部控制缺失的事实。

| 方向 | 对应事故机制或现象 | 建议验证重点 |
| --- | --- | --- |
| 可观测性与事故通信 | [2026-08-14 · Issues reaching status.claude.com](https://status.claude.com/incidents/kmbpgrsszf72) | 演练业务失败但HTTP 200、状态页证书失效；核查任务SLI和告警是否触发。 |
| 发布与配置安全 | [2024-01-30 · brief partial outage of claude-instant-1.2, claude-2.1](https://status.claude.com/incidents/3667134hg62q)；[2026-05-06 · Connection failures for organizations restricting GitHub access by IP address](https://status.claude.com/incidents/snxm62gpxfc9) | 错误配置注入与回滚演练；测量坏版本暴露范围、检测时间、回退完成时间。 |
| 语义质量可靠性 | [2025-07-10 · Claude Sonnet 4 degraded performance quality](https://status.claude.com/incidents/4q9qw2g0nlcb)；[2025-08-29 · Claude Opus 4.1 and Opus 4 degraded quality](https://status.claude.com/incidents/h26lykctfnsz) | 验证已知异常用例能阻断变更，统计质量回归漏检及误报；不要求随机生成逐字一致。 |
| 依赖隔离与恢复 | [2024-08-08 · Elevated error rates on 3.5 Sonnet and 3 Opus](https://status.claude.com/incidents/q5dvt5ph7tzx)；[2025-06-12 · Elevated errors on the API, Console and Claude.ai](https://status.claude.com/incidents/kn7mvrgb0c8m) | 注入依赖超时/断连，测量重试放大、恢复后积压排空、重复副作用和任务恢复率。 |
| 客户端状态与兼容 | [2026-02-26 · Claude Code showing "JSON Parse error: Unexpected EOF" and writing excessive files on Windows](https://status.claude.com/incidents/3kjy2zn2w2bj)；[2026-03-08 · Claude Desktop app unresponsive](https://status.claude.com/incidents/pqpgkf52p3tg) | 故障注入验证写入中断不损坏配置、调度有界终止、旧会话恢复和工作区访问正确。 |
| 数据与协议完整性 | [2024-06-03 · Images Cropped to Square](https://status.claude.com/incidents/vyw1vz0h6c1x)；[2025-05-09 · Elevated errors on Research](https://status.claude.com/incidents/926d2gm87s8c) | 验证引用保留率、图片变换正确性、协议回退成功率、允许列表误删恢复。 |
| 订阅与权益一致性 | [2025-12-05 · iOS Subscription Access Issues](https://status.claude.com/incidents/6rrnsb1y0kbn)；[2026-07-17 · Elevated errors across Fable 5](https://status.claude.com/incidents/g613ntyj2pwf) | 测量付款到权益生效时延、错误拒绝访问率、存量漏补数量；不以放宽认证代替恢复。 |
| 容量与服务连续性 | [2025-11-25 · Elevated errors for requests to Claude Opus 4.5](https://status.claude.com/incidents/5g213mxxlbsw)；[2026-06-13 · We’ve suspended access to Claude Mythos 5 and Claude Fable 5](https://status.claude.com/incidents/s9w82lp9dcn9) | 测量饱和拐点、重试放大和降级后的任务质量；生产目标依据业务SLO与基线确定。 |

详细的证据分层、32条归因逐项复核及工程方案见 [根因与可靠性工程专题](root-cause-review/Claude_事故根因与可靠性工程方向.html)（[Markdown](root-cause-review/Claude_事故根因与可靠性工程方向.md)）；[916起逐事故根因台账](root-cause-review/incident-root-causes.csv)保留每起的原字段、证据及判断。本次补充读取两条事故直接关联的官方技术复盘；不改变冻结事故数据、等级、时间区间和可用性数值。
