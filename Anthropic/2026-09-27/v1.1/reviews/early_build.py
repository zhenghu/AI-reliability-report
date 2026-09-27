"""Serialize explicit human review decisions after full docket reading; no keyword grading."""
import json
from pathlib import Path
P=Path(__file__).parent; X=json.loads((P.parents[1]/'v1.0/review-docket.json').read_text())[:307]
G={'F':'full_outage','P':'partial_outage','D':'degraded_performance','U':'unknown'}
# Exhaustively read 0..306. The majority are specifically named model/feature failures.
U=set([8,11,25,28,32,38,42,46,51,55,78,100,107,110,111,115,123,126,127,146,148,149,184,185,194,195,201,209,214,215,218,225,235,254,260,272,274,276,277,278,303,304,305])
D=set([12,20,22,43,47,59,67,84,91,101,103,125,138,152,157,161,167,169,182,189,191,217,239,249,258,259,268,280,281,288,301])
F=set([2,14,15,19,30,37,95,104,150,162,197,226,231,263,264,269])
assert not(U&D or U&F or D&F)
C={'claude.ai':'Claude.ai','Claude Console (platform.claude.com)':'Console','Claude API (api.anthropic.com)':'API'}
over={**{n:['API'] for n in range(15)},
13:['Console','API'],15:['Other'],16:['Claude.ai','Console','API'],
20:['Claude.ai','Unmapped'],
28:['API'],
34:['Unmapped'],
42:['Claude.ai'],
58:['Unmapped'],
60:['Other'],
62:['Unmapped'],
69:['Claude.ai','Console'],
70:['Unmapped'],
75:['Unmapped'],
77:['Claude.ai','Console'],
86:['Unmapped'],
91:['Claude.ai','Console','API'],
95:['External'],
112:['External'],
116:['External'],
117:['External'],
120:['External'],
121:['External'],
123:['API'],
129:['Claude.ai','API','External'],
140:['External'],
153:['Unmapped'],
162:['Other'],
166:['Other'],
167:['Console'],
172:['External'],
175:['External'],
186:['API'],
191:['API'],
201:['Other'],
218:['Other'],
230:['Unmapped'],
257:['Claude.ai'],
260:['Other'],
280:['Unmapped']}
reason={n:'公告明确限定指定模型、用户或功能路径发生失败，按整个产品范围判为部分不可用；原始官方标签不作为语义等级。' for n in range(307)}
for n in U:reason[n]='已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。'
for n in D:reason[n]='公告支持延迟、输出质量、显示或数据状态退化，未证明整个服务停止，判为性能/质量退化。'
for n in F:reason[n]='公告明确声明所列服务不可访问或停止工作，仅按声明的服务范围判为完全不可用。'
reason.update({0:'多数 API 流量受影响一小时，不是全部请求；只有时长无法定位实际区间。',
1:'多数 API 流量受影响30分钟，不是全部请求；只有时长无法定位实际区间。',
2:'所有当时模型暂时离线，API 请求返回404，判 API 完全不可用。',
5:'claude-v1.0 请求失败但其他模型继续服务，在 API 产品范围为部分不可用。',
9:'标题明确仅部分用户遇到529错误。',
13:'Console与API间歇报错支持部分请求失败。',
16:'标题明确 Claude.ai/Console 部分故障；首条还标 API 异常，保留历史组件各自时间。',
19:'Claude.ai 停止访问，API/Console仅退化；拆分服务等级，不能整段全服务按F。',
24:'正文量化每10分钟有5–10%请求出错，明确部分请求失败；不能视为连续全量失败。',
26:'初始指定模型访问失败，后续报告部分模型延迟；区分P与D阶段，时间采用公告边界。',
28:'API请求报错没有失败比例；3:55–4:00 PST 缺少AM/PM且公告接近前一日16:00PST，时间保留歧义。',
34:'仅claude-instant-1.2和claude-2.1不可用；平台未明确，保留Unmapped；负载均衡配置错误由供应商披露。',
43:'仅后续正文明确Instant性能退化，初始通用错误率无法语义定级；保留分段未知。',
59:'标题支持Haiku性能退化，早期官方P状态无进一步文字支持；保留初始阶段未知，随后D。',
60:'文档托管商故障属于Other；正文声明12:48 PDT恢复，不归推理API。',
69:'账号创建、文档上传和用量面板失败为部分功能；正文Feb18与公告Apr18冲突。',
78:'明确网站维护记录，不纳入非计划事故。',
82:'维护操作使Instant1.2部分不可用；这是操作导致的故障而非预告维护。',
84:'登录邮件严重延迟，恢复时间给出5pm Pacific；按延迟D，不当作全站故障。',
90:'Haiku采样请求报错，限定模型请求路径为P；无证据所有API不可用。',
91:'用户图片因bug裁剪成正方形，属于输入数据/质量退化。',
95:'明确Opus在Vertex完全不可访问；范围只限该第三方模型部署，不进入第一方核心产品计算。',
99:'Console部分账单功能失败、部分用户不能购入额度，P。',
102:'页面部分UI报错或缓慢，明确功能子集错误判P，延迟是伴随现象。',
108:'结案明确只有部分Claude.ai/Console使用受影响，P。',
125:'正文确认API延迟升高可判D，错误比例未知；其他服务通用错误保持未知，分组分段。',
126:'后端服务中断为已披露原因，但错误比例未知；8:27PST与夏令时/公告时间不一致。',
129:'两个指定模型及免费用户受限，期间恢复后复发；免费层禁用不等于全站F，按服务分段P。',
131:'领取免费额度和Build问卷提交路径失败；后续澄清常规购额不受影响，P。',
135:'免费用户临时转到Haiku，指定Sonnet访问受限仍属P。',
136:'免费用户Sonnet访问被移走；API只有部分Sonnet请求错误，各服务分别定边界。',
138:'首次公告已明确正常服务恢复，后续37小时不是影响区间；质量D可判但起止未知。',
145:'Sonnet错误在修复后复发；免费用户持续切换Haiku，保留服务分段。',
147:'Claude3子集失败，3.5Sonnet未受影响，修复后Haiku复发；需保留恢复间隙。',
158:'明确间歇错误06:00–16:02，但免费用户Sonnet仍未恢复；已知错误区间与后续受限分开且时间不完整。',
159:'仅旧Claude1.0/1.1/1.2不可用，不是整个API/Console完全停止。',
165:'模型错误已恢复后免费用户仍切到Haiku，Claude.ai区间延续到模型恢复。',
167:'API成功率明确不受影响；用量与账单显示延迟仅记Console D。',
168:'限定3.5Sonnet错误为P；回溯18:42–19:52未注明时区，不擅自UTC定位。',
170:'极少量首次3DS购额用户未激活，账号子集不可用判P。',
175:'Bedrock指定模型错误；结案正文仍说继续修复，与resolved状态冲突，恢复时间未知。',
180:'Sonnet两段错误之间恢复；Claude.ai免费层仍切换Haiku，不能把全服务间隙连成停机。',
182:'工具参数不完整是输出/结构质量退化D；回溯影响10月28日21:00至30日04:15UTC。',
183:'主要错误12:38–12:51但免费层模型仍切换；公告仅称primarily且恢复日期不明，时间不完整。',
186:'仅Message Batches API beta受影响，其他API明确不受影响，API产品P。',
194:'列举Haiku、Sonnet、Opus覆盖模型家族但无子集限定或错误比例，不能确认P/F。',
198:'只有新生成API密钥失败；11:49与12:00两种起始阈值冲突，时间保留未知。',
199:'IPv6路径禁用，其他路径仍可用为P；公告即resolved但称未来24小时重启，恢复端点不明。',
202:'初期API延迟D；03:41起部分Sonnet请求错误P；恢复公告封口，分阶段计算。',
208:'正文限定specific API workloads受影响，P。',
210:'明确部分请求529，成功率恢复时结束代理，不延至第二天结案。',
212:'登录注册失败及间歇不可用构成P，另有延迟D；不自动把官方D改成全站F。',
213:'失败比例1–2%且重试可成功，P；次日明确成功率/延迟恢复结束。',
214:'预告维护，排除非计划事故。',
215:'实际UTC窗口已给，但通用错误缺失败比例，等级U。',
218:'厂商明确所有系统和服务不受影响；社交账号事件，排除核心可用性。',
221:'回溯影响窗口05:05–05:22与04:23开始调查不一致；保留时间冲突，不把两个窗口拼接。',
225:'最终调查明确未影响用户请求；撤销初始错误告警的影响判断。',
231:'结案明确Claude.ai及Console不可用，非仅登录，因此F，API不受影响。',
253:'Artifacts发布/访问路径失败为P；只给实际起点，恢复时刻以结案代理，非精确全时间线。',
254:'官方标major但正文只说错误率与most models恢复，无完整失败范围证据，U。',
257:'项目聊天功能不可访问半小时，P；无法定位实际起止。',
258:'删除后Artifact仍对组织同事可见，属于数据状态D；结案时仍在修正历史数据，完整修复终点未知。',
259:'明确延迟可判D；伴随错误未给范围，不能据此升级F/P。',
267:'正文明确部分模型及后续部分用户请求失败，产品P；官方major不代表整个产品停机，服务恢复分别定位。',
268:'特殊字符或语言异常为质量D；首次通知即已恢复，真实区间未知。',
269:'原错误比例未知；事故处理中临时下线维护、随后恢复，只有这个明确下线阶段判F，其他阶段U。',
274:'访问错误率显著升高但未称全部无法访问，等级U；实际时间窗明确。',
275:'初始公告指3.5Sonnet，回溯多模型错误及继续残余Sonnet错误，P；两阶段与恢复间隔分开。',
280:'性能退化D，PST标签在夏令时日期且公告早于描述结束，保留时间歧义。',
284:'Haiku不能读取图像内容是质量D，部署期间额外请求失败P；实际结束20:15晚于结案19:26有冲突，不以推测修正。',
286:'仅部分登录用户曾出错，首次公告已监控且组件operational，不能确定影响开始与恢复。',
297:'启用analysis tool时特定文件类型上传失败；开始仅给4月14日日期，精确UTC不可定位。',
301:'明确邮件最终会到但延迟，D；恢复公告结束代理。',
303:'厂商最终确认错误未影响用户请求，排除影响时长。'})
# Specific update quotes selected manually after review; title quote retained for every row.
E={0:0,
1:0,
2:0,
3:0,
4:0,
5:0,
6:0,
12:3,
18:0,
20:0,
21:0,
22:0,
23:2,
24:15,
26:7,
27:1,
28:0,
31:3,
32:0,
34:0,
42:0,
43:3,
49:2,
50:1,
60:0,
62:0,
63:0,
65:2,
67:2,
68:2,
69:0,
70:0,
71:1,
72:1,
74:2,
77:0,
78:1,
80:2,
81:2,
82:1,
84:0,
86:0,
88:1,
91:0,
94:3,
95:0,
99:2,
102:3,
103:0,
106:2,
108:0,
109:1,
116:1,
117:1,
120:2,
121:1,
124:0,
125:3,
126:1,
128:0,
129:3,
130:0,
131:2,
132:2,
133:2,
135:3,
136:2,
137:1,
138:1,
139:1,
143:1,
145:2,
146:1,
147:4,
148:0,
149:0,
150:0,
151:0,
152:2,
153:0,
154:2,
155:3,
156:0,
157:0,
158:1,
159:2,
160:0,
162:1,
163:2,
164:0,
165:1,
166:1,
167:1,
168:0,
169:2,
170:0,
171:3,
172:1,
174:2,
175:0,
179:1,
180:1,
182:0,
183:1,
184:2,
186:2,
187:4,
188:1,
192:3,
193:2,
195:0,
196:2,
197:0,
198:2,
199:0,
202:2,
203:2,
206:2,
207:4,
208:2,
210:1,
211:0,
212:4,
213:4,
214:3,
215:0,
216:2,
218:0,
219:2,
221:0,
222:2,
224:2,
225:0,
226:0,
228:0,
230:0,
231:0,
233:1,
234:3,
235:2,
236:1,
238:4,
240:3,
243:2,
249:0,
253:0,
254:1,
256:0,
257:0,
258:1,
259:0,
260:0,
261:0,
262:3,
266:1,
267:2,
268:0,
269:2,
270:2,
271:2,
274:0,
275:3,
278:1,
280:0,
282:3,
284:0,
286:1,
291:1,
292:2,
296:1,
297:0,
300:0,
301:2,
302:0,
303:0}
R=[]
for r in X:
 n=r['n'];g='U' if n in U else 'D' if n in D else 'F' if n in F else 'P';groups=over.get(n,[C[c] for c in r['components'] if c in C]) or ['Unmapped']
 ev=[{'quote':r['title'],'update_id':None,'kind':'severity','reason':reason[n]}]
 if n in E:
  u=r['updates'][E[n]];ev.append({'quote':u['body'],'update_id':u['id'],'kind':'severity','reason':reason[n]})
 R.append(dict(n=n,incident_id=r['id'],grade=G[g],groups=groups,summary=reason[n],evidence=ev,time_mode='component_or_proxy',time_note='无完整实际起止；仅可按历史组件状态或公告时间代理，监控不自动等于恢复。',time_complete=False,root_cause_status='not_disclosed',root_cause='',flags=[]))

def no(n,msg,flag='unknown_actual_time'):
 R[n].update(time_mode='none',time_note=msg,time_complete=False);R[n]['flags'].append(flag)
def span(n,a,b,sev=None,gs=None,basis='explicit_impact',complete=True):
 R[n].update(time_mode='explicit',time_complete=complete,time_note='按原文实际UTC时间窗；若时间基础为代理则非完整真实时间。')
 R[n].setdefault('intervals',[]).append(dict(start_at=a,end_at=b,severity=G.get(sev,sev) if sev else R[n]['grade'],service_groups=gs or R[n]['groups'],time_basis=basis))
def same(n,start,end,sev=None,gs=None):
 day=X[n]['date'][:10];span(n,day+'T'+start+'Z',day+'T'+end+'Z',sev,gs)
def proxy(n,si,ei,sev=None,gs=None):
 span(n,X[n]['updates'][si]['display_at'],X[n]['updates'][ei]['display_at'],sev,gs,'announcement_proxy',False)
# Records with no interval information, resolved before publication, or unresolved contradictions.
for n in [0,1,9,10,20,25,28,37,58,62,69,70,75,86,123,126,138,168,175,198,199,221,257,258,268,280,284,286,297]:no(n,'已读完整公告；持续时长/日期或结束叙述不足以无歧义定位实际UTC区间，未把公告生命周期当实际影响。')
for n in [78,184,214]:no(n,'已确认为维护，保留原记录但排除非计划事故。','maintenance')
for n in [218,225,303]:no(n,'结案明确没有Anthropic服务或用户请求影响，排除故障区间。','no_user_impact')
for n in [69,126,168,175,198,199,221,280,284]:R[n]['flags'].append('source_time_conflict_or_ambiguity')
# Actual timestamps read from full updates.
for n,a,b in [(2,'19:04:00','19:06:00'),(3,'10:17:00','10:18:00'),(4,'08:58:47','08:59:01'),(5,'19:12:00','19:29:00'),(6,'17:00:00','17:35:00'),(18,'16:23:00','16:27:00'),(21,'18:03:00','18:23:00'),(22,'21:38:00','21:49:00'),(42,'19:52:00','20:35:00'),(77,'16:02:00','16:39:00'),(103,'02:30:00','10:30:00'),(124,'19:01:00','19:12:00'),(128,'20:00:00','22:02:00'),(130,'15:38:00','16:29:00'),(146,'17:17:00','17:29:00'),(148,'21:55:00','22:10:00'),(149,'16:14:00','16:34:00'),(150,'16:14:00','17:31:00'),(151,'19:48:00','20:20:00'),(153,'15:07:00','15:30:00'),(156,'06:57:00','15:11:00'),(157,'01:35:00','02:18:00'),(160,'11:03:00','16:37:00'),(164,'18:07:00','18:42:00'),(195,'04:12:00','04:33:00'),(197,'22:17:00','22:24:00'),(215,'20:04:00','20:10:00'),(226,'22:09:00','22:19:00'),(228,'21:52:00','22:55:00'),(230,'21:01:00','21:36:00'),(231,'21:04:00','21:36:00'),(256,'19:25:00','19:41:00'),(259,'18:27:00','18:38:00'),(260,'22:00:00','22:13:00'),(261,'21:45:00','22:14:00'),(274,'19:54:00','20:21:00'),(278,'21:27:00','21:37:00'),(300,'19:08:00','22:25:00'),(302,'17:06:00','18:25:00')]:same(n,a,b)
# Explicit local time conversions, retaining precision/chronology flags.
span(32,'2024-01-29T17:25:00Z','2024-01-29T17:27:00Z',basis='timezone_inferred')
span(34,'2024-01-30T03:56:00Z','2024-01-30T04:07:00Z',basis='timezone_inferred');R[34]['flags']+=['approximate_time','source_announcement_before_impact_end'];R[34]['time_complete']=False
span(91,'2024-06-03T12:00:00Z','2024-06-03T16:00:00Z',basis='timezone_inferred');R[91]['flags']+=['source_announcement_before_impact_end']
span(95,'2024-06-04T20:58:00Z','2024-06-05T03:26:00Z',basis='timezone_inferred');R[95]['flags']+=['source_announcement_before_impact_end','external_model_scope_only']
span(182,'2024-10-28T21:00:00Z','2024-10-30T04:15:00Z')
span(253,'2025-02-28T18:00:00Z',X[253]['updates'][0]['display_at'],basis='announcement_proxy',complete=False)
# Stage and service corrections, preserving evidence-supported restoration and recurrence.
proxy(12,3,1)
span(19,X[19]['updates'][2]['display_at'],X[19]['updates'][0]['display_at'],'F',['Claude.ai'],'announcement_proxy',False)
span(19,X[19]['updates'][1]['display_at'],X[19]['updates'][0]['display_at'],'D',['API','Console'],'official_component_interval',False)
proxy(24,17,1)
proxy(26,7,5,'P',['API']);proxy(26,5,0,'D',['API']);proxy(26,4,0,'P',['Claude.ai','Console'])
proxy(43,4,3,'U');proxy(43,3,1,'D')
proxy(59,2,1,'U');proxy(59,1,0,'D')
span(60,X[60]['updates'][1]['display_at'],'2024-03-26T19:48:00Z','P',['Other'],'announcement_proxy',False)
span(84,X[84]['updates'][1]['display_at'],'2024-05-15T00:00:00Z',basis='announcement_proxy',complete=False)
proxy(125,4,1,'U');proxy(125,3,1,'D',['API'])
span(129,'2024-08-08T06:15:10Z','2024-08-08T16:36:00Z','P',['API'],'announcement_proxy',False)
span(129,'2024-08-08T06:15:10Z','2024-08-08T18:31:00.429Z','P',['Claude.ai'],'announcement_proxy',False)
span(129,'2024-08-08T07:08:36.236Z','2024-08-08T17:15:00Z','P',['External'],'announcement_proxy',False)
proxy(129,5,2,'P',['API']);proxy(129,5,1,'P',['Claude.ai'])
proxy(135,5,1)
proxy(136,5,1,'P',['Claude.ai']);proxy(136,4,2,'P',['API'])
proxy(143,5,1,'P',['API']);proxy(143,3,1,'P',['Claude.ai','Console'])
proxy(145,5,4);proxy(145,3,1,'P',['API','Console']);proxy(145,3,0,'P',['Claude.ai'])
proxy(147,5,3);proxy(147,2,1,'P',['API']);# recurrence described on API then all models; other surfaces have no positive component trace
span(158,'2024-09-24T06:00:00Z','2024-09-24T16:02:00Z','P');R[158]['time_complete']=False;R[158]['flags']+=['intermittent_impact_envelope','free_tier_model_restoration_unknown']
proxy(163,4,3);proxy(163,2,1)
proxy(165,6,0,'P',['Claude.ai']);proxy(165,6,1,'P',['API']);proxy(165,2,1,'P',['Console'])
proxy(171,3,2);proxy(171,1,0)
proxy(180,4,0,'P',['Claude.ai']);proxy(180,4,3,'P',['API','Console']);proxy(180,2,1,'P',['API','Console'])
span(183,'2024-10-30T12:38:00Z','2024-10-30T12:51:00Z','P');R[183]['time_complete']=False;R[183]['flags']+=['explicit_window_primary_only','free_tier_model_restoration_unknown']
proxy(202,5,3,'D');span(202,'2024-11-21T03:41:00Z',X[202]['updates'][1]['display_at'],'P',['API'],'announcement_proxy',False)
proxy(210,2,1);proxy(213,4,1)
proxy(267,7,1,'P',['Claude.ai']);proxy(267,5,1,'P',['Console']);proxy(267,5,2,'P',['API'])
proxy(269,5,2,'U',['Claude.ai','Console']);proxy(269,2,1,'F',['Claude.ai','Console','API'])
span(275,'2025-03-29T22:32:00Z','2025-03-29T23:39:00Z','P');proxy(275,2,1,'P');R[275]['time_complete']=False
proxy(301,4,1)
for n in [19,26,43,59,125,129,136,145,147,158,163,165,171,180,183,202,267,269,275]:R[n]['flags'].append('multi_phase')
for n in [77,128,153]:R[n]['flags'].append('source_announcement_before_impact_end')
# Root causes explicitly stated; naming a fix alone is not disclosure of cause.
for n,cause,ui in [(34,'已应用的负载均衡配置错误；回滚后恢复。',0),(82,'维护操作使Claude Instant1.2集群部分不可用。',1),(91,'图片处理bug导致所有输入图片裁剪为正方形。',0),(126,'临时后端服务中断。',1),(129,'基础设施提供商的底层问题；没有披露更细原因。',9),(138,'回复上下文一致性bug；未发生提示泄漏。',1),(171,'指定Sonnet版本的基础设施问题；细节未披露。',3)]:
 R[n]['root_cause_status']='vendor_stated';R[n]['root_cause']=cause;u=X[n]['updates'][ui];R[n]['evidence'].append(dict(quote=u['body'],update_id=u['id'],kind='root_cause',reason=cause))
# Evidence for every explicit interval and scope decision remains attached to full update IDs.
for r,x in zip(R,X):
 if r['time_mode']=='explicit':
  for u in x['updates']:
   if any(z in u['body'] for z in ['UTC','PST','PT','Pacific','restored','return','resolved','normal','recurrence','recovery','unavailable']):
    r['evidence'].append(dict(quote=u['body'],update_id=u['id'],kind='time',reason='用于核对原文窗口、恢复或复发；具体采用边界见intervals与time_note。'))
 if r['groups']==['Unmapped']:r['flags'].append('service_platform_not_disclosed')
 if r['grade']=='unknown' and not {'maintenance','no_user_impact'}&set(r['flags']):r['flags'].append('severity_evidence_insufficient')
 r['review_status']='assessed'
 for ev in r['evidence']:
  assert ev['quote'] in (x['title'] if ev['update_id'] is None else next(u['body'] for u in x['updates'] if u['id']==ev['update_id']))
(P/'early.json').write_text(json.dumps(R,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(Counter(r['grade'] for r in R));print('interval records',sum(bool(r.get('intervals')) for r in R),'none',sum(r['time_mode']=='none' for r in R))
