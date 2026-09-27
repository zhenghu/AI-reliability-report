"""Build Chinese Markdown and self-contained searchable HTML report, no network."""
import sys,json,html,re,ast,collections,hashlib,os
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'v1.0';REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'.agents/skills/incident-research/scripts'))
from core import read_csv,utc
R=read_csv(ROOT/'incidents.csv');T=json.loads((ROOT/'trend_data.json').read_text());S=json.loads((ROOT/'summary-data.json').read_text());V=json.loads((ROOT/'incidents.validation.json').read_text());W=json.loads((ROOT/'service_windows.json').read_text());BY={r['incident_id']:r for r in R}
STEM='Anthropic_Claude_Availability_Report_2026-09-27_v1.2'
REPORT_DIR=ROOT.parent.parent
def report_link(url):
 if url.startswith('#') or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:',url):return url
 return os.path.relpath((ROOT/url).resolve(),REPORT_DIR)
LABEL={'Overall':'整体（任一核心应用受影响）','Claude.ai':'Claude.ai','API':'第一方 API','Console':'Console','Claude Code':'Claude Code','Cowork':'Cowork','Government':'Claude for Government（政府版）'}
def pct(x):return f'{100*x:.4f}%'
def num(x):return f'{x:,.2f}'
def table(head,rows):return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+['| '+' | '.join(str(v).replace('|','／').replace('\n',' ') for v in row)+' |' for row in rows])
def incident(i):return f"[{BY[i]['incident_title']}](https://status.claude.com/incidents/{i})"
annual=[r for r in T['annual'] if r['group']=='Overall']
y26=[r for r in T['annual'] if r['year']==2026];overall=next(r for r in y26 if r['group']=='Overall');api=next(r for r in y26 if r['group']=='API');ex=next(r for r in S['sensitivity_2026'] if r['group']=='Overall' and r['series']=='exclude_suspension');ug=S['unknown_grade_incidents'];unresolved=S['unresolved_impact_grade_records'];ut=S['no_assessed_interval_incidents']
annual_map={(r['group'],r['year']):r for r in T['annual']}
def annual_cell(group,year):
 r=annual_map.get((group,year))
 if r is None:return '—（未进入观察期）'
 partial=r['window_start']!=f'{year}-01-01T00:00:00Z' or r['window_end']!=f'{year+1}-01-01T00:00:00Z'
 return pct(r['availability_all'])+(' *' if partial else '')
def figure(name,caption):return f'![{caption}](figures/{name}.svg)\n\n{caption}。可下载 [PNG](figures/{name}.png)、[SVG](figures/{name}.svg)、[图表数据](figures/{name}.csv)。'
counts=collections.defaultdict(collections.Counter)
for r in R:counts[r['published_at_utc'][:4]][r['record_type']]+=1
full=sorted([r for r in R if r['assessed_severity']=='full_outage'],key=lambda r:r['published_at_utc'])
noimpact=[r for r in R if 'no_user_impact' in r['quality_flags_json']]
unknown_time=[r for r in R if r['record_type']=='incident' and not r['impact_intervals_json']]
definitions='''# 事故等级与时间定义 · Anthropic v1.2

按用户指定规则：**分析可以判断时采用分析等级，分析无法判断时按官方颜色定级**。官方历史组件阶段颜色优先；该阶段没有可用颜色时采用事故 impact。红色 major_outage / critical→F，橙色 partial_outage / major→P，黄色 degraded_performance / minor→D。绿色/none 不当作未知故障的等级，蓝色维护单列排除。

分析等级在**命名产品的整体范围**上判定：Claude.ai、第一方 API、Console、Claude Code、Cowork、Claude for Government（政府版）。一个事故可以有多个产品、多个阶段和不同等级；事故行保存有效阶段的最高等级，计算使用逐阶段等级；无可定位阶段时仍可保存有证据的官方事故等级。`semantic_grade`保留原分析结论，`severity_basis`和阶段`severity_evidence`标明官方兜底来源。官方红色兜底的F不证明整个产品所有请求失败。

| 等级 | 必要证据 | 示例与边界 |
| --- | --- | --- |
| F / full_outage / 完整不可用 | 原文证明命名产品整体无法访问或无法提供核心服务 | Claude.ai 所有用户无法访问；不把单模型或登录路径失效升级成整个产品 F |
| P / partial_outage / 局部不可用 | 明确部分用户、模型、地区、请求、功能或访问路径不可用 | 指定模型失败、登录失败但已有会话未证明不可用、上传/连接器失败；若分析无法判断，转用官方颜色兜底 |
| D / degraded_performance / 性能或质量退化 | 延迟、输出质量、展示或数据完整性退化 | 高延迟、错误输出、使用量展示延迟；退化阶段不因同一事故曾出现 F 而全部升级 |
| unknown / 未知 | 分析和官方颜色均不足以定级；另保留已确认无影响的标记记录 | 非第四个事故等级，不等于无影响或可用；保留原文、原因及可定位候选时间 |

官方 critical / major / minor 及组件颜色在分析无法判断时用于兜底，不覆盖已判定的分析阶段；Investigating / Monitoring / Resolved 是处理状态，不是严重等级。已确认无用户影响的记录不因早期告警颜色再次算作故障。等级兜底不补造时间。根因只在厂商明确陈述时为 vendor_stated；否则为 not_disclosed（限已取得正文及可访问复盘）。

时间采用带时区的左闭右开区间 [start,end)。明确实际窗口优先，其次使用历史组件状态边界，最后使用公告活动周期代理；后两者仍不是测量的真实影响边界。Monitoring 不自动表示恢复；已明确恢复则结束该阶段；再次出错单独重开。迟报或复盘不延长故障。仅持续时长、无法定位日期、PT/UTC 自相矛盾的内容不生成虚假精确区间。

每项判断绑定原始事故对象 SHA-256，并保留原文引用及 update_id。time_complete 仅表示全部实际影响时间线可以定位；复核已完成不意味着证据必然完整。

可用性估计 A(S)=1−|union(S)|/T，其中 S 分别是 F、F∪P、F∪P∪D；跨年和服务观察起点裁切，维护不计入，产品间并发重新取并集。Overall 表示任一纳入产品受影响，绝不表示所有产品同时中断。服务窗口不从第一起事故反推上线时间。

未知等级的候选时间仅用于独立敏感性场景，不混入主分析阶段。未定位时间的故障没有被填成 0，但无法进入分子，因此估计的剩余时间不能视为全部已确认正常。结果不是实际请求成功率、官方 uptime、SLA 或统计置信区间。
'''
(ROOT/'事故等级定义.md').write_text(definitions)
md=f'''# Claude 可用性与事故复核报告

**Anthropic · v1.2 分析优先、官方颜色兜底 · 冻结截止 2026-09-27 16:10:43 UTC**

## 年度可用性总结

**按 F∪P∪D（完整不可用、局部不可用及性能或质量退化）口径，核心服务并集的可用性估计从 2023 年观察期的 {pct(annual[0]['availability_all'])}，降至 2024 年的 {pct(annual[1]['availability_all'])}、2025 年的 {pct(annual[2]['availability_all'])}，2026 年截至冻结时间为 {pct(annual[3]['availability_all'])}。** 其中两个完整年度 2024→2025 下降 {100*(annual[1]['availability_all']-annual[2]['availability_all']):.2f} 个百分点；只计 F 的各年估计均高于 99.8%，纳入 P、D 后下降更明显。

**各应用摘要：** 2026 年截至冻结时间，Claude.ai 为 **{pct(annual_map['Claude.ai',2026]['availability_all'])}**，第一方 API 为 **{pct(annual_map['API',2026]['availability_all'])}**，Claude Code 为 **{pct(annual_map['Claude Code',2026]['availability_all'])}**；Console 为 **{pct(annual_map['Console',2026]['availability_all'])}**。Cowork 与 Claude for Government（政府版）分别为 **{pct(annual_map['Cowork',2026]['availability_all'])} / {pct(annual_map['Government',2026]['availability_all'])}**，但观察期更短，不能据此直接排名。

下表与同一张折线图统一采用 **F∪P∪D** 口径，将整体和六个应用放在一起比较；F、F∪P 的明细保留在后文及年度结果 CSV。**图中颜色区分应用／整体，不代表事故等级。**

{table(['整体／应用','2023','2024','2025','2026 截至冻结时间','观察起点 UTC'],[(LABEL[g],*[annual_cell(g,y) for y in [2023,2024,2025,2026]],W['service_windows'][g]['start'][:10]) for g in LABEL])}

星号（*）表示该应用当年仅有部分年度观察期；“—”表示尚未进入观察期，未填为 0% 或 100%。2023 年均从 07-11 开始；Claude Code 的 2025 年从 05-23 开始；Claude for Government、Cowork 的 2026 年分别从 02-18、04-02 开始。2026 年统一截止 09-27 16:10:43 UTC。单个年度数据仅画一个点，不向此前年份延伸。

{figure('02_annual_availability','图 1：年度可用性趋势折线图；整体与六个应用统一采用 F∪P∪D 口径，颜色区分应用，右侧标注最新观察值；缺少观察的年份不连线，纵轴截短至75%')}

**阅读结论的边界：** 2023 年从 7 月 11 日开始，2026 年仅截至 9 月 27 日，均不是全年结果，也未作年化预测。核心服务并集表示“任一纳入产品受影响”；新增产品、公开披露粒度、时间代理和观察期长短都会影响可比性。2026 年结果包含指定模型的主动访问暂停；排除该事件并重算重叠区间后，F∪P∪D 为 **{pct(ex['availability_all'])}**。这些数字是公开事故记录推导的时间估计，不能解释为真实请求成功率或官方 SLA。

来源：[Claude 官方状态站](https://status.claude.com)、[History](https://status.claude.com/history)。本版沿用 v1.0 冻结原始证据和 v1.1 全量语义审阅，按用户要求对无法判断的等级使用官方颜色兜底，重新计算并更新六组图表。

> 920 条记录均已完成复核，其中 916 起事故、4 条维护。原104条unknown中有 **{S["previously_unknown_filled"]}条通过官方等级兜底定级**；现有{ug}条编码为unknown，其中{S["no_impact_records"]}条明确无影响、{unresolved}条缺少可用等级证据。{ut}条没有可纳入主序列的分析时间段。以下数字是公开记录的时间可用性估计，包含明确标记的状态/公告代理；不是请求成功率或官方 SLA。

## 一、2026 年已知影响估计随故障定义而变化

核心服务并集的 **F 口径为 {pct(overall['availability_full'])}，F∪P 为 {pct(overall['availability_full_partial'])}，F∪P∪D 为 {pct(overall['availability_all'])}**。F包含分析确认的完整不可用与官方红色兜底，P包含分析局部不可用与官方橙色兜底，D包含分析退化与官方黄色兜底；Overall 指任一纳入产品发生相应影响。

第一方 API 的三种口径分别为 **{pct(api['availability_full'])} / {pct(api['availability_full_partial'])} / {pct(api['availability_all'])}**。这是 API 产品及其功能的时间指标，不是模型调用成功率，不能按用户或请求量解释。

指定模型的主动访问暂停是重要长事件。将这条记录排除并重新合并重叠区间后，核心服务并集的 F∪P∪D 估计变为 **{pct(ex['availability_all'])}**，相比主序列变化 **{100*(ex['availability_all']-overall['availability_all']):.2f} 个百分点**。两种口径一并展示，不将安全性主动暂停悄悄剔除。

## 二、分析结论优先，无法判断时按官方颜色定级

{table(['等级','判定条件','常见边界'],[
('F','分析证明完整不可用；分析未知时官方红色兜底','官方兜底不证明整个产品完全停机'),
('P','分析证明局部不可用；分析未知时官方橙色兜底','不覆盖已确定的分析等级'),
('D','分析证明性能或质量退化；分析未知时官方黄色兜底','时间证据仍需单独判断'),
('unknown','分析及官方颜色均不能定级，或已确认无影响而单独标记','无影响记录不计时长；缺失不填0')])}

只写“错误率升高”、分析无法判定的阶段，优先采用该产品相应时段的官方组件颜色；没有对应阶段颜色时采用事故级 impact 标签。已经明确的分析等级、服务归属和时间边界保持不变。官方未定级且无可用历史组件颜色时才继续保留未知。

共有 **{S['fallback_records']}条记录、{S['fallback_phase_count']}个阶段** 使用官方兜底，其中{S['previously_unknown_filled']}条原事故等级为unknown，其余是混合等级事故中的未知阶段。官方字段和原分析结论均完整保留；[兜底调整明细](官方颜色兜底调整明细.md) 可逐条查看来源。

[完整事故等级与时间定义](事故等级定义.md) 给出判定标准、未知处理、代理边界和根因定义。

{figure('06_reviewed_grades','图 2：分析优先、官方颜色兜底后的有效等级分布；unknown含3条明确无影响记录')}

## 三、公开历史有 916 起事故，近年公告数量增加

{table(['公告年份 UTC','事故','维护'],[(y,v['incident'],v['maintenance']) for y,v in sorted(counts.items())])}

共 2,919 条更新。最早公告为 2023-03-14，最新公告为 2026-09-22。2026 年未完结，不能直接用 364 起与前一完整年度比较。

{figure('01_same_period_counts','图 3：相同起止月日比较核心服务事故公告数；不同年份服务构成仍有变化')}

History 以三个月为一页，共保存 16 页，末页为早于页面创建日的空季度。920 个 History ID 与 920 个详情对象完全匹配，覆盖状态为 **enumerated**。这是公开可访问 History 的枚举，不证明未公开或删除的事故不存在。列表 API 第二页重复第一页，未用该接口的伪分页证明完整性。

采集证据见 [原始快照](../v1.0/snapshot.json)、[History 枚举轨迹](../v1.0/history-index.json)、[v1.0 原始 HTTP 证据目录说明](../v1.0/README.md)。交叉检查为 History 内嵌数据与详情 ID 对照，未声称浏览器逐页视觉核验。

## 四、观察窗口与重叠去重决定分母和分子

{table(['服务','观察开始 UTC','观察结束 UTC'],[(LABEL[g],v['start'],v['end']) for g,v in W['service_windows'].items()])}

Claude.ai、API 和 Console 采用官方组件 start_date；较新服务采用组件创建后的首个完整 UTC 日，避免向组件出现之前回填“零故障”。这些日期是研究观察窗口，不能理解为产品上线日期。Overall 中每个产品仅在自身窗口内贡献区间；第三方 Vertex/Bedrock 与官网/文档/社交账号分别归 External/Other，排除核心服务。

**A = 1 − 对应等级影响时间的并集秒数 ÷ 观察窗口秒数。** 同事故阶段、产品之间、不同事故之间均去重；跨年分摊；维护排除。F、F∪P、F∪P∪D 分别重新计算，不能将事故小时或产品小时相加。

时间证据顺序为实际影响窗口、历史组件状态区间、有依据的公告活动周期代理。Monitoring 不自动当恢复；晚发复盘不延长影响；重开拆成多个阶段。日期或时区矛盾且无法消解时不编造精确时间。未知等级与无可定位阶段仍保留，**未进入分子的时间不等于已确认正常**。表中 100% 只表示没有可计量的对应等级区间，不表示证实全年零故障。

年度及月度 `incident_count` 按该产品首次已知分析影响时间归属，时间未知则按公告时间；另保留 `publication_count` 对照 History。两种数量不能混用。

## 五、2026 年产品可用性与对应影响小时数

{figure('03_product_availability','图 4：2026 年产品时间可用性估计，纵轴截短以显示差异')}

{table(['服务','观察天数','F 可用性','F∪P 可用性','F∪P∪D 可用性','全部等级小时'],[(LABEL[r['group']],num(r['denominator_seconds']/86400),pct(r['availability_full']),pct(r['availability_full_partial']),pct(r['availability_all']),num(r['all_hours'])) for r in y26])}

{table(['服务','F 小时','F∪P 小时','F∪P∪D 小时','未知等级公告数','无主分析区间公告数'],[(LABEL[r['group']],num(r['full_hours']),num(r['full_partial_hours']),num(r['all_hours']),r['unknown_grade_count'],r['no_assessed_interval_count']) for r in y26])}

Cowork 和 Claude for Government 的观察天数更短。更少的已披露事故或更短的观察历史不能单独证明更可靠。所有图表均附源数据，可在 [年度结果](annual-results.csv) 中复算。

## 六、年度和月度趋势反映已披露影响，而非请求成功率

整体与各应用的年度折线和百分比摘要见报告开头；下表补充各年的观察天数和去重影响小时数。

{figure('05_monthly_availability','图 5：月度估计使用同一逐阶段口径；2026 年 9 月仅至冻结时间')}

{table(['年份','核心服务观察天数','F','F∪P','F∪P∪D','主序列影响小时'],[(r['year'],num(r['denominator_seconds']/86400),pct(r['availability_full']),pct(r['availability_full_partial']),pct(r['availability_all']),num(r['all_hours'])) for r in T['annual'] if r['group']=='Overall'])}

新增产品、披露粒度、未知事故比例和观察期长度都可能改变趋势。不能据此推导某项发布导致可靠性下降，也不能直接与本仓库 OpenAI 报告排名。同期比较见 [matched-window-results.csv](matched-window-results.csv)，月度细表见 [monthly-results.csv](monthly-results.csv)。

## 七、模型暂停和未知等级的敏感性需要并列呈现

{figure('04_sensitivity','图 6：敏感性场景重新合并区间，差异不是简单相减事故时长')}

{table(['2026 核心并集场景','F','F∪P','F∪P∪D','含义'],[(('主序列' if sc=='reviewed' else '排除指定模型暂停' if sc=='exclude_suspension' else '仅明确实际时间' if sc=='explicit_only' else '可定位未知等级均当 F'),pct(r['availability_full']),pct(r['availability_full_partial']),pct(r['availability_all']),('分析等级+官方兜底+标记代理' if sc=='reviewed' else '排除单条主动暂停，重算并集' if sc=='exclude_suspension' else '仅用于衡量时间证据覆盖，不能当真实上界' if sc=='explicit_only' else '保守压力场景，不能当真实下界')) for sc in ['reviewed','exclude_suspension','explicit_only','unknown_as_full'] for r in S['sensitivity_2026'] if r['group']=='Overall' and r['series']==sc])}

暂停事件为 {incident('s9w82lp9dcn9')}，仅指定模型，产品范围为 P。相关官方说明见 [访问暂停说明](https://www.anthropic.com/news/fable-mythos-access) 与 [恢复说明](https://www.anthropic.com/news/redeploying-fable-5)。

2026年剩余未定级事故没有可用于当年核心服务统计的候选区间，因此当前“可定位未知均当F”与主序列相同；这不表示没有缺失影响。“可定位未知均当 F”只改变存在候选时间的未知等级事故；完全无法定位的事件仍无法量化。因此这些场景**不是上下界或置信区间**。间歇错误的公告覆盖时间也不等于连续失败时长。例如 skills 功能间歇错误公告的代理区间约 159.60 小时；单独排除标记为间歇影响包络的三条记录后，2026 核心服务全部等级估计为 **{pct(next(r['availability_all'] for r in S['sensitivity_2026'] if r['group']=='Overall' and r['series']=='exclude_intermittent_envelopes'))}**（仍包含模型暂停）。此场景用于展示连续包络假设的影响，不能证明这些时段正常。详见 [全部敏感性数据](sensitivity-2026.csv)。公开披露样本不是随机抽样，没有依据给出统计误差条；这里报告的是口径敏感性。

## 八、全量复核已完成，证据缺口仍明确保留

{table(['复核和证据项目','结果'],[
('已完成逐记录语义复核','920 / 920；待复核 0；不代表厂商全部真实故障已知'),
('事故等级分布','；'.join(f'{k}: {v}' for k,v in S['grade_counts'].items())),
('无可纳入主序列时间段',f'{ut} / 916；含未知等级、无定位时间、明确无用户影响等'),
('完整实际影响时间线',f"{S['complete_actual_timeline_incidents']} / 916；其余可能仅部分精确或代理"),
('阶段时间来源','；'.join(f'{k}: {v}' for k,v in S['timing_phase_counts'].items())),
('根因审阅','；'.join(f'{k}: {v}' for k,v in S['root_cause_counts'].items())),
('明确无用户影响',f'{len(noimpact)} 条，保留公告但排除时长'),
('结构校验','48 列、UTF-8 BOM、920 唯一 ID、原始 JSON 哈希、引文、正长度、UTC、并集一致性')])}

本次仅调整无法判定的等级，保留 v1.1 已确认分析阶段；官方兜底阶段绑定原始字段、更新ID和组件ID。时间缺失仍缺失；重开、分服务、真实窗口优先和无用户影响排除规则继续生效。红色兜底按F统计，但不能解读为已从正文证明全产品不可用。

原分析的未知结论及兜底来源都有记录级理由，可从 CSV 的 `evidence_json.assessment` 与 HTML 索引检索。额外技术复盘的完整 HTTP 下载在上一轮返回 403，已停止该路径；只保存可读取的摘录，不声称完整复盘正文归档。根因 not_disclosed 仅表示在已取得材料中未明确披露。

可用于公开事故基线、功能风险识别与监测设计。用于生产 SLO 或供应商比较前，还需请求量、模型/地域分布、成功率、延迟分位数、重试后任务完成率和输出质量评测。

## 九、交付物与复算入口

- [单一事故 CSV](incidents.csv)：48 列、完整原始对象与更新、复核判断、证据及时间阶段。
- [全量分析](analysis.json)、[分析区间](assessed-intervals.json)、[窗口配置](service_windows.json)、[年度/月度趋势 JSON](trend_data.json)。
- [CSV 结构验证](incidents.validation.json)、[独立验证](verification.json)、[敏感性结果](sensitivity-2026.csv)。
- [生成和复算说明](README.md)、[分析程序](tools/analyze.py)、[绘图程序](tools/charts.py)、[报告程序](tools/build_report.py)。

CSV SHA-256：`{V['sha256']}`。规范化对象哈希与原始 HTTP 字节哈希分开保存。本版与生成程序、数据和历史版本一并纳入仓库管理。

## 附录：判为 F 的记录仍需按产品和阶段解读

{table(['日期','事故','服务','判断'],[(r['published_at_utc'][:10],incident(r['incident_id']),', '.join(r['service_groups_json']),r['analysis_summary']) for r in full])}
'''
(REPORT_DIR/(STEM+'.md')).write_text(re.sub(r'(!?\[[^\]]*\]\()([^)]+)(\))',lambda m:m[1]+report_link(m[2])+m[3],md))
def inline(s):
 s=html.escape(s);s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s);s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s);s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:f'<a href="{m[2]}">{m[1]}</a>',s);return s
parts=[];nav=[];lines=md.splitlines();k=0
while k<len(lines):
 l=lines[k]
 if l.startswith('| '):
  batch=[]
  while k<len(lines) and lines[k].startswith('| '):batch.append(lines[k]);k+=1
  cells=lambda x:[inline(c.strip()) for c in x.strip('|').split('|')]
  parts.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+x+'</th>' for x in cells(batch[0]))+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+x+'</td>' for x in cells(b))+'</tr>' for b in batch[2:])+'</tbody></table></div>');continue
 if l.startswith('!['):
  m=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',l);svg=(ROOT/m[2]).read_text();svg=svg[svg.find('<svg'):];svg=re.sub(r'id="([^"]+)"',lambda a:'id="'+Path(m[2]).stem+'-'+a[1]+'"',svg);svg=re.sub(r'url\(#([^)]+)\)',lambda a:'url(#'+Path(m[2]).stem+'-'+a[1]+')',svg);parts.append('<figure role="img" aria-label="'+html.escape(m[1],quote=True)+'">'+svg+'</figure>')
 elif l.startswith('## '):
  n=len(nav)+1;nav.append((n,l[3:]));parts.append(f'<h2 id="s{n}">{inline(l[3:])}</h2>')
 elif l.startswith('# '):parts.append('<h1>'+inline(l[2:])+'</h1>')
 elif l.startswith('> '):parts.append('<aside class="callout">'+inline(l[2:])+'</aside>')
 elif l.startswith('- '):parts.append('<p class="bullet">'+inline(l[2:])+'</p>')
 elif l:parts.append('<p>'+inline(l)+'</p>')
 k+=1
css=''
for n in ast.parse((OLD/'tools/build_report.py').read_text()).body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='css':css=ast.literal_eval(n.value)
css+='figure{margin:28px 0;border:1px solid #d8e1d8;border-radius:8px;overflow:hidden}figure svg{display:block;width:100%;height:auto}.intervals{white-space:pre-wrap;font-size:11px;overflow-wrap:anywhere}figure{break-inside:avoid}@media print{figure svg{max-height:16cm}#incident-index,.incident{display:none}}'
records=[]
for r in reversed(R):
 grade=r['assessed_severity'];gs=', '.join(r['service_groups_json']);e=r['evidence_json']['assessment'];updates=''.join('<div class="update"><small>'+html.escape(u['at']+' · '+u['status'])+'</small><p>'+html.escape(u['body']).replace('\n','<br>')+'</p></div>' for u in r['updates_json'])
 ev=''.join('<p><b>'+html.escape(q['kind'])+'</b>：'+html.escape(q['quote'])+'<br><small>'+html.escape(q.get('reason',''))+'</small></p>' for q in r['evidence_json']['items'])
 content='<p>'+html.escape(r['analysis_summary'])+'</p><p>最终等级：<b>'+grade+'</b> · 原分析：'+e.get('semantic_grade',grade)+' · 分级来源：'+r['severity_basis']+' · 官方等级：'+r['official_severity']+' · 服务：'+html.escape(gs)+'</p><p>质量标记：'+html.escape(', '.join(r['quality_flags_json']))+'</p><p>证据：</p>'+ev+'<p>主分析阶段：</p><pre class="intervals">'+html.escape(json.dumps(r['impact_intervals_json'],ensure_ascii=False,indent=2))+'</pre><p>原始对象 SHA-256：<code>'+r['raw_sha256']+'</code></p>'+updates
 records.append(f'<details class="incident" data-year="{r["published_at_utc"][:4]}" data-grade="{grade}" data-search="{html.escape((r["incident_title"]+" "+gs+" "+r["incident_id"]+" "+r["analysis_summary"]).lower(),quote=True)}"><summary><span class="date">{r["published_at_utc"][:10]}</span><span>{html.escape(r["incident_title"])}</span><span class="tag">{r["record_type"]} · {grade} · assessed</span></summary><div class="incident-body"><a href="https://status.claude.com/incidents/{r["incident_id"]}">官方公告 ↗</a>{content}</div></details>')
script="const q=document.querySelector('#q'),y=document.querySelector('#year'),g=document.querySelector('#grade'),items=[...document.querySelectorAll('.incident')];function filter(){let n=0;for(const e of items){const ok=(!y.value||e.dataset.year===y.value)&&(!g.value||e.dataset.grade===g.value)&&e.dataset.search.includes(q.value.toLowerCase());e.hidden=!ok;if(ok)n++}document.querySelector('#shown').textContent=n+' / '+items.length+' 条'}[q,y,g].forEach(e=>e.addEventListener('input',filter));filter();"
out='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Claude 可用性报告 v1.2</title><style>'+css+'</style></head><body><header><span>ANTHROPIC / RELIABILITY RESEARCH · v1.2</span><a href="#incident-index">920 条复核索引</a><button onclick="window.print()">打印报告</button></header><div class="layout"><nav>'+''.join(f'<a href="#s{i}">{html.escape(title)}</a>' for i,title in nav)+'<a href="#incident-index">交互事故索引</a></nav><main>'+''.join(parts)+'<h2 id="incident-index">完整复核索引</h2><p>可离线搜索标题、服务、ID 和判断理由；展开查看依据、阶段及完整原文。assessed 表示审阅完成，unknown 表示没有有效故障等级（含明确无影响记录），具体原因见标记。</p><div class="controls"><input id="q" type="search" placeholder="搜索标题、服务、ID 或复核理由" aria-label="搜索事故"><select id="year" aria-label="年份"><option value="">全部年份</option>'+''.join(f'<option>{y}</option>' for y in [2023,2024,2025,2026])+'</select><select id="grade" aria-label="等级"><option value="">全部等级</option>'+''.join(f'<option>{g}</option>' for g in ['full_outage','partial_outage','degraded_performance','unknown'])+'</select><span id="shown"></span></div>'+''.join(records)+'</main></div><script>'+script+'</script></body></html>'
out=re.sub(r'href="([^"]+)"',lambda m:'href="'+html.escape(report_link(html.unescape(m[1])),quote=True)+'"',out)
(REPORT_DIR/(STEM+'.html')).write_text(out)
(ROOT/'README.md').write_text('''# Anthropic / Claude v1.2

打开 [Anthropic 根目录主报告](../../Anthropic_Claude_Availability_Report_2026-09-27_v1.2.html)。开篇含整体及六个应用的年度汇总表和同图趋势折线；采用分析优先、官方颜色兜底。已内嵌全部图表和920条审阅索引，可离线浏览。主交付为48列UTF-8 BOM的 incidents.csv。

冻结快照和原始证据位于同级 `../v1.0/`，v1.2不修改它。../v1.1/reviews/ 保留三个互不重叠时间片的全文语义审阅记录；tools/analyze.py 合并并绑定原始对象hash。分析无法判断时采用官方颜色兜底，仍无等级或时间的数据不填0，时间代理不冒充真实停机。完整口径见事故等级定义.md。

复算：在仓库根运行 `python3 Anthropic/2026-09-27/v1.2/tools/analyze.py`，再运行 tools/fallback_list.py 生成调整明细，随后用已有含 reportlab 和 pypdfium2 的 Python 运行 tools/charts.py，再运行 tools/build_report.py 和 tools/verify.py。全部无网络，重新生成本版本派生物，不改变v1.0。绘图实际环境为内置Python3.12、ReportLab4.4.9及PDFium；无额外安装。

本机绘图命令：

```
/Users/nanasmac/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 Anthropic/2026-09-27/v1.2/tools/charts.py
```

figures/ 每图含SVG/PNG/PDF和源数据CSV。trend_data.json主序列只来自incidents.csv的impact_intervals_json；assessed-intervals.json的unknown_intervals只用于敏感性场景。本版主报告位于 Anthropic 根目录，历史版本保留在各自目录。
''')
print(REPORT_DIR/(STEM+'.html'))
