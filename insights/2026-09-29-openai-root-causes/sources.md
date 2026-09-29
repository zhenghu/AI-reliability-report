# 来源与证据边界

核验日：2026-09-29。事故日期与复盘发布日期不同；标题下日期按正文事故日期理解，不把 publication_year 当成实际影响年份。以下 S1–S14 都是一手厂商自述；技术方向为分析者建议。

| 编号 | 事故或材料 | 官方原文 | 本文用途 |
|---|---|---|---|
| S1 | 2024-12-11 API, ChatGPT & Sora | https://status.openai.com/incidents/01JMYB483C404VMPCW726E8MET/write-up | 遥测、Kubernetes、DNS 和恢复通道耦合；在线核验同事故旧短链 ctrsv3lwd797 |
| S2 | 2024-12-26 多服务高错误率 | https://status.openai.com/incidents/01JMYB44RFAHDFT1HWDPD0M2N5/write-up | 供电、区域数据库、人工跨区接管；在线核验 |
| S3 | 2025-06-09/10 Elevated error rates | https://status.openai.com/incidents/01JXCAW3K3JAE0EP56AEZ7CBG3/write-up | 主机自动更新、网络服务冲突与 GPU 节点恢复；在线核验 |
| S4 | 2025-02-26 Increased API error rates | https://status.openai.com/incidents/01JN2BQN4N618RG49BPMBDQGWZ/write-up | 账户迁移错误触发 429；在线核验 |
| S5 | 2026-02-04 ChatGPT Availability Impacted | https://status.openai.com/incidents/01KGMVV926ZSCD1MSDBS07AWYA/write-up | 数据库副本维护与重试放大；冻结正文核验 |
| S6 | 2026-03-04 API Error Rates | https://status.openai.com/incidents/01KJXQDJ6P1CG5YNXKZRY2H6RX/write-up | 过时调度队列批量执行；在线核验 |
| S7 | 2026-06-02/03 Codex, ChatGPT and Responses API | https://status.openai.com/incidents/01KT5XJ5ATD6RMYP908WS69FVD/write-up | 共享连接资源与多产品症状；在线核验 |
| S8 | 2026-07-25 Elevated error rates | https://status.openai.com/incidents/01KYC921K145JTR1JK7DYKGWH1/write-up | 不兼容配置回滚后再发布；在线与冻结正文核验 |
| S8b | 同一事件族另一记录 | https://status.openai.com/incidents/01KYCGY017EG43XZS6GFVXA8VH/write-up | 同因果与两个影响窗口，避免重复案例计数 |
| S9 | 2026-08-31 ChatGPT Work | https://status.openai.com/incidents/01M1C5M4K0WC8PPT0Z175RJA1E/write-up | 网络容量、内存与重试、任务准入；在线核验 |
| S10 | 2026-09-03 ChatGPT and Codex | https://status.openai.com/incidents/2rm6gqeh/write-up | 路由误解释与回流过载；在线核验；冻结 ID 01M1KWEDH417T2CF44YYHZDFCR |
| S11 | 2024-02-20 Unexpected responses | https://status.openai.com/incidents/01JMYB5NB6F20YWVCM96ABDTC1/write-up | 特定 GPU 配置下推理 kernel 算错；在线核验 |
| S12 | 2025-09-02/03 ChatGPT Not Displaying Responses | https://status.openai.com/incidents/01K47A0QGE7KMK2AHJZVYSTHXW/write-up | CDN 静态文件阻断、前端结果不可见；冻结正文核验 |
| S13 | 2025-10-02 RBAC 功能异常 | https://status.openai.com/incidents/01K6KAAN7WXN69E8JET8PYB0D5/write-up | 回填、权限错误与缓存恢复；冻结正文核验 |
| S14 | 2026-02 发现 API Platform Audit Logs | https://status.openai.com/incidents/01KJXA4N2X4W8KHZFSSFH0V0Q7/write-up | 服务拆分、事件漏投、监控盲区和不可恢复数据；在线核验 |

## 本地数据

- D1：`/Users/nanasmac/Downloads/OpenAI_all_incidents_2021-02_to_2026-09-27.csv`。用户本地已有全量公开事故采集数据。本次只读，SHA-256：`98ce305ebb39f3c32db363f1c9a74406963415f20bf9cc10afc78d526a348111`。
- D2：[既有可用性报告](../../OpenAI/2026-09-27/v1.1/OpenAI_Reliability_Report_2026-09-27_v1.1.md)。用于对齐统计范围，未重算、改写其可用性数据。
- D3：[analysis/writeups.json](analysis/writeups.json)。本次从 D1 提取的 76 条正文，保留 ID、来源、公告日期、文本提取路径及文本哈希。结构化文本按节点递归提取，使用换行保留边界。
- D4：[analysis/verification.json](analysis/verification.json)。计数与输入哈希复核。完全相同正文只检出一组，不等于所有共因记录都已去重。

## 其他人工检查线索

- 2023-03-18/19：`01JMYB7736QH17MQBBH8CA1PQA`、`01JMYB767FP69QVV5C72Y42ZJN`、`01JMYB76J0TCVZDY7PMK8BQQXQ` 共享 DALL·E 事件背景；后两条正文完全一致。
- 2023-03-20：`01JMYB75QBMB9WE7PVF1KMC4J5` 与 `01JMYB74N62B5JXY6PZNN1GSCX` 同根因，前者引用 DALL·E 复盘。
- 2025-07-15：`01K08JJK77JF5D2NN636SDY9WD`，共享无效配置导致多个服务 crash loop；复盘自身时间线冲突，未用于耗时计算。
- 2024-12-04：`01JMYB4A62XNXSAHAY8ZGQAAKD`，同一复盘有负载均衡配置错误与 DNS 缓存升级两种独立触发，说明一条记录也可能包含多个根因。
- 2026-03-11：`01KKFJRH4WP8X9YCX0W57ZXT9D`，正文写 2025 年，记录日期为 2026；不自行更正。

线上页面可以继续更新。本文事实以冻结正文为主，精选案例在线核验为辅；没有声明全部页面截至核验日均保持不变，也没有完整重抓历史。
