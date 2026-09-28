"""Build a root-cause evidence supplement without changing frozen incident classifications."""
import csv,json,hashlib,collections,re,html
from pathlib import Path
ROOT=Path(__file__).resolve().parent
V=ROOT.parent
SOURCE=V/'incidents.csv'
ROWS=list(csv.DictReader(SOURCE.open(encoding='utf-8-sig')))
INC=[r for r in ROWS if r['record_type']=='incident']
BY={r['incident_id']:r for r in INC}
T=json.loads((V/'trend_data.json').read_text())
LABEL={'Overall':'整体（任一核心应用受影响）','Claude.ai':'Claude.ai','API':'第一方 API','Console':'Console','Claude Code':'Claude Code','Cowork':'Cowork','Government':'Claude for Government（政府版）'}
# Explicitly reviewed classification. Themes are not claims about deepest technical causes.
# M = mechanism/direct failure mode; T = trigger/bug; L = domain only; R = recovery action only.
review_lines='''3667134hg62q|变更与配置|M|负载均衡配置错误；回滚恢复。配置为何未被验证未披露。|发布与配置安全
0qyp857kns2b|变更与配置|T|维护操作使集群部分不可用；维护步骤及防护失效未披露。|发布与配置安全
vyw1vz0h6c1x|数据与协议完整性|T|图像处理缺陷导致图片被裁为正方形；代码机制未披露。|数据与协议完整性
qn4crqd8ym36|基础设施与依赖|L|仅披露后端服务临时中断，不能进一步归因为容量或网络。|依赖隔离与恢复
q5dvt5ph7tzx|基础设施与依赖|L|上游基础设施问题；未说明底层机制，曾切换模型缓解。|依赖隔离与恢复
kygj9sjs8dxr|推理与输出质量|T|官方确认回复一致性缺陷，并明确无提示泄漏；更深机制未知。|语义质量可靠性
7gftd1ybnk3v|基础设施与依赖|L|指定模型的基础设施问题；不能推断硬件或GPU原因。|依赖隔离与恢复
926d2gm87s8c|数据与协议完整性|L|来源送达模型却未持久化到聊天，定位到数据链路但写入失败原因未知。|数据与协议完整性
kn7mvrgb0c8m|基础设施与依赖|L|明确依赖GCP及关联服务故障；本记录未给出供应商底层机制。|依赖隔离与恢复
4q9qw2g0nlcb|推理与输出质量|T|推理栈发布导致质量退化，回滚；不套用其他月份复盘的编译器原因。|语义质量可靠性
zr0lqy5rpx9w|客户端与软件兼容|T|确认回归缺陷，未披露具体变更或代码。|客户端状态与兼容
34c8pmy9lb6b|数据与协议完整性|M|部分MCP连接无法降级至SSE；协议回退为何失败仍未知。|数据与协议完整性
h26lykctfnsz|推理与输出质量|M|公告确认推理栈发布；关联官方复盘进一步说明TPU运行时配置与优化导致输出异常。|语义质量可靠性
72f99lh1cj2c|推理与输出质量|M|关联复盘披露上下文路由错误及近似top-k编译问题；同一公告涉及多机制，不按一因一事故计。|语义质量可靠性
 gr1vrcvz9jd4|基础设施与依赖|L|上游错误暴露内部基础设施问题并拖慢恢复；双方具体机制未披露。|依赖隔离与恢复
m05thlr411w6|客户端与软件兼容|T|确认客户端代码问题，未披露触发路径。|客户端状态与兼容
kfs1w8vywj9d|变更与配置|T|错误边缘代理部署触发故障，回滚后仍在调查深层原因。|发布与配置安全
p0svq4j6sk04|基础设施与依赖|L|只确认第三方供应商故障，未给出供应商名称与技术机制。|依赖隔离与恢复
49cmvxrrk228|基础设施与依赖|R|仅说明上游已实施修复；可确认恢复动作，不能据此认定技术根因。|依赖隔离与恢复
6rrnsb1y0kbn|订阅与权益控制|T|iOS指定版本引入购买激活缺陷；新购修复后，存量权益仍需修复。|订阅与权益一致性
9s03yn69ky6m|基础设施与依赖|L|内部数据服务影响报表及分析接口；具体数据故障机制未披露。|依赖隔离与恢复
3kjy2zn2w2bj|客户端与软件兼容|M|Windows配置文件并发写争用，产生非确定性损坏；已知关联客户端版本。|客户端状态与兼容
htjkfrfnzq12|基础设施与依赖|L|上游对等互联点网络退化导致连接超时；链路退化原因未披露。|依赖隔离与恢复
pqpgkf52p3tg|客户端与软件兼容|M|夏令时跳过小时使任务时间解析无法收敛，应用进入无限循环。|客户端状态与兼容
z5scppyhphjk|数据与协议完整性|M|连接器被从组织允许列表移除导致不可用；移除的深层原因未披露。|数据与协议完整性
zqsk02ryfmrd|客户端与软件兼容|T|指定客户端版本恢复旧会话时崩溃；底层代码缺陷未披露。|客户端状态与兼容
snxm62gpxfc9|变更与配置|M|基础设施变更改变GitHub连接出口IP，与客户IP允许列表不兼容。|发布与配置安全
 g613ntyj2pwf|订阅与权益控制|M|错误要求使用量额度，使本应可用的模型访问被拒绝。|订阅与权益一致性
kmbpgrsszf72|证书与状态通信|M|状态站点证书无效；不能进一步断言是到期或自动续期失败。|可观测性与事故通信
vr9tpk8w7zr8|基础设施与依赖|L|上游云服务问题造成远程会话失败或断开，具体机制未披露。|依赖隔离与恢复
r1pqn1kb4hvk|客户端与软件兼容|M|Windows更新使Cowork工作区失去本机磁盘访问，涉及外部系统兼容。|客户端状态与兼容
 t8fpw9vcshl9|基础设施与依赖|L|Google Play确认服务问题，影响订阅；未披露技术机制。|订阅与权益一致性'''
reviews={}
for line in review_lines.splitlines():
 i,theme,level,assessment,direction=line.strip().split('|')
 reviews[i]={'theme':theme,'evidence_level':level,'assessment':assessment,'engineering_direction':direction}
assert set(reviews)=={r['incident_id'] for r in INC if r['root_cause_status']=='vendor_stated'}
LEVEL={'M':'机制或直接失效方式','T':'触发变更或缺陷类型','L':'故障域／依赖定位','R':'仅恢复动作','U':'现有材料未披露原因','N':'明确无用户影响','S':'主动服务暂停'}
POST='https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues'
extras={'h26lykctfnsz':'TPU运行时配置与优化导致异常token输出；公告包含该官方复盘链接。','72f99lh1cj2c':'短上下文误路由至长上下文服务池；另有近似top-k编译缺陷。Haiku已确认，部分其他模型的关联仍有不确定性。'}
# New external notes are paraphrases; no claim to archive original HTTP bytes.
notes={'review_date':'2026-09-28','incident_cutoff_utc':'2026-09-27T16:10:43Z','method':'Reuse prior per-record semantic review, recheck all 32 existing attributions against saved updates, and screen all 916 incident update texts for additional causal statements. Screening is not independent full-text re-review. Read linked official postmortem as supplemental evidence.','sources':[{'url':POST,'published_date':'2025-09-17','retrieved_date':'2026-09-28','access':'Web reader returned article text; original HTTP bytes not archived','scope':'Linked explicitly by h26lykctfnsz and 72f99lh1cj2c; does not apply to all model-quality incidents','notes':list(extras.values())},{'url':'https://sre.google/workbook/canarying-releases/','scope':'Engineering reference for representative canary evaluation; not evidence about Anthropic internal controls.'},{'url':'https://docs.aws.amazon.com/wellarchitected/2022-03-31/framework/rel_mitigate_interaction_failure_limit_retries.html','scope':'Engineering reference for bounded retry/backoff/jitter; not an incident cause.'}], 'unchanged':['incidents.csv','analysis.json','assessed-intervals.json','trend_data.json']}
(ROOT/'source-notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n')
(ROOT/'review-decisions.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2)+'\n')
# Reproducible lead screening; semantic decisions remain explicit above.
pattern=re.compile(r'root cause|caused by|due to|because|regression|misconfig|roll.?back|revert|capacity|overload|memory leak|race condition|deployment|deploying|bug|certificate|DNS|provider|infrastructure|corrupt',re.I)
candidates=[]
for r in INC:
 if r['root_cause_status']=='vendor_stated':continue
 hits=[]
 for u in json.loads(r['updates_json']):
  for sentence in re.split(r'(?<=[.!?])\s+|\n+',u['body']):
   if pattern.search(sentence) and sentence not in [h['quote'] for h in hits]:hits.append({'update_id':u['id'],'quote':sentence})
 if hits:
  reason={'x0465yqg246w':'手机验证及问卷流程问题仅为故障链，后续更新还修正了购买受影响范围，不能从首条公告推断技术根因。','5g213mxxlbsw':'529 overloaded是响应现象，未说明资源瓶颈或触发原因。','s9w82lp9dcn9':'主动暂停记录，按特殊事件单列；不能从复盘链接名称推断技术原因。'}.get(r['incident_id'],'现有候选文字只有根因调查/修复过程或未展开的现象，未增加具体归因。')
  candidates.append({'incident_id':r['incident_id'],'source_record_sha256':r['raw_sha256'],'matched_statements':hits,'review_decision':reason})
assert len(candidates)==29
(ROOT/'screened-candidates.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2)+'\n')
ledger=[]
for r in INC:
 i=r['incident_id'];e=json.loads(r['evidence_json']);ev=[x for x in e['items'] if x.get('kind')=='root_cause']
 d=reviews.get(i,{'theme':'未知','evidence_level':'U','assessment':'沿用已完成的逐条语义复核；在已取得材料中未披露可判定原因。故障现象、修复完成或“已找到根因”不等于披露根因。','engineering_direction':'补充因果证据与事故复盘'})
 if 'no_user_impact' in json.loads(r['quality_flags_json']):d={'theme':'非故障影响','evidence_level':'N','assessment':'官方确认无用户影响，单列，不作为技术故障根因样本。','engineering_direction':'告警准确性与影响确认'}
 if i=='s9w82lp9dcn9':d={'theme':'主动暂停','evidence_level':'S','assessment':'官方公告主动暂停模型访问；不能归因为GPU、容量或基础设施故障。本次未扩展核验其政策原因。','engineering_direction':'服务连续性与替代路径'}
 updates={u['id']:u['body'] for u in json.loads(r['updates_json'])}
 for x in ev:assert x['quote'] in updates[x['update_id']]
 if i in extras:assert any('a-postmortem-of-three-recent-issues' in body for body in updates.values())
 ledger.append({'incident_id':i,'published_at_utc':r['published_at_utc'],'incident_title':r['incident_title'],'service_groups_json':r['service_groups_json'],'assessed_severity':r['assessed_severity'],'prior_root_cause_status':r['root_cause_status'],'prior_root_cause':r['root_cause'],'cause_evidence_level':d['evidence_level'],'cause_evidence_label':LEVEL[d['evidence_level']],'cause_theme':d['theme'],'root_cause_assessment':d['assessment'],'engineering_direction':d['engineering_direction'],'evidence_json':json.dumps(ev,ensure_ascii=False),'supplementary_evidence':extras.get(i,''),'supplementary_source_url':POST if i in extras else '', 'source_url':'https://status.claude.com/incidents/'+i,'source_record_sha256':r['raw_sha256']})
with (ROOT/'incident-root-causes.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(ledger[0]));w.writeheader();w.writerows(ledger)
count=collections.Counter(r['cause_evidence_level'] for r in ledger);themes=collections.Counter(d['theme'] for d in reviews.values())
summary={'incidents':len(ledger),'excluded_maintenance':len(ROWS)-len(INC),'previous_vendor_stated':len(reviews),'evidence_levels':dict(count),'prior_attribution_themes':dict(themes),'note':'Themes describe the 32 previously attributed records including one recovery-only record, not population-wide root-cause proportions. No impact-time attribution or availability recalculation.','source_csv_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()}
(ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
def table(head,rows):return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+['| '+' | '.join(str(x).replace('|','／').replace('\n',' ') for x in row)+' |' for row in rows])
def link(i):return f"[{BY[i]['published_at_utc'][:10]} · {BY[i]['incident_title']}](https://status.claude.com/incidents/{i})"
# Recommendations are analysis, distinct from vendor descriptions.
directions=[
('P0','可观测性与事故通信','kmbpgrsszf72','将HTTP成功、首token/完成时延、工具调用和最终任务完成率分开；关联模型、路由池、发布版本、硬件、客户端版本；状态页独立探测证书和可达性。','建立可追踪请求样本和隐私保护反馈通道，记录检测/恢复时间。','演练业务失败但HTTP 200、状态页证书失效；核查任务SLI和告警是否触发。'),
('P0','发布与配置安全','3667134hg62q,snxm62gpxfc9,kfs1w8vywj9d','代码、模型、代理、路由和配置均纳入渐进发布；按真实租户/地域/客户端选金丝雀，配置检查覆盖出口IP及客户允许列表契约；保留回退版本。','发布绑定错误率、质量和任务成功门槛；定义自动停止与可验证回滚。','错误配置注入与回滚演练；测量坏版本暴露范围、检测时间、回退完成时间。'),
('P0','语义质量可靠性','4q9qw2g0nlcb,h26lykctfnsz,72f99lh1cj2c','把“成功响应但质量错误”作为失败类别；使用工具调用结构校验、长短上下文、多轮会话与硬件/精度/批次矩阵差分评估。','在真实服务路径持续运行合成质量探针；将路由与推理版本关联到异常样本。','验证已知异常用例能阻断变更，统计质量回归漏检及误报；不要求随机生成逐字一致。'),
('P1','依赖隔离与恢复','q5dvt5ph7tzx,kn7mvrgb0c8m,gr1vrcvz9jd4,vr9tpk8w7zr8','按故障域隔离连接池、配额和任务队列；超时预算、单层有界重试与抖动；验证备用路径不共享同一依赖。','对工具副作用使用幂等键与结果对账；长任务检查点恢复，明确重试和切换条件。','注入依赖超时/断连，测量重试放大、恢复后积压排空、重复副作用和任务恢复率。'),
('P1','客户端状态与兼容','3kjy2zn2w2bj,pqpgkf52p3tg,zqsk02ryfmrd,r1pqn1kb4hvk','配置使用原子写与并发协调；会话格式迁移可回退；调度明确夏令时缺失/重复小时语义；测试OS升级及沙箱文件访问。','建立Windows/macOS、旧会话、并发进程、时区和系统更新兼容矩阵。','故障注入验证写入中断不损坏配置、调度有界终止、旧会话恢复和工作区访问正确。'),
('P1','数据与协议完整性','vyw1vz0h6c1x,926d2gm87s8c,34c8pmy9lb6b,z5scppyhphjk','为图片尺寸、引用持久化、MCP协议协商和连接器允许列表建立端到端不变量；区分模型拿到数据与用户最终看到数据。','加入写后读核验、协议能力矩阵及配置差异审计。','验证引用保留率、图片变换正确性、协议回退成功率、允许列表误删恢复。'),
('P1','订阅与权益一致性','6rrnsb1y0kbn,g613ntyj2pwf,t8fpw9vcshl9','交易与权益分离状态机但可对账；处理重复/乱序/延迟支付事件；按既定授权规则处理供应商故障。','覆盖免费/付费/已购用户合成旅程；修复新交易和补偿存量权益分别验证。','测量付款到权益生效时延、错误拒绝访问率、存量漏补数量；不以放宽认证代替恢复。'),
('P2','容量与服务连续性','5g213mxxlbsw,s9w82lp9dcn9','529只能证明过载响应现象，不能证明GPU不足；先采集队列等待、并发、token吞吐和请求长度，再评估准入、背压及容量余量。主动模型暂停另作业务连续性场景。','压测混合长短请求并设计明确授权的替代模型/异步处理路径；不绕过主动暂停。','测量饱和拐点、重试放大和降级后的任务质量；生产目标依据业务SLO与基线确定。')]
tech_table=table(['优先级','技术方向','直接事故证据','建议能力与实现','验收观测'],[(p,d,'；'.join(link(i) for i in ids.split(',')),cap+' '+deliver,measure) for p,d,ids,cap,deliver,measure in directions])
annual={(r['group'],r['year']):r for r in T['annual']}
def cell(g,y):
 r=annual.get((g,y))
 if not r:return '—'
 return f"{100*r['availability_all']:.4f}%"+(' *' if r['window_start']!=f'{y}-01-01T00:00:00Z' or r['window_end']!=f'{y+1}-01-01T00:00:00Z' else '')
annual_table=table(['整体／应用','2023','2024','2025','2026 至冻结时间'],[(LABEL[g],*[cell(g,y) for y in [2023,2024,2025,2026]]) for g in LABEL])
md=f'''# Claude 事故根因与可靠性工程方向

复核日期：2026-09-28。事故与可用性数据仍冻结于 2026-09-27 16:10:43 UTC；范围为现有 Claude 报告的916起事故，4条维护排除。本次补充根因证据，不重算历史可用性。

## 开篇可用性摘要

以下统一采用 F∪P∪D。整体为任一纳入应用的影响区间并集，不是应用平均值。2026年整体为79.8238%；各应用差异与观察期如下。它们是公开事故时间估计，不是请求成功率或官方SLA。

{annual_table}

星号表示部分年度。2023从07-11开始；Claude Code的2025从05-23开始；Government和Cowork的2026分别从02-18、04-02开始；2026截止09-27 16:10:43 UTC。缺失年份不补零、不连线。新增产品与时间代理影响可比性；排除指定模型主动暂停后2026整体为86.4682%，该场景不替代主序列。

![整体与应用年度趋势](../figures/02_annual_availability.svg)

[年度图表源数据](../figures/02_annual_availability.csv) · [完整主报告](../../../Anthropic_Claude_Availability_Report_2026-09-27_v1.2.html)

## 根因分析结论

**不能把大多数事故的“错误率上升”归因为容量不足，也不能把“已找到根因”当作已公开根因。** 原报告32条vendor_stated占916起的{32/916*100:.2f}%，但这个字段混合了技术机制、触发因素、故障域和恢复动作；它不是32份完整RCA。本次将证据深度拆开，保留原字段以便审计。

{table(['证据层级','事故数','解释'],[(LEVEL[k],count[k],desc) for k,desc in [('M','说明机制或直接失效方式，仍不等于追溯到组织和流程根因'),('T','确认发布、回归或缺陷，但底层实现原因未披露'),('L','只定位到依赖、服务或数据环节'),('R','上游实施修复；不能当作根因证明'),('U','现有证据无法定因'),('N','确认无用户影响，单列排除故障推论'),('S','主动暂停，单列业务连续性场景')]])}

总体最有依据的技术方向是：**发布与配置安全、语义质量可靠性、依赖隔离与任务恢复、客户端状态/兼容、数据与协议完整性、订阅权益一致性，以及贯穿各方向的可观测性。** 优先级是本研究基于影响范围、复现机制和控制能力提出的工程判断，不能从少量披露样本推出厂商全部故障的根因比例。

## 样本与归因边界

复用已完成的916起事故逐条语义复核；本次逐项核对32条已有归因的原始更新，并对全部916起更新文本做因果线索筛查，复查[29条候选记录](screened-candidates.json)。关键词筛查用于发现线索，不声称是独立的全量逐字复审。大多数候选只包含模板化“正在找根因”“部署修复”等文字；未据此补造新原因。手机验证及529记录只有故障链条/响应现象，不能升级为技术根因。

原始CSV保持不变；[916起逐事故根因台账](incident-root-causes.csv)为补充视图，每行保留原根因字段、证据深度、分类、原文引用、update_id、官方URL和原始对象SHA-256。维护不进入台账，3条明确无影响和1条主动暂停单列。unknown表示当前材料证据不足，不声称厂商从未发布过其他材料。

## 公开归因主题

{table(['主题','已有归因记录数'],themes.most_common())}

分母仅为32条原vendor_stated记录，含1条本次降为“仅恢复动作”的记录；各记录只取一个主主题，多个触发因素在逐条解释中保留。主题计数不等于唯一底层故障数，也不等于总停机贡献；不同公告可能描述同一底层问题。未将各原因时长相加或计算“根因占停机百分比”。

## 代表性故障链及设计启示

- **变更可同时破坏网络和客户契约。** {link('3667134hg62q')}明确由负载均衡配置错误触发；{link('snxm62gpxfc9')}由出口IP变化撞上客户允许列表。工程启示是配置也要灰度和回滚，并将外部契约纳入发布验证。
- **HTTP成功不代表模型正确。** {link('4q9qw2g0nlcb')}将质量和工具调用问题归因于推理栈发布。7月事件不能直接套用8月复盘的编译器原因。工程上需要任务质量与协议正确性门槛。
- **补充官方复盘。** 2025-09-17的[技术复盘]({POST})解释三类问题：上下文路由到错误服务池、TPU运行时配置导致输出异常、近似top-k编译缺陷。它明确部分模型关联仍不确定。只将补充归因关联到公告中直接链接该复盘的两条记录，原分析区间和事故数量保持不变。
- **故障恢复链也会失败。** {link('gr1vrcvz9jd4')}称上游错误暴露内部问题并延长恢复；{link('vr9tpk8w7zr8')}涉及长任务会话断开。应验证依赖隔离、任务检查点和恢复后的积压处理，而非只验证正常调用。
- **客户端包含持久状态和日历边界。** {link('3kjy2zn2w2bj')}披露配置并发写争用；{link('pqpgkf52p3tg')}披露夏令时解析无限循环。对应的是原子写、并发协调和有界时间解析，不是泛泛增加服务器。
- **交易完成与权益生效是两步。** {link('6rrnsb1y0kbn')}新购买路径修好后仍需补偿既有用户。需区分前向修复与存量恢复，并验证对账闭环。

## 可靠性工程技术方向与验收

下表的方案是研究建议，不代表已知Anthropic缺少这些控制，也不是已经实施的改进。先建立业务SLO与基线，再定阈值；不从公开状态页反推内部容量、团队流程或具体架构。

{tech_table}

发布灰度的代表性选择与对照评价可参考[Google SRE发布工程](https://sre.google/workbook/canarying-releases/)。重试应受次数和时间预算约束，并采用退避与抖动，可参考[AWS重试控制](https://docs.aws.amazon.com/wellarchitected/2022-03-31/framework/rel_mitigate_interaction_failure_limit_retries.html)。这些工程资料用于支撑设计方向，不作为Claude事故归因证据。

## 建议推进顺序

第一阶段建立任务SLI、请求到发布版本的关联、证据分层和复盘模板，同时验证配置回滚与真实路径质量探针。第二阶段围绕已出现的具体机制建设兼容矩阵、协议契约、权益对账与依赖恢复演练。第三阶段根据运行基线决定容量投入、备用模型或供应商路径，并定期复测故障注入与恢复质量。该顺序是建议，不是交付工期承诺。

应收集的新增证据包括：事故触发版本、变更ID、检测渠道、真实影响范围、恢复动作及其结果、复发原因和控制缺口。没有这些数据时，不能量化改进后可用性提升，也不能给出可信的容量或投资回报预测。

## 32条已有归因记录的逐项复核

{table(['事故','主主题','证据深度','复核结论'],[(link(i),reviews[i]['theme'],LEVEL[reviews[i]['evidence_level']],reviews[i]['assessment']) for i in reviews])}

## 复算与验证

[完整逐事故台账](incident-root-causes.csv) · [人工判断映射](review-decisions.json) · [统计结果](summary.json) · [新增来源与范围说明](source-notes.json) · [验证记录](verification.json) · [生成程序](build.py)。源CSV SHA-256：`{summary['source_csv_sha256']}`。
'''
(ROOT/'Claude_事故根因与可靠性工程方向.md').write_text(md)
# Small standalone reader: full table, shared annual SVG, no external JS or fonts.
def inline(s):
 s=html.escape(s);s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s);s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
 return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:f'<a href="{m[2]}">{m[1]}</a>',s)
lines=md.splitlines();parts=[];i=0
while i<len(lines):
 l=lines[i]
 if l.startswith('| '):
  batch=[]
  while i<len(lines) and lines[i].startswith('| '):batch.append(lines[i]);i+=1
  cells=lambda x:[inline(c.strip()) for c in x.strip('|').split('|')]
  parts.append('<div class="table"><table><thead><tr>'+''.join('<th>'+c+'</th>' for c in cells(batch[0]))+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+c+'</td>' for c in cells(row))+'</tr>' for row in batch[2:])+'</tbody></table></div>');continue
 if l.startswith('!['):
  m=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',l);svg=(ROOT/m[2]).read_text();parts.append('<figure aria-label="'+html.escape(m[1])+'">'+svg[svg.index('<svg'):]+'</figure>')
 elif l.startswith('## '):parts.append('<h2>'+inline(l[3:])+'</h2>')
 elif l.startswith('# '):parts.append('<h1>'+inline(l[2:])+'</h1>')
 elif l:parts.append('<p>'+inline(l[2:] if l.startswith('- ') else l)+'</p>')
 i+=1
css='body{max-width:1180px;margin:40px auto;padding:0 28px;font:16px/1.8 system-ui,sans-serif;color:#21382e;background:#fafbf9}h1,h2{color:#134e4a}h2{margin-top:48px}a{color:#25638a}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:10px 12px;border:1px solid #d5ded7;text-align:left;vertical-align:top}th{background:#e7eee8}.table{overflow-x:auto}figure{margin:24px 0}svg{width:100%;height:auto}code{overflow-wrap:anywhere}@media print{body{max-width:none}tr,figure{break-inside:avoid}}'
(ROOT/'Claude_事故根因与可靠性工程方向.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Claude事故根因与可靠性工程方向</title><style>'+css+'</style><body>'+''.join(parts)+'</body></html>')
# Snippet inserted into the main report by its own builder, whose links are relative to V.
snippet=f'''## 九、事故根因与可靠性工程方向（2026-09-28补充复核）

916起事故中，原32条vendor_stated仅占{32/916*100:.2f}%，且并非都有完整技术根因。本次区分：{count['M']}条机制或直接失效方式、{count['T']}条触发变更/缺陷、{count['L']}条故障域定位、{count['R']}条仅恢复动作；另有{count['U']}条现有材料未披露原因、{count['N']}条明确无影响、{count['S']}条主动暂停。证据不足时不推断为GPU、容量或网络故障。

优先方向为发布与配置安全、语义质量可靠性和可观测性；随后完善依赖隔离与任务恢复、客户端兼容、数据/协议完整性、订阅权益一致性。方向与验收指标基于有明确证据的案例推导，属于研究建议，不是厂商内部控制缺失的事实。

{table(['方向','对应事故机制或现象','建议验证重点'],[(d, '；'.join(link(i) for i in ids.split(',')[:2]),measure) for _,d,ids,_,_,measure in directions])}

详细的证据分层、32条归因逐项复核及工程方案见 [根因与可靠性工程专题](root-cause-review/Claude_事故根因与可靠性工程方向.html)（[Markdown](root-cause-review/Claude_事故根因与可靠性工程方向.md)）；[916起逐事故根因台账](root-cause-review/incident-root-causes.csv)保留每起的原字段、证据及判断。本次补充读取两条事故直接关联的官方技术复盘；不改变冻结事故数据、等级、时间区间和可用性数值。
'''
(ROOT/'main-report-section.md').write_text(snippet)
# Cross-check source invariants, full ledger coverage, quote integrity, report links and totals.
assert len(INC)==len(ledger)==len({r['incident_id'] for r in ledger})==916
assert sum(count.values())==916 and sum(themes.values())==32
assert count['N']==3 and count['S']==1
check=list(csv.DictReader((ROOT/'incident-root-causes.csv').open(encoding='utf-8-sig')))
assert len(check)==916 and all(x['source_record_sha256']==BY[x['incident_id']]['raw_sha256'] for x in check)
for path in [ROOT/'Claude_事故根因与可靠性工程方向.md']:
 for url in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text()):
  if '://' not in url and url!='verification.json':assert (path.parent/url).is_file(),url
result={'validation':'passed','incident_rows':916,'excluded_maintenance':4,'original_attributions_reviewed':32,'supplementary_postmortem_linked_incidents':2,'evidence_level_total':sum(count.values()),'original_source_csv_sha256':summary['source_csv_sha256'],'original_csv_unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==summary['source_csv_sha256'],'evidence_quotes_checked':sum(len(json.loads(r['evidence_json'])) for r in ledger),'local_links':'passed','limitations':['Not an independent fresh full-text review of all 916 incidents; reuses prior semantic review and screens for causal statements.','Public evidence does not support a complete root-cause distribution or causal allocation of downtime.']}
(ROOT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
