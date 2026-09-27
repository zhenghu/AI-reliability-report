# Anthropic / Claude v1.1

打开 [本版本归档主报告](Anthropic_Claude_Availability_Report_2026-09-27_v1.1.html)。已内嵌全部图表和920条审阅索引，可离线浏览。主交付为48列UTF-8 BOM的 incidents.csv。

冻结快照和原始证据位于同级 `../v1.0/`，v1.1不修改它。reviews/ 是三个互不重叠时间片的全文语义审阅记录；tools/analyze.py 合并并绑定原始对象hash。未知不填0，时间代理不冒充真实停机。完整口径见事故等级定义.md。

复算：在仓库根运行 `python3 Anthropic/2026-09-27/v1.1/tools/analyze.py`，随后用已有含 reportlab 和 pypdfium2 的 Python 运行 tools/charts.py，再运行 tools/build_report.py 和 tools/verify.py。全部无网络，重新生成本版本派生物，不改变v1.0。绘图实际环境为内置Python3.12、ReportLab4.4.9及PDFium；无额外安装。

本机绘图命令：

```
/Users/nanasmac/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 Anthropic/2026-09-27/v1.1/tools/charts.py
```

figures/ 每图含SVG/PNG/PDF和源数据CSV。trend_data.json主序列只来自incidents.csv的impact_intervals_json；assessed-intervals.json的unknown_intervals只用于敏感性场景。未提交、推送或公开发布。
