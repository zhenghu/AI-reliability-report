"""Manual decisions made after reading every assigned update; no keyword grading."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
D=json.load(open(ROOT.parents[1]/'v1.0/review-docket.json'))
G={'rwppv331jlwc':'Claude.ai','0qbwn08sd68x':'Console','k8w3r06qmzrp':'API','yyzkbfz2thpt':'Claude Code','bpp5gb3hpjcl':'Cowork','0scnb50nvy53':'Government'}
NAME={'claude.ai':'Claude.ai','Claude Console (platform.claude.com)':'Console','Claude API (api.anthropic.com)':'API','Claude Code':'Claude Code','Claude Cowork':'Cowork','Claude for Government':'Government'}
# These index decisions are explicit manual review conclusions, not title classifiers.
U={617,630,634,635,638,643,645,662,663,678,680,743,756,757,760,769,786,803,814,816,820,822,831,846,863,879,883,906}
DEG={618,633,676,706,721,730,790,840,881,882,892,894,907,909}
FULL={712,735,738,893}
NONE={621,707,732,826,838}
# Product scope overrides grounded in the complete body rather than broad component checkboxes.
OV={614:['Cowork'],618:['Cowork'],621:['Cowork'],645:['Claude.ai','Console','Claude Code','Cowork'],653:['API'],656:['Cowork','Claude Code'],664:['Claude.ai'],671:['Claude.ai','Claude Code'],676:['Claude.ai'],677:['Claude.ai','Console'],681:['Cowork'],687:['Cowork'],696:['Unmapped'],699:['Claude.ai','Claude Code'],701:['Claude.ai','Console','Claude Code'],702:['Console','API'],703:['Claude.ai'],707:['Claude.ai'],708:['Claude.ai','Console','API','Claude Code','Cowork'],709:['Unmapped'],710:['Claude.ai','Claude Code'],711:['API'],716:['Claude.ai','Cowork'],720:['Claude.ai'],721:['API'],726:['Claude.ai','Console','API','Claude Code','Cowork'],727:['Claude Code'],732:['Claude Code'],735:['Claude.ai','API','Claude Code','Cowork'],738:['Claude.ai','API'],777:['Claude.ai','Console'],825:['Unmapped'],826:['Unmapped'],833:['Claude.ai','Claude Code'],838:['Unmapped'],840:['Claude.ai','Claude Code','Cowork'],842:['Unmapped'],845:['Claude.ai','Claude Code','Cowork'],864:['Claude.ai','Claude Code','Cowork'],868:['Claude.ai','Claude Code','Cowork'],869:['Unmapped'],872:['Unmapped'],892:['Claude Code','Cowork'],893:['Other'],896:['Claude.ai','Console','API','Claude Code','Cowork'],900:['Claude.ai'],903:['Claude.ai','Claude Code'],908:['Claude.ai'],909:['Claude.ai','Console','Other'],910:['Console','API'],918:['Claude.ai']}
S={
614:'Cowork 新建任务页面不能加载，限定功能失效，判 P；组件为空，按标题补归属。',
618:'Cowork 回复未显示，证据是显示退化而非所有任务停止，判 D。',
621:'限定 Windows 桌面版本用户无法使用 Cowork，判 P；仅事后解决更新，开始时刻未知。',
629:'Windows 与旧版 macOS 部分用户桌面无法启动，判 P；客户端更新并非所有用户立即恢复。',
632:'报表端点先报错不可用，恢复后缺历史数据；前段 P、后段 D，推理能力未被证明失效。',
633:'Windows 2.1.59 配置写争用及 JSON/config 损坏，属于数据完整性/客户端退化 D。',
636:'部分新桌面登录失败，限定认证路径，P。',
640:'登录路径故障且部分 API 方法失败，P；API 曾被确认正常后重新受影响，保留分段。',
645:'多个产品仅报错误增加，无失败比例或明确受影响子集，U；Cowork 从标题补入。',
649:'Console 与 admin API 使用量报表特定功能不可用，P；分别保留 API 和 Console 恢复时刻。',
653:'部分 API 连接超时且已连接请求不受影响，P；正文纠正错误的 claude.ai 组件归属。',
654:'桌面文件系统连接器从组织允许列表缺失，限定功能 P；初始修复说明仍需用户恢复允许列表。',
656:'夏令时跳过小时导致部分时区计划任务无限循环；Cowork/Code 桌面限定用户功能失效 P。',
657:'部分用户登录失败并有性能减慢，判 P（同时存在 D）；API 明确不受影响。',
659:'Sonnet 4.6 指定模型错误为产品 P；另有 Claude.ai 一分钟事件但症状等级未知，分开保留。',
664:'免费 Claude.ai 用户的 Sonnet 4.6 错误，P；以正文限定用户群，排除最初过宽组件。',
665:'限定免费 Claude.ai 用户/指定模型错误，P。',
667:'限定免费 Claude.ai 用户/指定模型错误，P。',
671:'Code 登录/退出失败支持 P；Claude.ai 仅笼统错误，保留为 U 区间。',
672:'跨产品认证请求失败，限定路径，P；正文给实际跨午夜窗口。',
676:'文本流结束后额外等待约 5 秒，D；API 明确不受影响，按追溯起点统计。',
677:'Claude.ai/Console 身份认证失败，P；并未证明已登录功能全部停止。',
678:'实际窗口明确，但只说明 Claude.ai 错误率上升，无影响比例，U。',
680:'错误率无比例或范围，U；resolved 同时标 major_outage 是状态冲突，不能延长。',
681:'Cowork 会话连接重置错误，特定连接路径失败 P；重启可缓解不代表全体同时恢复。',
684:'部分 MCP 调用失败，P；resolved 时组件仍 P，以解决消息封顶。',
685:'Opus 4.6/短暂 Sonnet 4.6 子模型错误，产品 P；13:40 与16:30两次恢复说法不一致。',
687:'Dispatch 回复通道停止而普通 Cowork 正常，限定功能 P；归入 Cowork。',
690:'部分桌面连接器不可用，P；允许列表仍需手动补回。',
691:'Haiku 4.5 请求错误并伴随延迟，指定模型子集 P，同时存在 D。',
694:'桌面连接失败、网站不受影响，客户端子集 P。',
696:'两个指定模型错误支持 P，但 most product surfaces 未枚举具体产品，归属未知。',
697:'Claude.ai 登录/对话/语音及 Code 等登录路径失败，P；按实际窗口并保留明确组件。',
699:'Claude.ai/Code 认证及部分功能错误，P；不能把官方 critical 当全产品中断。',
701:'Claude.ai、Console 与 Code 登录路径错误，P；正文未证明推理 API 不可用。',
702:'Console/admin API 工作区创建失败而推理正常，限定功能 P。',
703:'部分用户访问网站/桌面失败，P；明确实际窗口。',
705:'某些连接器错误，限定功能 P。',
706:'Vaults 性能退化 D；无完全功能不可用证据。',
707:'部分未登录用户的部分分享链接不可达，P；只有日期范围，不能精确填午夜。',
708:'非 Opus 4.6 模型错误、Opus 4.6 不在影响内，产品 P；政府组件一直正常排除。',
709:'电子邮件登录通道失败，P；未指明具体产品，归属未知。',
710:'实际影响是 Claude.ai/Code 登录，P；官方全中断标志不扩大语义。',
711:'usage/analytics admin API 间歇 503，特定端点失败 P，排除未受影响组件。',
712:'混合事件：Claude.ai/Console 明确 down 阶段 F，Code 仅登录 P、已登录可用；API恢复文字时间冲突，早段 U。',
714:'特定桌面版本部分用户 Cowork 无法启动，P。',
715:'Console Vault 添加凭证功能失败，P。',
716:'Claude.ai/Cowork 上传 Google Drive 功能失败，P；其余组件一直正常。',
719:'部分文件上传失败，限定功能及请求子集 P。',
720:'Claude.ai MCP 应用不可用，限定功能 P；按正文已解决时刻截断。',
721:'结构化输出特定语法质量下降，D；非该功能请求不受影响。',
725:'Console 注册流程错误，P。',
727:'Claude Code 2.1.120 恢复旧会话时崩溃，限定客户端及操作 P；排除复制进来的其他产品组件。',
730:'标题明确 slower responses 支持 D；未量化错误范围，D 仅表示已确认的性能退化。',
731:'Claude.ai 计费相关路径错误，限定功能 P。',
732:'Code Review 间歇无法启动会话，P；仅已解决公告，无可定位开始。',
735:'Claude.ai 不可访问支持 F；API/Code 认证路径仅 P，Cowork 只列组件不足以证明全产品 F。',
738:'标题明确 Claude.ai 和 API 不可用，F；其他产品仅组件标签不扩展全中断判断。',
744:'GitHub 源 IP 限制组织在基础设施 IP 变化后连接失败，用户子集/功能 P。',
746:'恢复后限 Opus4.1 与 Opus4.6 Fast，P；初始跨模型错误范围未明，早段 U。',
747:'文件操作路径错误，限定功能 P。',
750:'特定 Code 版本 Windows IDE 扩展无法加载，P。',
752:'Code 网页端部分中断，产品子集 P。',
753:'Vaults/凭证路径错误，Console 子功能 P。',
759:'明确部分模型请求失败，P，模型依次恢复不改变产品层面 P。',
763:'Claude.ai/Code 登录失败并伴随延迟，P；使用已报告实际窗口。',
770:'先 Opus/Sonnet、后 Opus/Haiku 请求错误，P；保留中间恢复间隙。',
773:'Code 的 Slack 集成请求错误，限定渠道 P。',
777:'计费/订阅管理失败而 Chat/API 接入不受影响，Claude.ai/Console 子功能 P。',
787:'Code 安全审查/代码审查/例程/部分网页会话异常，限定功能 P。',
789:'五个模型先后恢复，产品 P；使用供应商最终逐模型时间最大值，非较早恢复公告。',
790:'仅报告 Opus4.8 degraded service 无具体失败描述，D 表示已确认退化。',
792:'正文明确 some Claude Models 的请求错误，产品 P。',
799:'Code Desktop 模型选择器无法选择 Fable，限定模型/渠道 P。',
804:'主动暂停 Mythos 5 与 Fable 5 两个模型，产品 P；单列策略性暂停敏感性。',
807:'第一阶段多个模型约10%错误、第二阶段 Opus4.8约10%，均P；跨阶段并集连续。',
814:'仅 service disruption，未说明用户失败比例或具体功能，U；实际窗口可定位。',
825:'Opus4.8 Fast 特定模型模式错误，P；没有产品组件或平台正文，归属未知。',
826:'Opus4.8 指定模型错误 P；只有已缓解记录无开始，归属未知。',
832:'Fable 5 确认错误支持后阶段 P；此前 several models 无受影响子集，早阶段 U。',
833:'Code OAuth 登录不可用支持 P；Claude.ai仅笼统错误且组件F不充分，U。',
834:'Claude Tag GitHub 操作被拒，Code 子功能 P。',
836:'部分模型请求错误 P；两次明确 success rates normal 分段，不能将中间监控全算受损。',
838:'MCP 授权请求不能发送，子功能 P；缺具体产品和可定位开始。',
839:'部分模型请求错误，P；最终实际窗口覆盖中间短暂恢复措辞，不声称精确连续失败。',
840:'远程会话/审查/文档创建性能问题，D；正文补 Code/Cowork/Claude.ai 归属。',
842:'Opus4.5/Sonnet4.5 指定模型错误 P；实际窗口清楚，但具体产品未知。',
845:'容器创建影响文档创建/Code/Cowork远程等子功能，P。',
849:'Enterprise SSO 登录失败，限定用户/认证路径 P。',
850:'部分用户/模型错误，P；按最终实际窗口而非较早恢复公告。',
854:'Fable5 错误要求使用量余额，指定模型访问失败，P；客户端可能需重启。',
856:'部分 Max 用户被错误提示用量点数，限定账户/模型访问 P；首次记录已在监控且无开始时刻。',
860:'Haiku4.5/Opus4.8 两个指定模型错误，P。',
864:'文档创建、网页/远程Code和Cowork等功能中断，产品子功能P，不能将组件F扩大为全产品。',
868:'文档/远程会话等限定功能中断，P；正文补Claude Code。',
869:'特定Microsoft Office加载项无法访问，P；未列产品组件，不硬映射Cowork或API。',
872:'Sonnet4.6/5 错误，P；约10分钟和约恢复时刻允许近似回推，不标精确。',
874:'特定命名模型及其他模型错误，未明确影响比例，保留 P 仅作为已明确模型子集的事件级判断。',
880:'早期跨模型范围不明 U；后仅特定模型P；再次跨所有模型和后续调查时序另保留U，不把最后调查遗漏。',
881:'Opus4.8 明确性能退化 D，无请求失败细节。',
882:'Sonnet5 明确性能退化 D，无请求失败细节。',
884:'正文 Sonnet5 错误率恢复，指定模型请求失败 P。',
887:'部分用户登录及模型请求失败，明确用户子集 P。',
888:'命名模型错误请求，产品子集 P，标题 degraded 不自动变D。',
890:'初始 multiple models 范围不明 U；后明确 Fable5 请求错误 P。',
892:'Code 网页与 Cowork Remote 等性能退化 D，正文补 Code 归属。',
893:'状态网站证书无效导致不可访问，仅辅助站点 Other 的 F，不纳入 Claude 核心产品。',
894:'正文只明确性能退化 D；官方 P 不足以判断具体不可用请求。',
896:'认证路径失败支持 Claude.ai/Code/Cowork P；API/Console仅性能退化 D，不能把组件F当全中断。',
897:'Opus5请求错误 P 后Sonnet5退化描述 D；按服务阶段分别记。',
898:'Opus5等模型错误，产品P；最后窗口是Opus5，其他模型具体时刻不清。',
900:'Google连接器子功能错误而核心功能正常，Claude.ai P，正文缩小过宽组件。',
903:'Claude.ai/Code订阅登录失败 P；桌面后续只称potential，未额外生成确定影响区间。',
904:'访问/订阅登录错误，限定认证路径 P。',
905:'上游云问题导致部分 Code网页/Cowork 会话启动失败或中断，P。',
906:'仅聊天错误上升，无用户/请求比例，不能证明整产品或明确子集不可用，U。',
907:'Slack/网页Code/CodeReview 性能退化 D；以追溯窗口统计。',
908:'Office365 集成路径错误，Claude.ai 子功能 P。',
909:'辅助文档、Console、Office365 性能退化 D；推理和API明确未受影响。',
910:'余额零用户购点到账延迟导致部分API误拒，P；购买受影响窗口不等同于请求影响结束，保留残余影响代理。',
914:'Windows更新导致本地命令不可运行，多数聊天和文件功能仍工作，Cowork P；真实开始仅日期。',
915:'部分美国中西部入口客户延迟及请求超时，P（兼D）；不能扩大成所有API失败。',
918:'Google Play 新订阅等交互失败，Android/订阅路径P，归Claude.ai。'
}

def evidence(r,quote=None,kind='severity',reason=None):
 if quote is None: return {'quote':r['title'],'update_id':None,'kind':kind,'reason':reason or '原始标题明确所评估症状与范围。'}
 for u in r['updates']:
  if quote in u['body']: return {'quote':quote,'update_id':u['id'],'kind':kind,'reason':reason or '供应商更新直接支持判断。'}
 raise ValueError((r['n'],quote))
R={}
for r in D[614:920]:
 n=r['n'];g='unknown' if n in U else 'degraded_performance' if n in DEG else 'full_outage' if n in FULL else 'partial_outage'
 groups=OV.get(n) or sorted(set(NAME[x] for x in r['components'] if x in NAME)|set(G[x['code']] for u in r['updates'] for x in (u['affected_components'] or []) if x['code'] in G)) or ['Unmapped']
 summary=S.get(n,('标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。' if g=='unknown' else '指定模型的请求错误属于产品内模型子集失效，判 P；未证明整个产品不可用。'))
 R[n]={'n':n,'incident_id':r['id'],'grade':g,'groups':groups,'summary':summary,'evidence':[evidence(r)],'time_mode':'none' if n in NONE else 'component_or_proxy','time_note':'优先使用历史组件恢复/重开时序；缺少实际起止时以明确标注的公告时间作为代理，监控本身不等于恢复。','time_complete':False,'root_cause_status':'not_disclosed','root_cause':'','flags':[]}
 if n in NONE:R[n]['time_note']='仅日期、事后已解决记录或无可定位开始，不能从公告时间制造完整影响区间。';R[n]['flags'].append('unpositioned_impact')
 if groups==['Unmapped']:R[n]['flags'].append('product_scope_unknown')
 if n not in U and n not in DEG and n not in FULL and n not in S:R[n]['flags'].append('model_subset_product_partial')
 if g=='unknown':R[n]['flags'].append('severity_unknown_after_full_review')

def note(n,q,kind='severity',reason=None):R[n]['evidence'].append(evidence(D[n],q,kind,reason))
def interval(n,a,b,g=None,groups=None,basis='explicit_impact',complete=True):
 R[n]['time_mode']='explicit';R[n]['time_complete']=complete
 R[n].setdefault('intervals',[]).append({'start_at':a,'end_at':b,'severity':g or R[n]['grade'],'service_groups':groups or R[n]['groups'],'time_basis':basis})
 R[n]['time_note']='以正文供应商影响窗口为准；分段时逐段保留不同严重性/服务范围。' if complete else '混合实际边界与公告/组件代理，或约数/部分时间轴；不声称完整精确影响窗口。'
def window(n,day,a,b,complete=True,basis='explicit_impact'):
 interval(n,day+'T'+a+':00Z',day+'T'+b+':00Z',complete=complete,basis=basis)
# Explicit complete windows independently checked against supplied update body.
for n,day,a,b in [
(639,'2026-02-28','17:50','18:12'),(651,'2026-03-04','14:45','14:50'),(655,'2026-03-07','13:35','14:44'),(657,'2026-03-11','14:17','17:11'),(673,'2026-03-19','15:23','15:42'),(674,'2026-03-19','15:53','16:14'),(678,'2026-03-23','16:10','16:26'),(697,'2026-04-06','15:00','16:30'),(699,'2026-04-07','14:32','15:12'),(701,'2026-04-08','17:25','17:44'),(703,'2026-04-08','23:22','23:50'),(710,'2026-04-13','15:31','16:19'),(713,'2026-04-16','06:03','07:26'),(722,'2026-04-23','15:23','15:35'),(726,'2026-04-25','01:24','01:59'),(734,'2026-04-28','13:22','13:39'),(736,'2026-04-28','23:25','23:33'),(762,'2026-05-18','21:47','22:18'),(763,'2026-05-19','04:34','04:42'),(772,'2026-05-25','06:30','10:30'),(777,'2026-05-28','18:27','19:05'),(779,'2026-05-29','18:16','18:42'),(789,'2026-06-05','15:08','17:29'),(794,'2026-06-08','16:56','17:47'),(795,'2026-06-08','18:35','19:30'),(796,'2026-06-08','21:01','21:27'),(797,'2026-06-08','22:06','22:28'),(798,'2026-06-09','02:50','03:30'),(803,'2026-06-11','16:42','17:03'),(807,'2026-06-16','17:23','19:20'),(809,'2026-06-16','20:45','20:58'),(811,'2026-06-17','04:59','05:41'),(814,'2026-06-18','06:55','07:40'),(822,'2026-06-23','14:08','15:33'),(839,'2026-07-08','17:45','19:40'),(842,'2026-07-10','13:00','15:15'),(850,'2026-07-16','18:30','22:15'),(863,'2026-07-21','15:28','16:26'),(894,'2026-08-14','20:14','20:38'),(898,'2026-08-18','16:11','18:23'),(902,'2026-08-24','04:50','07:36'),(903,'2026-08-24','16:02','16:08'),(904,'2026-08-24','20:00','20:08'),(907,'2026-08-31','16:55','19:16'),(911,'2026-09-02','21:05','21:19'),(916,'2026-09-11','13:57','14:20'),(919,'2026-09-22','00:50','02:10')]:window(n,day,a,b)
interval(672,'2026-03-18T23:59:00Z','2026-03-19T00:30:00Z')
interval(676,'2026-03-20T20:00:00Z','2026-03-22T13:02:00Z',complete=False);R[676]['flags'].append('approximate_start')
interval(692,'2026-03-31T17:45:00Z','2026-04-01T05:52:00Z')
interval(721,'2026-04-22T16:10:00Z','2026-04-23T01:59:00Z')
interval(892,'2026-08-13T23:42:00Z','2026-08-14T00:50:00Z')
interval(895,'2026-08-14T20:00:00Z','2026-08-15T00:11:00Z')
for n,day,a,b in [(696,'2026-04-04','17:09','17:31'),(702,'2026-04-08','16:15','19:30'),(709,'2026-04-10','22:46','23:52'),(791,'2026-06-06','18:12','18:55'),(808,'2026-06-16','19:41','19:53'),(872,'2026-07-25','17:57','18:07')]:
 window(n,day,a,b,complete=False,basis='timezone_inferred' if n!=702 else 'explicit_impact');R[n]['flags'].append('approximate_or_timezone_inferred_window')
for a,b in [('09:53','09:57'),('10:01','10:06'),('10:34','10:36')]:window(724,'2026-04-24',a,b)
# Correct known ending before announcement; the starting boundary remains an announcement proxy.
for n,day,end in [(623,'2026-02-23','09:30'),(624,'2026-02-23','11:26'),(626,'2026-02-24','07:27'),(627,'2026-02-24','13:10'),(652,'2026-03-04','16:08'),(884,'2026-08-03','15:20'),(913,'2026-09-03','16:16')]:
 first=min(u['display_at'] for u in D[n]['updates']);interval(n,first,day+'T'+end+':00Z',basis='announcement_proxy',complete=False)
# Timing contradictory statements: don't silently choose PT, UTC, or a plausible typo correction.
for n in [688,700,733,737,739,800,876,877,878,879]:
 R[n]['time_mode']='none';R[n]['time_note']='供应商原文 PT/PST 与 UTC 换算或小时/时区标签相互矛盾；无法唯一定位，排除确定时间计算，保留原公告供不确定性分析。';R[n]['flags'].append('conflicting_source_times')
# Read and confirmed prior explicit cases.
for n in [699,710,721]:R[n]['use_prior_explicit']=True
# Range with actual start/end and transition from unavailable endpoint to stale data.
interval(632,'2026-02-26T02:00:00Z','2026-02-27T03:04:54.747Z','partial_outage',basis='announcement_proxy',complete=False)
interval(632,'2026-02-27T03:04:54.747Z','2026-02-27T06:20:00Z','degraded_performance',basis='announcement_proxy',complete=False)
R[632]['flags']+=['multi_phase','approximate_start']
# Small independent Claude.ai event grade unknown in same report as known model errors.
window(659,'2026-03-12','15:30','15:44')
interval(659,'2026-03-12T15:27:00Z','2026-03-12T15:28:00Z','unknown',['Claude.ai'],'timezone_inferred',False)
interval(660,'2026-03-12T16:27:00Z','2026-03-12T18:00:19.000Z',basis='announcement_proxy',complete=False)
# Correct service-specific mixed cases, avoiding whole-span worst-grade substitution.
interval(671,'2026-03-18T15:16:38.307Z','2026-03-18T16:05:10.845Z','unknown',['Claude.ai'],'announcement_proxy',False)
interval(671,'2026-03-18T15:19:28.479Z','2026-03-18T16:05:10.845Z','partial_outage',['Claude Code'],'announcement_proxy',False)
interval(677,'2026-03-22T18:31:58.133Z','2026-03-22T18:43:45.062Z','partial_outage',['Console'],'announcement_proxy',False)
interval(677,'2026-03-22T18:33:13.739Z','2026-03-22T18:43:45.062Z','partial_outage',['Claude.ai'],'announcement_proxy',False)
for groups,a,b,g in [(['Claude.ai','Console'],'14:53:02.097','15:40:22.000','unknown'),(['Claude.ai','Console'],'15:40:22.000','16:29:45.676','full_outage'),(['Claude.ai','Console'],'16:29:45.676','17:42:57.229','partial_outage'),(['Claude Code'],'14:53:02.097','15:20:03.212','unknown'),(['Claude Code'],'15:20:03.212','17:42:57.229','partial_outage'),(['API'],'14:53:02.097','15:20:03.212','unknown')]:
 interval(712,'2026-04-15T'+a+'Z','2026-04-15T'+b+'Z',g,groups,'announcement_proxy',False)
R[712]['flags']+=['multi_phase','conflicting_source_times','early_severity_unknown']
interval(720,'2026-04-23T00:41:43.361Z','2026-04-23T00:57:59.215Z',basis='announcement_proxy',complete=False)
interval(735,'2026-04-28T17:34:00Z','2026-04-28T18:52:00Z','full_outage',['Claude.ai'])
interval(735,'2026-04-28T17:34:00Z','2026-04-28T18:52:00Z','partial_outage',['API','Claude Code'])
interval(735,'2026-04-28T17:41:55.480Z','2026-04-28T18:59:47.057Z','unknown',['Cowork'],'official_component_interval',False)
R[735]['flags'].append('mixed_service_severity')
interval(746,'2026-05-08T09:49:14.232Z','2026-05-08T10:22:00Z','unknown',basis='announcement_proxy',complete=False)
interval(746,'2026-05-08T10:22:00Z','2026-05-08T11:32:47.301Z','partial_outage',['Claude.ai','Console','API','Claude Code','Cowork'],'announcement_proxy',False)
interval(832,'2026-07-06T07:36:23.654Z','2026-07-06T08:45:51.570Z','unknown',basis='announcement_proxy',complete=False)
interval(832,'2026-07-06T08:45:51.570Z','2026-07-06T09:13:37.323Z','partial_outage',basis='announcement_proxy',complete=False)
interval(833,'2026-07-06T19:18:49.331Z','2026-07-06T19:46:02.528Z','unknown',['Claude.ai'],'announcement_proxy',False)
interval(833,'2026-07-06T19:28:17.401Z','2026-07-06T19:46:02.528Z','partial_outage',['Claude Code'],'announcement_proxy',False)
for a,b in [('20:02:33.495','20:28:40.504'),('21:47:40.990','23:19:36.067')]:interval(836,'2026-07-07T'+a+'Z','2026-07-07T'+b+'Z',basis='announcement_proxy',complete=False)
R[836]['flags'].append('reopened_preserved')
interval(890,'2026-08-12T13:50:28.580Z','2026-08-12T16:10:01.523Z','unknown',basis='announcement_proxy',complete=False)
interval(890,'2026-08-12T16:10:01.523Z','2026-08-12T18:07:11.547Z','partial_outage',basis='announcement_proxy',complete=False)
interval(896,'2026-08-16T21:58:57.096Z','2026-08-16T22:34:39.037Z','partial_outage',['Claude.ai','Claude Code','Cowork'],'announcement_proxy',False)
interval(896,'2026-08-16T22:02:03.684Z','2026-08-16T22:34:39.037Z','degraded_performance',['Console','API'],'announcement_proxy',False)
interval(897,'2026-08-17T13:56:41.229Z','2026-08-17T14:25:27.706Z','partial_outage',basis='announcement_proxy',complete=False)
interval(897,'2026-08-17T14:25:27.706Z','2026-08-17T14:39:58.009Z','degraded_performance',basis='announcement_proxy',complete=False)
interval(910,'2026-09-01T12:10:00Z','2026-09-02T01:24:22.251Z','partial_outage',basis='announcement_proxy',complete=False)
R[910]['flags'].append('purchase_window_not_request_recovery')
R[804]['flags'].append('intentional_model_access_suspension')
R[914]['flags'].append('start_date_only_proxy_understates')
R[856]['time_mode']='none';R[856]['time_note']='首次公告已说明可重启且状态 operational，缺实际开始；不能把后续监控8小时当故障。';R[856]['flags'].append('already_mitigated_first_notice')
# Additional per-record body evidence selected manually.
QS={621:'Some Windows users on v1.1.3918',629:'a subset of Windows users and macOS users on older macOS releases',632:'Impact: Feb 26 ~02:00 to Feb 27 06:20 UTC.',633:'significant write contention for the .claude.json global config file',636:'Some new logins to the Claude Desktop app were not working.',640:'We have discovered that some API methods are not working',649:'the admin API and some reporting screens in the Console',653:'Requests that successfully connect are unaffected.',654:'Users may need to re-add the Filesystem connector',656:'affected by an infinite loop',657:'Some users may be unable to log in',664:'only impacting free Claude.ai users.',665:'only free Claude.ai users',667:'only free Claude.ai users',671:'Claude Code login/logout actions are also affected',672:'when trying to authenticate',676:'"hang" for around 5 seconds',677:'Logins have returned to normal',681:'connection errors which occur during Claude Cowork sessions',684:'some MCP calls',685:'our error rate has returned to the baseline',687:'standard Cowork sessions, which are unaffected.',690:'some Claude.ai connectors becoming unavailable',694:'the Claude.ai website is unaffected',696:'across most product surfaces',697:'errors when attempting to login, engaging with voice mode, or completing chats',699:'Claude.ai and Claude Code authentication',701:'/login attempts via Claude Code',702:'Other functionality including inference and the messages API is not impacted',703:'Some users experienced an error',705:'Certain connectors',707:'some users who were not signed in',708:'models other than Claude Opus 4.6',709:'Email login was broken',710:'primarily affecting login',711:'Intermittent 503 errors',712:'Claude.ai and Platform are down.',714:'v1.3036.0 release',716:'uploading documents to Google Drive',719:'Some users will see their uploads failing',720:'We have resolved the issue impacting MCP Apps',721:'returned with reduced quality',725:'attempting to sign up',727:'when resuming a prior session',732:"intermittently wasn't starting sessions",735:'preventing users from reaching Claude.ai',744:'A recent infrastructure change altered the IP addresses',746:'remaining impact is limited to Claude Opus 4.1 and Fast Mode',750:'prevents the IDE extension from loading on Windows',759:'both Sonnet 4.6 and Opus 4.7 return to normal',763:'errors when attempting to login',770:'some additional errors impacting Claude Opus 4.7 and Haiku 4.5',777:'Chat and API access are not affected.',787:'some Claude Code web sessions',789:'Recovery times per model were:',792:'some Claude Models',799:'issues with selecting Claude Fable',807:'an average error rate of 10%',832:'Fable 5 has now also started returning errors.',833:'inability to log-in via Claude.ai OAuth for Claude Code',834:'GitHub operations denied',836:'success rates return to normal',838:'unable to send authorized requests to MCP servers.',839:'some requests',840:'a performance issue',845:'document creation in claude.ai',850:'some users experienced elevated errors',854:'erroneous requirement for usage credits',856:'Some Claude Code Max plan users were incorrectly prompted',860:'Claude Haiku 4.5 and Opus 4.8',864:'outage affecting features',868:'outage affecting features',869:'issues accessing the add-in functionality',872:'approximately 10 minutes',880:'All models except Opus 5 have recovered.',884:'error rates on Claude Sonnet 5',887:'some users experiencing issues',888:'Claude Mythos 5, Claude Fable 5, and Claude Opus 5, Claude Sonnet 5',890:'errors are primarily impacting Claude Fable 5',892:'degraded performance in Claude Code on the Web',893:'invalid certificate',894:'reports of degraded performance',896:'users authenticating to claude.ai, Claude Code, and Claude Cowork',897:'Claude Sonnet 5 is degraded.',898:'The issue affecting Claude Opus 5',900:'Core functionality is not affected.',903:'At this time, this issue has been resolved',904:'including logging in via subscriptions for Claude Code',905:'Some sessions may fail to start or disconnect mid-task',907:'degraded performance affecting Claude in Slack',908:'Claude for Microsoft Office 365',909:'Core inference and the API are not impacted.',910:"some requests to the Claude API receiving 'credit balance is too low' errors erroneously",914:'For most users, chat and file reading and editing still work.',915:'some request timeouts',918:'Google has confirmed an issue with Google Play'}
for n,q in QS.items():note(n,q)
# Each timing decision includes its exact body containing the relevant stated boundaries.
for n,r in R.items():
 if r['time_mode']=='explicit' or 'conflicting_source_times' in r['flags']:
  us=[u for u in D[n]['updates'] if any(x in u['body'] for x in ['UTC','PDT','PST',' PT','Impact:'])]
  for u in us:
   r['evidence'].append({'quote':u['body'],'update_id':u['id'],'kind':'time','reason':'原始时间说明，供复核实际边界、约数或时区矛盾。'})
# Root cause is vendor stated only when mechanism/dependency actually stated.
CAUSE={632:('internal data service issue','内部数据服务问题影响使用量报表。'),633:('significant write contention for the .claude.json global config file','Windows 版本 2.1.59 配置文件写入争用。'),653:('network degradation at an upstream peering point','上游对等互联节点网络退化。'),656:('it couldn’t resolve them and got stuck','夏令时跳过时段任务解析陷入无限循环。'),690:('Affected connectors were removed from organization allowlists','连接器从组织允许列表被移除。'),727:('version 2.1.120 that causes a crash when resuming a prior session','Code 2.1.120 恢复旧会话崩溃。'),744:('A recent infrastructure change altered the IP addresses','基础设施变更改变连接GitHub出口IP，与组织允许列表不符。'),854:('erroneous requirement for usage credits','错误的Fable5使用量额度要求。'),893:('invalid certificate','状态页无效证书。'),905:('an issue with an upstream cloud provider','上游云提供商问题（未披露更具体机制）。'),914:('A Windows update released September 8','9月8日Windows更新令Cowork工作区不能访问本机磁盘。'),918:('Google has confirmed an issue with Google Play','Google Play供应商服务问题（未披露更具体机制）。')}
for n,(q,s) in CAUSE.items():R[n]['root_cause_status']='vendor_stated';R[n]['root_cause']=s;note(n,q,'root_cause')
# Explicit correction notes to support aggregation flags.
for n in [640,642,644,646,668,682,724,770,836,851,862]:R[n]['flags'].append('reopening_or_recurrence_reviewed')
for n in [617,625,630,632,641,685,689,712,718,735,746,770,786,822,832,833,836,854,861,863,875,878,879,880,890,896,897]:R[n]['flags'].append('official_multiphase_reviewed')
for n in [685]:
 R[n]['time_mode']='none';R[n]['time_note']='13:40 已回基线但最终又称16:30才缓解；没有解释是否重开，不能唯一确定真实终点。';R[n]['flags'].append('conflicting_recovery_boundaries')
# Preserve a recurrence with no component re-opening after 10:23 on July 30.
for a,b,g in [('05:57:43.629','06:26:26.771','unknown'),('06:26:26.771','08:33:00.000','partial_outage'),('08:33:00.000','09:58:00.000','unknown'),('10:23:09.989','10:48:56.631','partial_outage')]:interval(880,'2026-07-30T'+a+'Z','2026-07-30T'+b+'Z',g,basis='announcement_proxy',complete=False)
R[880]['flags'].append('additional_investigation_after_component_recovery')
# March 2 explicit API correction and later API recurrence; Government remains unverified.
for groups,a,b,g in [(['Claude.ai'],'11:49:20.921','15:25:23.846','partial_outage'),(['Console','Claude Code'],'12:06:11.458','15:25:23.846','partial_outage'),(['API'],'13:37:01.682','15:25:23.846','partial_outage'),(['Government'],'12:06:11.458','12:21:24.244','unknown')]:
 interval(640,'2026-03-02T'+a+'Z','2026-03-02T'+b+'Z',g,groups,'announcement_proxy',False)
R[640]['flags'].append('API_initial_impact_retracted_by_body')
note(640,'the Claude API is working as intended','service')
# June 10 text confirms near-normal rather than fully recovered after operational state.
interval(801,'2026-06-10T13:06:47.699Z','2026-06-10T17:21:33.620Z','partial_outage',basis='announcement_proxy',complete=False)
R[801]['flags'].append('body_overrides_premature_operational_component')
note(801,'success rates recover to close to normal operating levels','time')
R[682]['flags'].append('recurrence_gap_not_locatable_proxy_includes_possible_gap')
R[903]['flags'].append('unconfirmed_potential_desktop_issue_not_counted')
# Unknown stage labels and scoped model errors remain explicit, not automated upgrades.
# Validate exact quotes, unique IDs, and time interval positivity before delivery.
from datetime import datetime
for n,r in R.items():
 for e in r['evidence']:
  assert e['quote'] in (D[n]['title'] if e['update_id'] is None else next(u['body'] for u in D[n]['updates'] if u['id']==e['update_id']))
 for p in r.get('intervals',[]):assert datetime.fromisoformat(p['start_at'].replace('Z','+00:00'))<datetime.fromisoformat(p['end_at'].replace('Z','+00:00'))
assert list(R)==list(range(614,920))
(ROOT/'recent.json').write_text(json.dumps(list(R.values()),ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(Counter(r['grade'] for r in R.values()));print(Counter(r['time_mode'] for r in R.values()))
