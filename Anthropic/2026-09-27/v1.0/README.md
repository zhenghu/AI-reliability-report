# Anthropic / Claude 可用性研究 · 2026-09-27

先打开 `Anthropic_Claude_Availability_Report_2026-09-27_v1.0.html`。本版为公开状态参考估计，不是全量语义核验定稿或 SLA。

主交付 `incidents.csv` 为 48 列 UTF-8 BOM，920 条；精确冻结范围与缺口见报告。

`trend_data.json` 来自 CSV 的 `evidence_json.reference_intervals`，不是未完成的分析区间。不要误用通用聚合器把后者当完整时长。

在仓库根目录，用已有 Python 3 运行：

```sh
python3 Anthropic/2026-09-27/v1.0/tools/analyze.py
python3 Anthropic/2026-09-27/v1.0/tools/build_report.py
python3 Anthropic/2026-09-27/v1.0/tools/verify.py
```

复算脚本只读本轮快照；会重建本轮派生文件，不访问网络。新的采集应新建版本目录，不能对本轮改变 cutoff。

`evidence/` 为原始 HTTP 响应体与单独元数据，`snapshot.json` 为整合后的规范化快照。失败路径保存在 coverage 元数据中。

未安装软件，未使用凭证，未提交或推送 GitHub。
