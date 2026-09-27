# DeepSeek · 2026-09-27 · v1.0

[打开 HTML 报告](DeepSeek_Availability_Report_2026-09-27_v1.0.html) · [Markdown](DeepSeek_Availability_Report_2026-09-27_v1.0.md) · [主交付 CSV](incidents.csv) · [资料包](DeepSeek_Availability_Audit_2026-09-27_v1.0.zip)

冻结截止 2026-09-27 19:36:20 UTC。103 起事故、2 条维护、314 条更新；按月枚举并与 17 个 History 页面交叉核验。HTML 内嵌图表并含全部记录的搜索索引。报告开篇为整体和全部纳入应用的同表、同图年度总结。

本仓库研究归档。临时 Cookie 响应头已去除，原始响应 body 字节不变。raw/ 是原始响应；*.meta.json 保存 URL、抓取时刻及 HTTP 响应 body 字节 SHA-256。CSV raw_sha256 是另一层规范化事故对象哈希，不混用。两起事故缺可信时长；三起使用公告窗口代理；长公告敏感性和历史组件改名均在正文说明。

复算不访问网络：先运行 `python3 tools/analyze.py`、`python3 tools/verify_coverage.py`，再在已有 reportlab、pypdfium2 的 Python 中运行 `tools/charts.py`，最后运行 `python3 tools/build_report.py`。本版使用独立 Flashduty 分析适配，未改动通用展示管线。tools/collect.py 为有网络的采集复现脚本，默认读取已保存断点；不要将后续新数据混入本冻结目录。

报告不证明真实请求成功率或未披露事故完整性。未经正文中的口径说明，不宜与其他供应商排名。
