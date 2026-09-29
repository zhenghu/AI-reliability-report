# OpenAI 根因分析专题

已完成冻结数据校验、76 条公开复盘阅读与提取、代表案例官方页面核验，以及故障模式和技术方向归纳。

结论：公开复盘显示变更、共享依赖、重试和恢复自动化相互耦合；优先验证变更隔离与恢复能力，随后补齐推理正确性、任务完成和数据完整性。76 条复盘记录占 1,006 条事故记录的 7.55%，存在同事故复用复盘的情况，不能据此推断全量根因占比。

- [report.md](report.md)：完整中文分析，含 14 个代表案例、7 类故障模式、工程方向、验收设计及局限。
- [sources.md](sources.md)：官方链接、输入哈希、日期冲突与共因说明。
- [analysis/writeups.json](analysis/writeups.json)：提取后的 76 条冻结复盘。
- [analysis/verification.json](analysis/verification.json)：唯一 ID、类型、年度、字段数、更新数、正文提取路径复核。
- [analysis/extract.py](analysis/extract.py)：只使用 Python 标准库的可重跑提取脚本。

## 复算

在本目录运行，Python 3 标准库即可；无需额外安装依赖：

```sh
python3 analysis/extract.py /Users/nanasmac/Downloads/OpenAI_all_incidents_2021-02_to_2026-09-27.csv
```

换机器时改为实际原始 CSV 路径，并核对 `verification.json` 内输入哈希。原始 CSV 位于用户 Downloads，不复制整份重复数据入专题；76 条复盘正文已在专题保留，可直接审阅。

脚本复现计数、提取和精确文本去重；案例因果拆解及技术建议属于人工阅读分析，不宣称由脚本自动验证。年度按公告年份统计；缺少复盘不等于没有因果信息。未改写原始 CSV、既有可用性报告或其统计。

下一步需要内部 trace、依赖拓扑与演练数据，才能量化不同机制的损失贡献和改进收益。
