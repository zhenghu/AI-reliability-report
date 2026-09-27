# incident-csv-v1 与中间文件契约

主交付为单一 CSV，UTF-8 BOM、RFC 4180 风格引号；每个 `(company_id, incident_id)` 一行。
数组和对象写成 JSON 单元格，所有事件原文保留在 `raw_incident_json`。
Python 3.10+ 标准库即可运行，不需要模型 API key。完整报告的绘图依赖仍使用仓库 requirements.txt。

## 字段

| 类别 | 列 | 含义 |
|---|---|---|
| 身份 | schema_version, company_id, company_name, status_page_url, source_platform, incident_id, incident_title | 固定版本 incident-csv-v1；平台为 incidentio/statuspage/generic |
| 状态 | record_type, incident_status | incident 或 maintenance；状态保持供应商原值 |
| 公告 | published_at_utc, first_update_at_utc, first_resolved_at_utc, last_update_at_utc | 统一带时区时间；未知为空，不能当影响起止 |
| 官方等级 | official_severity, official_severity_codes_json | 统一映射结果与原始代码同时保留；Statuspage impact 映射不是全站宕机的证据 |
| 分析等级 | assessed_severity, severity_basis, severity_scope | 分析结论与判断口径，unknown 仅表示证据缺失 |
| 服务 | service_groups_json, components_json | 名称/ID/分组；当前组件树不是历史上线时间 |
| 影响范围 | impact_start_at_utc, impact_end_at_utc | 已知阶段的最早/最晚边界；两者之差不是影响时长 |
| 并集时长 | impact_seconds, known_full_seconds, known_full_partial_seconds, known_all_seconds | 单事故内去重的累计秒数；无可定位阶段时为空，不填0；跨事故仍须再次取并集 |
| 时间质量 | time_basis, time_complete, right_censored | 明确影响/官方区间/公告代理/未知；是否完成语义时间核对；未结束或超出 cutoff 的截断 |
| 分析 | review_status, analysis_summary, root_cause, root_cause_status | needs_review/assessed；根因 not_assessed/not_disclosed/vendor_stated/hypothesis |
| 证据 | evidence_json, updates_json, impact_intervals_json, official_intervals_json, source_urls_json | 引文与分析侧车、完整更新、用于计算的阶段、未经改动的官方阶段、原始来源 |
| 原始数据 | raw_incident_json, raw_sha256 | 原始事故对象；哈希是键排序、UTF-8、无空白 JSON 的 SHA-256，不冒充 HTTP 原始字节哈希 |
| 质量 | quality_flags_json | 缺等级、缺时间、代理时间、映射未知、区间被结案裁切等 |
| 范围 | requested_start_utc, cutoff_utc, retrieved_at_utc | 查询起点、冻结截止、实际抓取时间 |
| 运行元数据 | coverage_status, collection_run_id, analysis_version, spreadsheet_escaped_fields_json | 覆盖状态、运行ID、分析工具版本、CSV防公式注入的转义列名 |

不同供应商 service_groups 的范围不会自动变得可比；必须在报告中固定产品范围。
`time_complete=True` 只用于智能体确认证据能够定位整个相关影响时间线的记录，不来自机器看到一对起止时间。
当前官方区间与代理时间可以被保留并参与**显式允许**的估计；默认聚合不将未核对数据伪装成定稿。
CSV 复读会还原被前置单引号保护的文本，原始 JSON 从不改写。超长 JSON 不适合在 Excel 中另存，使用 CSV 解析器。

## snapshot.json

collect 输出或浏览器助手导入使用相同快照。手动/工具导入未验证覆盖时，必须写 `unverified`，不要伪造已枚举标记。

```json
{
  "schema_version": 1,
  "platform": "incidentio",
  "company": {"id": "provider", "name": "Provider"},
  "status_page_url": "https://status.example.com",
  "start_utc": "2025-01-01T00:00:00Z",
  "cutoff_utc": "2026-01-01T00:00:00Z",
  "retrieved_at_utc": "2026-01-02T00:00:00Z",
  "run_id": "provider-2025-frozen",
  "components": {"api-id": {"id":"api-id", "name":"API", "group":"API"}},
  "coverage": {"status":"unverified", "cross_check":"not_performed", "errors":[]},
  "records": [{
    "raw": {"id":"incident-1", "name":"Example", "published_at":"2025-06-01T00:00:00Z", "status":"resolved", "updates":[]},
    "source_urls": ["https://status.example.com/incidents/incident-1"],
    "evidence_documents": []
  }]
}
```

三个 native shapes：incidentio 的 updates/component_impacts/status_summaries；Statuspage 的 incident_updates/components/impact；generic 的 id/name/published_at/status/updates。generic 是浏览器提取中间格式，不是厂商 JSON：**不能在 generic 中伪造官方组件阶段**，描述产生的阶段必须走 analysis.json 并附引用。

额外复盘、HTML、PDF 证据可写入 `evidence_documents`：`{"url":"原始官方URL", "text":"保存的原文", "sha256":"原文UTF-8字节SHA256"}`。PDF需保留页码，识别表格/图像时由执行工具截图核对，不把 OCR 错字当时间证据。`source_urls` 中的 native API URL 证明整条事故对象；额外文档的引用只匹配该 URL 的保存原文。

## analysis.json

```json
{
  "schema_version": 1,
  "records": [{
    "incident_id": "incident-1",
    "source_record_sha256": "用 core.digest(raw) 计算",
    "severity": "partial_outage",
    "service_groups": ["API"],
    "summary": "受影响范围与恢复过程的中文概述",
    "root_cause": "",
    "root_cause_status": "not_disclosed",
    "time_complete": true,
    "evidence": [
      {"kind":"severity", "source_url":"官方URL", "quote":"实际保存原文中的短引文"},
      {"kind":"service", "source_url":"官方URL", "quote":"实际服务归属证据"},
      {"kind":"time", "source_url":"官方URL", "quote":"实际起止时间证据"}
    ],
    "intervals": [{
      "start_at":"2025-06-01T00:00:00Z", "end_at":"2025-06-01T00:10:00Z",
      "severity":"partial_outage", "service_groups":["API"],
      "time_basis":"explicit_impact", "right_censored":false, "evidence_indices":[0,1,2]
    }]
  }]
}
```

只校正需要改变的记录即可；没有分析的记录仍标 needs_review。改变存在阶段的等级或服务归属时必须明确给出完整阶段列表，不能把整条事故最高等级静默套在每个阶段。`intervals: []` 用于确认无法定位时间，必须保持 `time_complete:false`。
证据类型为 severity/time/service/root_cause/summary。脚本核验引文存在、更新ID、原始哈希、时区及阶段正长度；智能体核验语义支持和是否仍缺阶段。
根因 `hypothesis` 必须在报告里明确为假说，不作为厂商确认的根因占比统计。

## service_windows.json 与报告桥接

```json
{
  "company_id":"provider",
  "overall_group":"Overall",
  "service_windows":{
    "Overall":{"start":"2025-01-01T00:00:00Z","end":"2026-01-01T00:00:00Z"},
    "API":{"start":"2025-01-01T00:00:00Z","end":"2026-01-01T00:00:00Z"}
  }
}
```

聚合结果兼容仓库 `trend_data.json` v1，有 annual、cutoff_utc 和空 matched_windows。
未知区间/等级需要 `--allow-estimates` 明确允许；采集不完整还需 `--allow-incomplete`。
空 CSV 不能独立证明一段时间内零事故，聚合默认拒绝。
为报告准备 Markdown 和 `configs/` 中的公司配置后，调用原 `scripts/publish_report.py`。
此 Skill 不会把采集或分类结果强行拟合到 OpenAI 历史报告已有数值，也不会自动生成同期期限比较。
