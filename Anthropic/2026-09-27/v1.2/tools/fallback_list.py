"""Show applied fallback decisions and remaining unknown records from the final CSV."""
import sys,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parents[2]/'.agents/skills/incident-research/scripts'))
from core import read_csv
R=read_csv(ROOT/'incidents.csv');F=[r for r in R if 'official_color_fallback' in r['quality_flags_json']];U=[r for r in R if r['record_type']=='incident' and r['assessed_severity']=='unknown']
def row(r):
 a=r['evidence_json']['assessment'];events=a.get('official_fallback',{}).get('phase_decisions',[]);sources=sorted({x['raw_value'] for x in events});ie=a.get('official_fallback',{}).get('incident_grade_evidence')
 if ie:sources=sorted(set(sources)|{ie['raw_value']})
 return f"| {r['published_at_utc'][:10]} | [{r['incident_title'].replace('|','／')}](https://status.claude.com/incidents/{r['incident_id']}) | {a['semantic_grade']} | {r['assessed_severity']} | {', '.join(sources)} | {'有' if r['impact_intervals_json'] else '无'} |"
text='''# 官方颜色兜底调整明细 · v1.2

规则：分析已知阶段保留；未知阶段优先对应产品的历史组件颜色，其次事故级impact颜色。红色→F、橙色→P、黄色→D。无影响记录和维护排除；时间缺失不补造。

109条记录使用兜底，其中93条原事故等级unknown，16条为混合事故中的未知阶段。531个阶段保存原始官方字段、update_id、component_id和映射结果，详见CSV的severity_evidence。事故最高等级可能与阶段颜色不同，统计以阶段为准。

| 公告日期UTC | 官方公告 | 原分析等级 | 有效等级 | 采用的官方代码 | 有计量阶段 |
| --- | --- | --- | --- | --- | --- |
'''+ '\n'.join(row(r) for r in F)
text+='\n\n## 剩余11条unknown：8条无可用等级，3条明确无影响\n\n| 日期UTC | 官方公告 | 原因 |\n| --- | --- | --- |\n'
for r in U:
 note='厂商确认无服务或用户请求影响；排除故障时长' if 'no_user_impact' in r['quality_flags_json'] else '分析无法判定，且无可用官方故障颜色；继续保留未知'
 text+=f"| {r['published_at_utc'][:10]} | [{r['incident_title']}](https://status.claude.com/incidents/{r['incident_id']}) | {note} |\n"
text+='\n[完整CSV](incidents.csv) · [主报告](../../Anthropic_Claude_Availability_Report_2026-09-27_v1.2.html)\n'
(ROOT/'官方颜色兜底调整明细.md').write_text(text)
print('Fallback records',len(F),'Remaining unknown',len(U))
