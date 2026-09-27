# 数据源适配与完整性核验

## 选择顺序

| 类型 | 处理方式 | 不能做的推断 |
|---|---|---|
| incident.io 自定义域名 | 发现公开 summary → 分时间窗口读取 incidents → 保存原始组件影响与复盘 | 前端 proxy 是经观察的接口，非稳定产品承诺；不能视为永久契约 |
| Atlassian Statuspage | summary.json → incidents.json?page=N → scheduled-maintenances.json?page=N | 文档明确默认“最近50条”；名叫 all 不代表包含全部历史 |
| 无适配器的 HTML/动态网页 | 智能体用获授权的浏览器逐 History 窗口读取、保存 native JSON 或 generic 证据快照，再用同一导出器 | 不把网站颜色/加载中/RSS/搜索索引当全量和准确等级 |

## incident.io

2026-09-27 对 OpenAI 公共站点观察到：

```text
https://status.openai.com/proxy/status.openai.com/summary
https://status.openai.com/proxy/status.openai.com/incidents?start_at=...&end_at=...
```

历史接口限制单次时间跨度不超过约三个月；脚本默认30天串行读取，可设1—60天。
相邻窗口不留空档，边界记录按ID去重。窗口返回的记录可按影响/更新时间与窗口相交，导出用明确的 publication-window 选择口径，不能混同。
summary 中的 `data_available_since` 是站点历史元数据，不是产品上线时间。未指定 start 时留31天查询缓冲以容纳补发公告，缓冲不构成真实连续监测声明。

共享 incident.io 域名和子路径的路由可能不同；脚本不保证自动识别。用浏览器观察实际公开请求，再导入，不尝试有鉴权的管理API。返回新的 next_cursor/pagination 等结构时，脚本拒绝继续宣称枚举完成，需更新适配器。

## Statuspage

官方 Status API 文档示例：
https://status.atlassian.com/api/v2

```text
/api/v2/summary.json
/api/v2/incidents.json?page=1
/api/v2/scheduled-maintenances.json?page=1
```

默认列表仅最近50条。page 参数在具体站点是否工作必须验证：比较相邻页ID与最早时间；只有取得终止空页且未触发限制才标记接口枚举结束。重复相同页面、HTTP错误、字段缺失和超出安全页数均标 incomplete，不能直接统计为全部历史。遍历所有 API 页后仍应核对浏览器 History；API保留策略可能与界面不同。

保留 `impact`、`incident_updates`、`components`、`postmortem`。
默认 critical→full、major→partial、minor→degraded 只是透明映射；“major/critical”可描述严重性而非整个服务完全中断，必须结合描述复核。none/maintenance/缺失值不映射成正常。
组件的**当前状态**不能冒充历史阶段；未提供组件时间区间时，最多采用有标签的公告代理或显式描述证据。

## 浏览器/Firecrawl 后备方式

先确认可用工具契约。可以读取公开页面和保存响应，不可借站点脚本绕过工具安全拦截。
页面一次只显示一个窗口时逐页读取；记录旧/新窗口、ID列表和证据文件。不要仅“成功点击下一页”就声明相应年份已完成。

要把 JSON 转出插件环境，先做小样本实际文件转交测试；可用正规附件或工具支持的文件参数。未授权不得上传第三方临时服务器；不能凭远程 `/mnt/data` 路径捏造 ChatGPT sandbox 链接。

## 网络边界

只允许公开 HTTPS 默认端口，不继承环境代理凭证；DNS检查阻止私网/环回/链路本地地址，重定向不得跨源。生产服务端接收不可信URL时仍须配置出站网络隔离，代码的DNS预检查不是抵御DNS重绑定的完整网络沙箱。
单次响应上限20MiB、单次超时30秒、默认请求间隔0.3秒、可重试429/5xx最多3次、401/403停止该路径。
`raw/` 缓存校验原始字节SHA；中断后同一运行复用原始页，不把缓存更新成不同时间快照。

## 一手参考（查阅日期：2026-09-27）

- Agent Skills 构建格式：https://developers.openai.com/codex/skills/
- Agent Skills 指南：https://developers.openai.com/api/docs/guides/tools-skills
- Statuspage 官方公共API：https://status.atlassian.com/api/v2
- OpenAI 官方历史：https://status.openai.com/history
- OpenAI 公开前端数据实例：https://status.openai.com/proxy/status.openai.com/summary

以上来源用于格式和适配约束，不是各家事故数量或真实可用性的证据。
