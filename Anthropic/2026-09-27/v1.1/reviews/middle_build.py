# -*- coding: utf-8 -*-
"""Encode manual review AFTER reading all full docket records 307..613.
No keyword grading. Sets below are explicit reviewer decisions; helpers only bind
quotes, normalize known component names and encode individually checked times.
"""
import json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parent
A=json.loads((ROOT.parent.parent/'v1.0/review-docket.json').read_text())
P='partial_outage';D='degraded_performance';F='full_outage';U='unknown'
unknown={323,325,331,335,348,355,357,365,377,397,419,423,449,456,468,478,479,482,489,494,507,516,517,521,523,526,529,536,563,567,570,572,587,592,594,595,604}
degraded={320,378,405,413,426,435,451,464,465,505,510,528,535,548,551,558,559,561,576,580,581,586,613}
full={343,374,467,496,539,540}
# All remaining assigned records were individually read and have a named model,
# feature, client or user subset with failed requests/access; product severity P.
assert not(unknown&degraded or unknown&full or degraded&full)
NAMES={'claude.ai':'Claude.ai','Claude Console (platform.claude.com)':'Console','Claude API (api.anthropic.com)':'API','Claude Code':'Claude Code'}
R={}
for n in range(307,614):
 r=A[n];grade=U if n in unknown else D if n in degraded else F if n in full else P
 summary={P:'公告将失败范围限定于所列模型、功能、客户端或用户子集；按产品整体范围评为部分不可用。',D:'公告描述性能、输出质量、显示或数据完整性退化，按退化评估。',F:'公告明确产品服务不可访问；全量不可用仅限所列服务和有证据的阶段。',U:'已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。'}[grade]
 R[n]={'n':n,'incident_id':r['id'],'grade':grade,'groups':[NAMES[x] for x in r['components'] if x in NAMES] or ['Unmapped'],'summary':r['title']+'：'+summary,'evidence':[{'quote':r['title'],'update_id':None,'kind':'severity','reason':summary}], 'time_mode':'component_or_proxy','time_note':'未给完整真实起止；历史组件变更或公告生命周期只作为已标记代理，保留各服务恢复和复发阶段。','time_complete':False,'root_cause_status':'not_disclosed','root_cause':'','flags':[]}
def note(n,summary,groups=None):
 R[n]['summary']=summary
 R[n]['evidence'][0]['reason']=summary
 if groups is not None:R[n]['groups']=groups

def ev(n,q,kind='severity',reason='支持本条复核判断。'):
 matches=[u for u in A[n]['updates'] if q in u['body']]
 assert matches,(n,q)
 R[n]['evidence'].append({'quote':q,'update_id':matches[0]['id'],'kind':kind,'reason':reason})
def cause(n,q,text):
 R[n]['root_cause_status']='vendor_stated';R[n]['root_cause']=text;ev(n,q,'root_cause','供应商正文明确说明原因；不外推根因细节。')
def none(n,why,flag='actual_time_unpositioned'):
 R[n]['time_mode']='none';R[n]['time_note']=why;R[n]['flags'].append(flag)
def phase(n,start,end,severity=None,groups=None,basis='explicit_impact'):
 return {'start_at':start,'end_at':end,'severity':severity or R[n]['grade'],'service_groups':groups or R[n]['groups'],'time_basis':basis}
def times(n,pairs,complete=True,basis='explicit_impact',note_text=None):
 R[n]['time_mode']='explicit';R[n]['intervals']=[phase(n,a,b,basis=basis) for a,b in pairs];R[n]['time_complete']=complete
 R[n]['time_note']=note_text or ('正文明确实际起止时间，日期按公告上下文定位；UTC 时间优先。' if complete else '实际时间与公告代理混合；未声称完整真实停机窗口。')
 # Bind full relevant time-bearing updates selected by reviewer calls below, not automatic grade inference.
def daily(n,start,end,complete=True,basis='explicit_impact'):
 day=A[n]['date'][:10];times(n,[(day+'T'+start+'Z',day+'T'+end+'Z')],complete,basis)
def mixed(n,start=None,end=None):
 us=sorted(A[n]['updates'],key=lambda u:u['display_at']);day=A[n]['date'][:10]
 a=day+'T'+start+'Z' if start else us[0]['display_at'];b=day+'T'+end+'Z' if end else us[-1]['display_at']
 times(n,[(a,b)],False,'announcement_proxy','至少一端为正文实际时间，另一端为公告代理；不计作精确真实窗口。')
# Evidence refinements and service attribution after full reading.
note(308,'首次公告泛称所有模型，恢复说明修订为部分模型（包括 Sonnet 3.7）；按最终有边界说明评产品 P。');ev(308,'on requests to some models');R[308]['flags'].append('scope_revised_in_updates')
note(309,'免费用户使用 Sonnet 3.7 报错，Pro/Max 明确未受影响。',['Claude.ai']);ev(309,'Users of the Pro and Max plans have been unaffected.');mixed(309,'12:30:00');ev(309,'Since 12:30 UTC','time')
note(310,'企业 SSO 登录失败，限定认证路径；组件全程 operational 与正文冲突，采用公告代理。');ev(310,'prevent enterprise customers from signing in using SSO');R[310]['flags'].append('component_body_disagreement')
note(314,'Sonnet 3.7 模型错误；Console 仅 operational，没有受影响状态，服务范围收窄到 Claude.ai/API。',['Claude.ai','API'])
note(318,'正文明确仅 Claude.ai 的 Sonnet 3.5 请求，Console/API 全程 operational。',['Claude.ai']);ev(318,'on Claude.ai.')
note(320,'Research 回复的来源没有保存进聊天，模型仍获来源；属于引用/数据完整性退化。');ev(320,'Sources are being correctly provided to the model');cause(320,'are not being persisted into the chat','来源数据没有持久化到聊天。')
daily(321,'19:36:00','19:59:00');ev(321,'From 19:36–19:59 UTC','time')
note(322,'购买 API credits 功能失败，属于 Console 子功能部分不可用。');ev(322,'some users experiencing errors when attempting to purchase API credits');mixed(322,end='05:34:07.414');ev(322,'Credit purchases are currently functional.','time')
note(326,'Claude.ai 后续明确部分用户登录失败；Console 早期只有错误率说明，单独保持未知阶段；API 明确未受影响。');ev(326,'preventing some users from being able to log into Claude.ai.');ev(326,'The Anthropic API is unaffected,','service')
R[326]['time_mode']='explicit';R[326]['intervals']=[phase(326,'2025-05-12T20:32:35.872Z','2025-05-12T20:58:06.581Z',P,['Claude.ai'],'announcement_proxy'),phase(326,'2025-05-12T20:32:35.872Z','2025-05-12T20:53:26.199Z',U,['Console'],'announcement_proxy')];R[326]['flags'].append('service_specific_grade')
note(328,'企业长上下文请求中部分失败，限定请求类型与计划。');ev(328,'some long context requests on Claude for Enterprise')
note(329,'仅 Console 购买 API credits 失败；API 组件始终 operational。',['Console']);mixed(329,end='16:46:21.597');ev(329,'Credit purchases are currently functional.','time')
ev(330,'API requests with web search server tool');mixed(331,'10:05:00');ev(331,'started at 10:05 UTC','time')
daily(332,'15:30:00','17:09:00');ev(332,'From 15:30–17:09 UTC','time')
daily(335,'23:24:00','23:32:00');ev(335,'requests to all models');ev(335,'From 23:24–23:32 UTC','time');R[335]['flags'].append('title_body_scope_disagreement')
ev(336,'preventing image use for some users');ev(337,'resolved upon updating Claude Code.','time');R[337]['flags'].append('client_update_required_recovery')
mixed(338,'05:30:00');ev(338,'started at 05:30 UTC','time')
note(339,'Opus 4 对话错误标为 Legacy 后无法选择继续；这是特定模型选择功能不可用，非仅显示异常。');ev(339,'Opus being unavailable');none(339,'只有事后已恢复公告，没有实际开始或持续时间。')
note(342,'Code execution tools 错误且历史组件为 API Beta Features；按 API 子功能 P。',['API'])
times(343,[('2025-05-27T22:11:00Z','2025-05-28T00:24:00Z')]);ev(343,'Claude.ai and the Anthropic Console were unavailable');ev(343,'From 22:11–00:24 UTC','time');R[343]['use_prior_explicit']=True
daily(344,'13:30:00','14:10:00');ev(344,'Since 13:30 UTC','time');ev(344,'As of 14:10 UTC','time')
none(345,'首条公告已确认修复，不能把其后监控期当故障持续期。');ev(345,'This issue has been resolved,','time')
note(346,'长运行请求提前超时，明确小部分请求受影响，按 P。');ev(346,'a small number of requests timing out earlier than expected')
mixed(348,'06:50:00');ev(348,'Since 6:50 UTC','time')
times(349,[('2025-06-06T12:10:00Z','2025-06-06T12:40:00Z'),('2025-06-06T14:20:00Z','2025-06-06T14:50:00Z')]);ev(349,'Between 12:10-12:40 UTC and 14:20-14:50 UTC','time');R[349]['flags'].append('service_unmapped')
note(353,'GCP 故障影响图片/文件上传及部分模型请求，文本请求仍可成功；不按组件红色状态推断所有产品全停。');ev(353,'Requests involving text-only are likely to be successful');cause(353,'a result of an ongoing outage impacting GCP','GCP 及相关依赖服务故障。');mixed(353,end='20:44:17.119');ev(353,'all success rates have returned to normal','time')
mixed(354,'06:50:00');ev(354,"Since 06:50 UTC",'time');mixed(355,'12:00:00');ev(355,'Since 12 noon UTC','time')
mixed(356,'07:10:00');ev(356,'as of 7:10 UTC','time')
ev(360,'tool use errors on Claude.ai');mixed(361,'12:05:00');ev(361,'Since 12:05 UTC','time');mixed(364,'12:00:00');ev(364,'Since 12:00 UTC noon','time')
daily(365,'05:00:00','10:02:00');ev(365,'starting with 5:00 UTC','time');ev(365,'As of 10:02 UTC','time')
times(368,[('2025-07-03T06:47:00Z','2025-07-03T08:58:24.800Z'),('2025-07-03T09:20:00Z','2025-07-03T10:40:00Z')],False);R[368]['intervals'][0]['time_basis']='announcement_proxy';R[368]['flags'].append('recurrence_preserved');ev(368,'started at 6:47 UTC','time');ev(368,'returned to a baseline','time');ev(368,'starting from 9:20 UTC','time');ev(368,'As of 10:40 UTC','time')
daily(369,'13:55:00','14:21:00');ev(369,'Since 13:55 UTC','time');ev(369,'As of 14:21 UTC','time');mixed(370,end='14:08:13.230');ev(370,'level of errors for Claude 3.5 Haiku is at the baseline.','time')
times(372,[('2025-07-08T11:30:00Z','2025-07-08T14:45:00Z'),('2025-07-08T12:30:00Z','2025-07-08T16:20:00Z'),('2025-07-08T14:30:00Z','2025-07-08T15:39:00Z')]);ev(372,'Claude 3.7 Sonnet between 11:30 UTC and 14:45 UTC','time');ev(372,'Claude 3.5 Sonnet since 16:20 UTC','time');ev(372,'Claude 4 Sonnet since 15:39 UTC','time')
note(374,'只有 21:36–21:52 Claude.ai/Console 全部无法访问；其前后为 Claude.ai 部分请求和 Artifacts 功能失败，分段保留。');ev(374,'users were unable to access Claude.ai or the Anthropic Console');ev(374,'a small number of requests');R[374]['time_mode']='explicit';R[374]['intervals']=[phase(374,'2025-07-09T00:11:32.504Z','2025-07-09T21:36:00Z',P,['Claude.ai'],'announcement_proxy'),phase(374,'2025-07-09T21:36:00Z','2025-07-09T21:52:00Z',F,['Claude.ai','Console']),phase(374,'2025-07-09T21:52:00Z','2025-07-09T23:09:08.008Z',P,['Claude.ai'],'announcement_proxy')];R[374]['flags'].append('multi_phase');R[374]['use_prior_explicit']=True
R[376]['time_mode']='explicit';R[376]['intervals']=[phase(376,'2025-07-09T16:21:00Z','2025-07-09T16:45:00Z'),phase(376,'2025-07-09T16:58:47.364Z','2025-07-09T17:10:33.098Z',basis='announcement_proxy')];R[376]['flags'].append('continued_impact_start_uncertain');ev(376,'From 16:21–16:45 UTC','time');ev(376,'continued impact to some requests')
note(378,'Sonnet 4 输出智力和工具调用格式退化；正文直接确认 Claude Code，其他未指定入口保留 Unmapped。',['Claude Code','Unmapped']);times(378,[('2025-07-08T08:45:00Z','2025-07-10T02:00:00Z')]);ev(378,'From 08:45 UTC on July 8th to 02:00 UTC on July 10th','time');cause(378,'caused by a rollout of our inference stack','推理栈上线导致质量退化，已回滚。');R[378]['use_prior_explicit']=True
daily(379,'06:05:00','08:25:00');ev(379,'since 6:05 UTC','time');ev(379,'As of 8:25 UTC','time');R[379]['time_note']='Sonnet 的 06:05–08:25 已覆盖 Opus 的 07:25–07:43，产品层面对并发影响求并集。'
mixed(380,end='15:15:00');ev(380,'As of 15:15 UTC','time');daily(381,'15:33:00','15:50:00');ev(381,'between 15:33 UTC and 15:50 UTC','time')
none(384,'首条为已实施修复的监控，且全部组件 operational；真实影响开始不明。')
mixed(386,'10:00:00');ev(386,'since 10AM UTC','time');R[386]['flags'].append('intermittent_proxy_envelope')
mixed(387,'13:05:00',end='16:08:07.883');ev(387,'since 13:05 UTC','time')
note(390,'API 请求提前终止，未证明全部 API 或全部 Code 调用失效；按请求执行失败的部分不可用。')
note(393,'正文和标题明确 Claude Code 调用 Opus 4 路径；不将其他被勾选组件自动扩展为已证实影响。',['Claude Code']);ev(393,'via Claude Code')
daily(394,'06:15:00','08:52:00');ev(394,'started at 6:15 UTC','time');ev(394,'As of 08:52 UTC','time')
daily(399,'06:00:00','06:39:00');ev(399,'6:00 UTC','time');ev(399,'6:39 UTC','time');daily(400,'09:06:00','09:15:00');ev(400,'9:06 UTC','time');ev(400,'9:15 UTC','time')
times(401,[('2025-07-23T13:05:00Z','2025-07-23T13:24:00Z'),('2025-07-23T13:50:00Z','2025-07-23T14:18:00Z')],False);R[401]['flags'].append('only_spike_windows_known');R[401]['time_note']='仅计供应商列出的两次明显峰值；首报 13:04 与首峰 13:05 有一分钟差异，未声称中间无影响。';ev(401,'between 13:05 UTC and 13:24 UTC','time');ev(401,'between 13:50 UTC and 14:18 UTC','time')
daily(403,'19:07:00','19:28:00');ev(403,'19:07 UTC','time');ev(403,'19:28 UTC','time')
mixed(404,'21:40:00');ev(404,'21:40 UTC','time');R[404]['flags'].append('edited_update_mentions_future_stage')
none(407,'恢复正文 22:45 PT / 6:45 UTC 换算差一小时，且 06:45 晚于发布 05:47；保留冲突，不选一个作为真值。','time_conflict');ev(407,'22:45 PT / 6:45 UTC','time')
times(408,[('2025-07-25T06:55:00Z','2025-07-25T08:00:00Z'),('2025-07-25T08:58:00Z','2025-07-25T09:21:00Z'),('2025-07-25T12:47:00Z','2025-07-25T15:35:00Z')],False);R[408]['flags']+=['recurrence_preserved','between_spikes_residual_errors_uncertain'];R[408]['time_note']='保留三段已知影响；最后一段合并两峰及供应商明确仍有中等错误的间隔。首段恢复为低错误率而非严格零影响，窗口并非完整真实停机。';ev(408,'6:55 UTC','time');ev(408,'8:00 UTC','time');ev(408,'8:58 UTC and 2:21 PT / 9:21 UTC','time');ev(408,'a period of medium level of errors','time');ev(408,'15:35 UTC','time')
note(409,'正文明确 Opus 4 影响 Claude Code；服务范围收窄。',['Claude Code']);mixed(409,'14:40:00');ev(409,'14:40 UTC','time');R[409]['flags'].append('PST_label_conflicts_with_UTC_but_explicit_UTC_used')
none(411,'恢复写为 09:05 PT / 16:05 PT，两个同一时区时刻矛盾；不静默把后一 PT 改成 UTC。','time_conflict');ev(411,'09:05 PT / 16:05 PT','time')
daily(414,'06:35:00','08:36:00');ev(414,'6:35 UTC','time');ev(414,'08:36 UTC','time')
daily(415,'13:15:00','15:00:00',False);R[415]['flags'].append('approximate_start');ev(415,'around 6:15 PT / 13:15 UTC','time');ev(415,'15:00 UTC','time')
mixed(416,end='18:30:00');ev(416,'As of 18:30 UTC','time');daily(417,'08:00:00','08:20:00');ev(417,'8am UTC, lasting 20 minutes','time')
none(419,'仅潜在错误标题和修复后监控，无真实发生范围或开始；不将整个监控阶段视为已确认影响。');R[419]['flags'].append('potential_impact_only')
none(420,'11:32 发布的结案称已于 13:15 UTC 恢复，恢复时间晚于自身公告；无法确定真实终点。','time_conflict');ev(420,'13:15 UTC / 6:15 PT','time')
daily(421,'13:00:00','13:55:00');ev(421,'13:00 UTC','time');ev(421,'13:55 UTC','time')
none(422,'PT/UTC 双时间换算错一小时，且 09:10 UTC 晚于结案发布 08:50；不静默修正。','time_conflict');ev(422,'22:30 PT / 6:30 UTC','time');ev(422,'1:10 PT / 9:10 UTC','time')
for n in (427,428):
 note(n,'8 月 15 日起升级账户未获得限额增加及 Opus 权限，属于订阅用户子集不可用。');ev(n,'Starting August 15th','time');none(n,'开始只有日期无时区/时刻，且两条同主题记录可能连续或重复；不伪造精确起止。','date_only_start');R[n]['flags'].append('possible_duplicate_related_incident')
none(429,'正文称 since August 18，仅日期无时区/时刻；无法完整定位真实影响窗口。','date_only_start');ev(429,'since August 18','time');ev(429,'unable to add more members')
daily(430,'13:22:00','14:50:00');ev(430,'13:22 UTC','time');ev(430,'14:50 UTC','time')
cause(435,'We identified a regression','供应商确认回归问题但未披露技术细节。');none(435,'周末部署并监控修复，仅周一结案，缺实际修复时刻；不将完整周末当停机。','retrospective_recovery_unpositioned')
ev(441,'failing to downgrade MCP connections to SSE');cause(441,'failing to downgrade MCP connections to SSE','部分 MCP 服务器连接未正确降级到 SSE。')
mixed(438,'18:40:00');R[438]['flags'].append('approximate_start_timezone_inferred');ev(438,'~11:40 PT','time');mixed(442,end='14:45:00');ev(442,'14:45 UTC','time')
daily(443,'06:08:00','07:46:00');ev(443,'6:08 UTC','time');ev(443,'7:46 UTC','time');daily(444,'11:14:00','13:40:00');ev(444,'11:14 UTC','time');ev(444,'13:40 UTC','time');daily(445,'06:10:00','07:50:00');ev(445,'6:10 UTC','time');ev(445,'7:50 UTC','time')
none(446,'首报 12:29 称自 13:05 UTC 已恢复且 PT 换算也不一致；起始和终止语义不可信。','time_conflict');ev(446,'5:05 PT / 13:05 UTC','time')
note(449,'预告的 Connector Auth Storage 维护，保留记录并排除事故可用性统计。');none(449,'计划维护，非事故。','maintenance')
daily(450,'05:30:00','09:15:00');ev(450,'5:30 UTC','time');ev(450,'9:15 UTC','time')
note(451,'推理栈上线导致 Opus 4.1/4 质量下降；4.1 有明确历史窗口，4 的开始未知，保留可定位部分且明确不完整。');times(451,[('2025-08-25T17:30:00Z','2025-08-28T02:00:00Z')],False);R[451]['flags'].append('additional_model_period_unpositioned');ev(451,'From 17:30 UTC on Aug 25th to 02:00 UTC on Aug 28th','time');cause(451,'caused by a rollout of our inference stack','推理栈上线导致输出质量退化，回滚。')
daily(452,'05:30:00','08:15:00');ev(452,'5:30 UTC','time');ev(452,'8:15 UTC','time');R[452]['flags'].append('model_name_corrected_in_update')
none(453,'恢复写为 00:50 PT / 7:30 UTC，换算相差 20 分钟，终点不唯一。','time_conflict');ev(453,'00:50 PT / 7:30 UTC','time')
mixed(455,'06:10:00');ev(455,'6:10 UTC','time');mixed(457,end='07:15:00');ev(457,'7:15 UTC','time')
daily(458,'06:25:00','06:50:00');ev(458,'6:25 UTC','time');ev(458,'6:50 UTC','time');daily(459,'13:00:00','14:30:00');ev(459,'13:00 UTC','time');ev(459,'14:30 UTC','time');daily(460,'14:30:00','15:15:00');ev(460,'14:30 UTC','time');ev(460,'15:15 UTC','time')
none(464,'正文追溯 Aug 5–Sep 4 与 Aug 26–Sep 5 的质量问题，日期无完整时区边界；不能用 Sep 9–17 公告生命周期替代。','retrospective_date_only');cause(464,'the issues mentioned above stem from unrelated bugs','两个互不相关的软件缺陷造成模型质量退化；此条无更具体技术根因。');ev(464,'from Aug 5-Sep 4','time');ev(464,'from Aug 26-Sep 5','time')
mixed(466,'06:53:00',end='09:14:56.676');ev(466,'6:53 UTC','time')
# Only record 467 substantiates a total outage then staggered historical recovery.
note(467,'正文明确 API、Console、Claude.ai 全停；随后按各组件历史 F/P/D 恢复阶段分段，不把最高 F 延伸到全部结案周期。');ev(467,'APIs, Console, and Claude.ai are down.');R[467]['flags'].append('multi_phase');R[467]['time_mode']='explicit';R[467]['intervals']=[]
for group,segments in {'Claude.ai':[('16:28:37.000','16:37:28.000',F),('16:37:28.000','16:55:23.000',P),('16:55:23.000','17:15:16.621',D)],'Console':[('16:28:37.000','16:55:23.000',F),('16:55:23.000','17:15:16.621',D)],'API':[('16:28:37.000','16:55:23.000',F),('16:55:23.000','17:30:15.351',P),('17:30:15.351','17:36:04.544',D)]}.items():
 for a,b,g in segments:R[467]['intervals'].append(phase(467,'2025-09-10T'+a+'Z','2025-09-10T'+b+'Z',g,[group],'official_component_interval'))
note(468,'仅称 Claude.ai services impacted 后直接结案，无法判断具体影响方式和程度。',['Claude.ai']);none(468,'仅有已恢复单条公告，无可定位的开始。')
daily(469,'13:10:00','14:05:00');ev(469,'13:10 UTC','time');ev(469,'14:05 UTC','time')
none(470,'15:40–15:51 PT 与 22:40–22:41 UTC 持续时间冲突；保留模型 P，但时长未知。','time_conflict');ev(470,'15:40-15:51 PT (22:40-22:41 UTC)','time')
times(471,[('2025-09-15T06:15:00Z','2025-09-15T07:40:00Z'),('2025-09-15T08:20:00Z','2025-09-15T09:00:00Z')]);R[471]['flags'].append('recurrence_preserved');ev(471,'6:15 UTC','time');ev(471,'07:40 UTC','time');ev(471,'08:20 UTC','time');ev(471,'9:00 UTC','time')
daily(472,'10:45:00','11:30:00');ev(472,'10:45 UTC','time');ev(472,'11:30 UTC','time');R[472]['flags'].append('model_name_corrected_in_update');daily(473,'11:10:00','12:10:00');ev(473,'11:10 UTC','time');ev(473,'12:10 UTC','time');daily(475,'06:35:00','08:05:00');ev(475,'6:35 UTC','time');ev(475,'8:05 UTC','time')
ev(476,'except for Sonnet 4.0.');daily(476,'19:35:00','20:40:00');ev(476,'19:35 UTC','time');ev(476,'20:40 UTC','time')
times(477,[('2025-09-20T02:00:00Z','2025-09-20T05:00:00Z'),('2025-09-20T02:30:00Z','2025-09-20T03:30:00Z')]);ev(477,'Sep 20 02:00 UTC','time');ev(477,'Sep 20 05:00 UTC','time');R[477]['flags'].append('retrospective_exact_window')
note(479,'连接错误公告与组件红色状态不足以确认全量失败；后续明确部分端点恢复，保留未知严重度候选窗口。');ev(479,'restored service on some endpoints.');mixed(479,end='21:08:15.326');ev(479,'Services have been restored.','time')
ev(480,'fetching images and PDFs by URL');mixed(480,end='20:17:31.554');ev(480,'all systems are now operating normally.','time')
note(486,'Sonnet 4 的部分 Claude.ai 用户收到 conversation not found，部分不可用。',['Claude.ai']);ev(486,'some claude.ai users of Sonnet 4');none(486,'仅单条事后恢复公告，未知开始。')
R[488]['flags'].append('recurrence_preserved')
note(491,'复盘确认间歇访问异常及错误率/延迟，并非证明全量故障；访问失败为 P，Claude.ai 早于 API/Code 恢复。');R[491]['grade']=P;ev(491,'intermittent access issues');cause(491,'triggered by an upstream provider error','上游供应商错误暴露自身基础设施问题，并延长恢复。');R[491]['time_mode']='explicit';R[491]['intervals']=[phase(491,'2025-10-03T01:17:00Z','2025-10-03T02:53:58.483Z',P,['Claude.ai'],'announcement_proxy'),phase(491,'2025-10-03T01:17:00Z','2025-10-03T03:47:00Z',P,['API','Console','Claude Code'])];R[491]['flags'].append('approximate_start');ev(491,'approximately 1:17 AM UTC','time');ev(491,'fully resolved by 3:47AM UTC','time');ev(491,'Claude.ai is back up.','time')
mixed(492,'05:47:00',end='08:39:26.637');ev(492,'05:47 UTC','time');ev(495,'Claude.ai remains available in a browser, iOS, and Android.');cause(495,'responsible code issue','供应商确认客户端代码问题但未披露细节。');R[495]['flags'].append('client_restart_required')
cause(496,'a faulty edge proxy deployment','错误的边缘代理部署，已回滚。')
note(500,'标题明确 Claude.ai 连接器与 API server tools/MCP 错误，补充 API 范围；均为子功能 P。',['Claude.ai','API']);R[500]['flags'].append('service_added_from_title')
times(510,[('2025-11-03T23:00:00Z','2025-11-04T18:45:00Z')],True,'timezone_inferred');ev(510,'3pm on Nov 3 PST','time');ev(510,'10:45am on Nov 4 PST','time')
note(511,'Claude Code Web 路径错误属于 Code 子入口不可用；记录首报已 monitoring、组件 operational，真实时间不可定位。');none(511,'监控公告没有故障开始，不能将一分钟监控阶段视为全部影响。')
daily(514,'16:44:00','17:37:00');ev(514,'16:44 PM UTC','time');ev(514,'Errors have returned to baseline from 17:37 UTC','time');R[514]['flags'].append('later_recovery_statement_18_01');R[514]['time_note']='选择明确错误回基线 17:37；后续 18:01 recovered 是较晚平台恢复确认，不延长错误窗口。'
daily(515,'17:20:00','22:30:00');ev(515,'Between 17:20 and 22:30 UTC','time')
cause(523,'due to a third-party vendor','第三方供应商故障，未披露名称与技术原因。')
mixed(525,end='11:55:00');ev(525,'11:55 UTC','time');note(527,'部分 Claude Code 用户错误率上升，范围明确为用户子集。',['Claude Code']);ev(527,'Some Claude Code users');none(527,'只有事后恢复公告，无实际起止。')
ev(528,"Sonnet model usage was counted as Opus usage.")
daily(537,'12:11:00','12:18:00');ev(537,'12:11 UTC','time');ev(537,'12:18 UTC','time')
times(538,[('2025-12-04T22:01:00Z','2025-12-05T00:48:00Z')]);ev(538,'From 22:01 UTC to 00:48 UTC','time')
cause(539,'An upstream provider has implemented a fix','上游供应商修复了其问题；未披露技术根因。')
note(540,'标题确认 Claude.ai 不可用；Console 仅被列组件且无文字证明全量，单独保留 U 候选阶段。');R[540]['flags'].append('service_specific_grade');R[540]['time_mode']='explicit';R[540]['intervals']=[phase(540,'2025-12-05T10:47:09.383Z','2025-12-05T11:18:24.529Z',F,['Claude.ai'],'announcement_proxy'),phase(540,'2025-12-05T10:47:15.182Z','2025-12-05T11:18:24.529Z',U,['Console'],'official_component_interval')]
note(541,'部分 App Store 购买 Pro/Max 用户无正确计划权限；仅确认 Claude.ai 订阅入口，不扩展所有 Code 调用。',['Claude.ai']);cause(541,'a bug introduced in Claude iOS app version 1.251117.1','iOS 版本 1.251117.1 引入购买激活缺陷。');none(541,'用户影响起自 Nov 24 或之后的购买，缺实际起始时刻；首报已修复新购买但既有账户仍待恢复，不能用公告周期替代。','date_only_start')
note(543,'无法开始聊天是 Claude.ai 新建会话功能失效；非证明已有对话全停。',['Claude.ai']);none(543,'只有结案公告，无实际开始。')
note(544,'文档站欧洲区域错误，归辅助网站而非 Console 核心产品。',['Other'])
ev(545,'related to Sonnet 4.0, Sonnet 4.5, and Opus 4.5.');mixed(545,end='22:43:00');ev(545,'22:43 UTC','time')
note(548,'新聊天错误默认选择 Opus，属于选择状态/产品行为退化，未说明请求不可执行。')
note(549,'正文明确只影响免费 Claude.ai 用户，API 组件被纠正为 operational。',['Claude.ai']);ev(549,'only free tier claude.ai users.')
R[551]['flags'].append('client_update_required_recovery')
none(560,'新购买从约 Jan 8 22:00 PST 起，修复约结案前两小时；结案仍待恢复旧账户权限，无法定义完整真实受影响结束。','partial_recovery_unpositioned');ev(560,'The issue began around 10PM PST on 2026-01-08','time');ev(560,'work to restore access and/or provide refunds','time')
R[566]['flags'].append('recurrence_preserved')
note(567,'仅称 compaction having issues，未说明失败还是质量/速度退化；不凭组件标签判 P/D。')
note(573,'跨 Bedrock、Vertex 与第一方 API 混用 thinking signature 的请求失败；各平台独立使用正常。第一方 API 特定请求路径 P，保留外部互操作影响。',['API','External']);ev(573,'Each platform is fully operational independently.');none(573,'00:00–08:00 是产生不兼容响应的窗口，后续跨平台重放仍可能报错，非完整用户影响终点。','persistent_artifact_effect_unpositioned');ev(573,'there may still be errors.','time')
mixed(578,end='11:50:00');ev(578,'11:50 UTC','time');daily(579,'13:41:00','14:12:00');ev(579,'13:41 UTC','time');ev(579,'14:12 UTC','time')
note(580,'充值余额/计费/自动充值及恢复权限延迟，正文描述延迟而非失败；按 D。');ev(580,'There is no longer a system delay')
R[581]['flags'].append('client_update_required_recovery')
daily(582,'10:41:00','10:51:00');ev(582,'10:41 UTC','time');ev(582,'10:51 UTC','time');daily(583,'11:36:00','11:55:00');ev(583,'11:36 UTC','time');ev(583,'11:55 UTC','time')
mixed(584,end='22:30:00');R[584]['flags'].append('approximate_recovery_timezone_inferred');ev(584,'since around 2:30pm Pacific Time','time');daily(585,'23:09:00','23:15:00');ev(585,'23:09 UTC to 15:15 PT / 23:15','time')
note(586,'Desktop SSO/magic link 登录退化，但未说明具体失败或延迟比例；仅按供应商明示退化保留 D。',['Claude.ai']);none(586,'仅一条已恢复记录，无可定位开始。')
note(588,'API 所有模型有较小比例请求受影响，不能因 critical 变成所有请求全停。',['API']);daily(588,'17:52:00','17:56:00');ev(588,'The percentage of requests impacted was also smaller.');ev(588,'17:52 UTC','time');ev(588,'17:56 UTC','time');R[588]['use_prior_explicit']=True
daily(590,'20:08:00','22:38:00');ev(590,'20:08 and 22:38 UTC','time');times(591,[('2026-02-04T10:00:00Z','2026-02-04T10:35:00Z'),('2026-02-04T10:54:00Z','2026-02-04T11:01:00Z')]);ev(591,'10:00 UTC to 02:35 PT / 10:35 UTC','time');ev(591,'10:54 UTC to 03:01 PT / 11:01 UTC','time');R[591]['flags'].append('recurrence_preserved')
daily(592,'16:20:00','16:55:00');ev(592,'16:20 UTC','time');ev(592,'16:55 UTC','time')
note(594,'Claude.ai 错误率上升缺用户/请求边界，且仅已恢复记录。',['Claude.ai']);none(594,'单条结案，无时间定位。')
daily(595,'15:15:00','16:27:00');ev(595,'15:15 UTC','time');ev(595,'16:27 UTC','time');mixed(596,'10:05:00');ev(596,'about 02:05 PST','time');R[596]['flags'].append('approximate_start_timezone_inferred')
R[597]['flags'].append('service_unmapped');mixed(597,end=None);R[597]['intervals'][0]['end_at']='2026-02-11T02:51:57.931Z';ev(597,'The issue has been mitigated.','time')
note(605,'API code execution tool 请求报错，限定 API 工具路径。',['API']);ev(605,'API requests using the Code Execution Tool are erroring')
ev(612,'skills-related service used by claude.ai, Claude Desktop app, and our API.');R[612]['flags'].append('intermittent_proxy_envelope');R[612]['time_note']='正文明确 periods of high error rates，但无各段边界；公告周期只是可能包含正常间隔的代理包络，非连续真实故障。'
# Validate every bound quote against immutable docket, every interval positive,
# and maintain complete assigned coverage.
from datetime import datetime
for n,r in R.items():
 if r['groups']==['Unmapped']:r['flags'].append('service_unmapped')
 r['flags']=sorted(set(r['flags']))
 for e in r['evidence']:
  source=A[n]['title'] if e['update_id'] is None else next(u['body'] for u in A[n]['updates'] if u['id']==e['update_id'])
  assert e['quote'] in source,(n,e)
 for p in r.get('intervals',[]):assert datetime.fromisoformat(p['end_at'].replace('Z','+00:00'))>datetime.fromisoformat(p['start_at'].replace('Z','+00:00')),(n,p)
assert sorted(R)==list(range(307,614))
(ROOT/'middle.json').write_text(json.dumps(list(R.values()),ensure_ascii=False,indent=2)+'\n')
counts=Counter(r['grade'] for r in R.values()); modes=Counter(r['time_mode'] for r in R.values())
(ROOT/'middle.md').write_text('# 中段完整复核\n\n逐条读取冻结 docket 307–613（含首尾，共 307 条）的全部更新正文、时间、状态和历史组件变化。没有截断正文；工具批次 307–346、347–348、349–386、387–426、427–466、467–506、507–546、547–586、587–613。首次 347–386 读取因 None affected_components 在 349 中止，已从 349 重读全批。\n\n'+f'分级：{dict(counts)}。时间模式：{dict(modes)}。\n\n'+'所有等级是人工阅读后录入的固定决定，脚本不使用关键词分类。每条有原文标题证据，复杂案例另附正文与时间证据；所有 quote 与原文逐字校验通过。\n\n'+'重点修正：单模型/登录/功能失败按产品 P；不把 major_outage 自动视为 F。374 和 467 分阶段，326/540 区分不同产品未知等级。368/376/401/408/471/488/566/591 保留复发或明确峰值。407/411/420/422/446/453/470 时间冲突不填造精确窗口。451 只保留明确的历史 Opus 4.1 质量窗口，464 不使用事后公告跨度。427/428 可能重复，日期边界不确定。612 仅有间歇影响的代理包络；统计应单列敏感性。\n\n'+'服务映射：342 历史 API Beta 归 API；393/409 限 Code；544 文档站归 Other；549 限免费 Claude.ai；588 沿用已复核 API 范围；378 明确 Code 外其他服务为 Unmapped，避免凭模型名称扩大到全部第一方产品。\n')
print(dict(counts),dict(modes),len(R))
