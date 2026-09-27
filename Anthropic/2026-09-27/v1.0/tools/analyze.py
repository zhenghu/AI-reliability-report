"""Build auditable CSV and official-state reference estimates; no network calls.
Unreviewed semantic judgments stay needs_review, never silently become reviewed.
"""
import sys,json,csv,hashlib,re,collections,copy
from pathlib import Path
from datetime import datetime,timedelta,timezone
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'.agents/skills/incident-research/scripts'))
from core import normalize_record,normalized_updates,lifecycle_windows,union_seconds,utc,iso,js,digest,write_json,validate_csv,FIELDS,JSON_FIELDS,highest
S=json.loads((ROOT/'snapshot.json').read_text());END=utc(S['cutoff_utc']);M=S['components'];BY={e['raw']['id']:e for e in S['records']}
GRADES={'major_outage':'full_outage','partial_outage':'partial_outage','degraded_performance':'degraded_performance'}
# Explicit assessment decisions made from original announcement/update text. U is unknown, not normal.
REV={}
def review(ids,grade,summary,groups=None):
 for i in ids.split():REV[i]={'grade':grade,'summary':summary,**({'groups':groups} if groups else {})}
review('85cf5bgslwtw cpssy4797smx','partial_outage','正文称多数 API 流量受影响，非所有请求；只有持续时长，没有定位起止。',['API'])
review('cbnwvjjmr26h','full_outage','正文说明模型暂时离线；仅按当时 API 服务范围判断。',['API'])
review('wxv8qktfv3sn m2fy7ttnc5lt zchm8l8spmrv 18jfgfwmyy25 rt1kx84m7jvw','partial_outage','正文或标题明确 partial outage；限定部分请求受影响。',['API'])
review('d3pkgr12bgq4','partial_outage','claude-v1.0 请求失败，正文明确其他模型仍服务；在 API 产品范围按 Partial。',['API'])
review('3667134hg62q','partial_outage','两个指定模型不可用；不提升为整个 API Full。')
review('ddcqt95wb9g2 mzbrvjdyg58h','degraded_performance','正文只支持性能/服务退化，未证明全部不可用。')
review('q7r96llr464k 306rf7bb75mm 1k1dv2q3vhb6','partial_outage','正文明确仅部分请求或间歇请求报错；整体产品按 Partial。')
review('3ssrcy8kwsx9 198dzcv9ptcq lhr41x13htg5 49cmvxrrk228 kfs1w8vywj9d shhpbrjb160c','full_outage','公告明确所指 Claude.ai 聊天或入口不可用；影响范围不扩展至 API。',['Claude.ai'])
review('cm416m2m0p83 kr7vv24cr0sn','full_outage','正文明确 Claude.ai/Console 无法登录和访问，API 不受影响。',['Claude.ai','Console'])
review('3j3zbrx1cfbt rjjg3fzd2spp','full_outage','公告明确 Claude.ai、Console、API 不可用；未给真实起止时采用标记代理。',['Claude.ai','Console','API'])
review('2gf1jpyty350','full_outage','公告明确 claude.ai 与 API 不可用；不扩展至其他产品。',['Claude.ai','API'])
review('vc4jcltdwzg8','full_outage','公告标题明确 Claude.ai 与 Console outage；记录范围仅这两个入口。',['Claude.ai','Console'])
review('svk9pskgp576','full_outage','公告标题声明 API Outage；实际影响时间未明确，保留代理。',['API'])
review('5ww9gdw94j3c','partial_outage','后续正文明确部分 Claude.ai 用户不能登录、Console 已恢复、API 未受影响。',['Claude.ai','Console'])
review('kn7mvrgb0c8m','partial_outage','图片和文件上传不可用，但文本请求仍可能成功；GCP 为供应商说明的依赖故障。',['API','Claude.ai','Console'])
review('7542z654hwl8','full_outage','正文明确 21:36–21:52 无法访问 Claude.ai/Console；其他时段是部分请求和 Artifacts 功能故障。',['Claude.ai','Console'])
review('krdqz4n56w9w','degraded_performance','聊天保存失败属于数据完整性退化，不等于所有聊天请求均失败。',['Claude.ai'])
review('2f7kwfs03p6v','partial_outage','无法新建会话是所述功能不可用，未证明已有会话和所有入口不可用。',['Claude.ai'])
review('d8v3zr02my00','partial_outage','正文明确受影响请求比例较小，不能因红色标签判整个 API Full。',['API'])
review('124yr07585k9 6jd2m42f8mld k5yvlfppnp4f','partial_outage','正文支持 Claude.ai/Claude Code 登录或部分功能失败，未证明所有调用路径不可用。',['Claude.ai','Claude Code'])
review('f4wqmj8rhjsc','partial_outage','登录/认证路径受影响，未证明已登录用户全部失去服务。',['Claude.ai','Console'])
review('4qsb0fp16tpb','partial_outage','公告列举文档创建、Cowork Remote 和 Code 等功能故障，非所有模型推理停机。')
review('qtxnlg9yrwqv 5xh2zd6jrklj t4trmtzzdk2w tgzm3mf45wzc bf1hsq5gbm9b wlysnq540b32','unknown','仅错误率升高或指定模型 outage，缺少失败比例和受影响对象完整性证据；不把 critical 自动升级成 Full。')
review('5dcd2h34gbcg sn3y911gkt0r 7svmbgb2b28x mqxbmckr6bbx r20t009skp4b s0c6w5gmlcq3 9g6qpr72ttbr pr6yx3bfr172 jbhf20wjmzrf vcynh9cf33xp q2kg8n613kr3 qt14v73myyy5 p0svq4j6sk04 xg2v4m4nc40n','unknown','公告证明发生错误或服务异常，但不能确定全量/部分失败边界；官方标签保留作参考，不视为完成语义分级。')
review('s9w82lp9dcn9','partial_outage','两个指定模型访问被主动暂停，其他模型未受影响；服务产品层面为 Partial。公告生命周期仅作暂停代理；另给排除此项敏感性结果。')
review('r1pqn1kb4hvk','partial_outage','Windows Cowork 的本地命令失效；正文明确多数用户仍可聊天和读写文件。',['Cowork'])
review('72f99lh1cj2c h26lykctfnsz 4q9qw2g0nlcb kygj9sjs8dxr v8vxwtcbmhkn t6v0k97s0802 vyw1vz0h6c1x','degraded_performance','正文描述输出质量、图像处理或上下文质量退化，不等同于服务不可用。')
review('dccfckxw59q6','degraded_performance','单一模型尾延迟增加；正文明确恢复，但不是整体 API 停机。',['API'])
review('5pr1d63fdjml vgdmw7cp6xdg s9yk4l23th4d fqzlkqnhk3l3','partial_outage','正文明确特定功能、长请求、少量请求或免费用户受影响，产品范围按 Partial。')
review('6rrnsb1y0kbn','partial_outage','仅部分 App Store 购买者未得到计划权限，影响开始早于公告，不能把公告周期当真实全窗口。',['Claude.ai'])
review('zr0lqy5rpx9w','degraded_performance','项目知识库可见性问题，未证明核心推理不可用。',['Claude.ai'])
review('htd54cj3t4d9','degraded_performance','组织内部删除后的 Artifacts 仍可访问，属于数据状态退化，不是整体停机。',['Claude.ai'])
review('pqpgkf52p3tg','partial_outage','仅特定夏令时地区且设有定时任务的客户端受影响；厂商说明时间计算死循环。',['Claude.ai','Claude Code','Cowork'])
review('jbc4ybjk83c6 yc7mr2gvl914','partial_outage','限定连接器或 Office 插件功能不可用，不代表整体产品不可用。')
review('61k4r5c1xzfj whtx5sq6d3fg qkx8wwyfdlh7 bybj2w3097hm','unknown','官网/文档站故障与核心推理服务不同，放在辅助网站组，不能回填成 API 停机。',['Other'])
review('mzyhcbn140fg','degraded_performance','社交账号安全事件；公告明确 Anthropic 服务未受影响，不能纳入产品可用性。',['Other'])
review('ysbg73gy3ctm','full_outage','正文明确 Opus 在 Vertex 全部不可访问；只归第三方 Vertex，不归第一方 API。',['External'])
# UTC windows individually checked against the original text. No time-only duration is positioned artificially.
TIMES={
'cbnwvjjmr26h':('2023-04-28T19:04:00Z','2023-04-28T19:06:00Z'),
'wxv8qktfv3sn':('2023-04-29T10:17:00Z','2023-04-29T10:18:00Z'),
'm2fy7ttnc5lt':('2023-04-30T08:58:47Z','2023-04-30T08:59:01Z'),
'd3pkgr12bgq4':('2023-05-03T19:12:00Z','2023-05-03T19:29:00Z'),
'zchm8l8spmrv':('2023-06-02T17:00:00Z','2023-06-02T17:35:00Z'),
'q7r96llr464k':('2023-08-12T18:03:00Z','2023-08-12T18:23:00Z'),
'mzbrvjdyg58h':('2023-08-22T21:38:00Z','2023-08-22T21:49:00Z'),
'198dzcv9ptcq':('2024-09-12T16:14:00Z','2024-09-12T17:31:00Z'),
'cm416m2m0p83':('2024-11-15T22:17:00Z','2024-11-15T22:24:00Z'),
'lhr41x13htg5':('2025-01-10T22:09:00Z','2025-01-10T22:19:00Z'),
'kr7vv24cr0sn':('2025-05-27T22:11:00Z','2025-05-28T00:24:00Z'),
'd8v3zr02my00':('2026-02-03T17:52:00Z','2026-02-03T17:56:00Z'),
'124yr07585k9':('2026-04-07T14:32:00Z','2026-04-07T15:12:00Z'),
'6jd2m42f8mld':('2026-04-13T15:31:00Z','2026-04-13T16:19:00Z'),
'4q9qw2g0nlcb':('2025-07-08T08:45:00Z','2025-07-10T02:00:00Z'),
't6v0k97s0802':('2026-04-22T16:10:00Z','2026-04-23T01:59:00Z')}
review('fwj5yn2lmbrc h4bygm7vgqkj','unknown','结案正文明确未影响用户请求；属于告警/调查记录，不能记入产品故障时长。')
# Explicit windows with only elevated errors remain unknown in semantic grade; used only in state reference series.
REFERENCE_TIMES={
'7g1qpkyz5gxh':('2026-09-22T00:50:00Z','2026-09-22T02:10:00Z'),
't33dncr5ydvl':('2026-09-11T13:57:00Z','2026-09-11T14:20:00Z'),
'ls6bn1x81m0w':('2026-09-02T21:05:00Z','2026-09-02T21:19:00Z'),
'sn3y911gkt0r':('2024-09-11T21:55:00Z','2024-09-11T22:10:00Z'),
'7svmbgb2b28x':('2024-11-14T04:12:00Z','2024-11-14T04:33:00Z'),
'qtxnlg9yrwqv':('2025-03-14T21:45:00Z','2025-03-14T22:14:00Z'),
'r20t009skp4b':('2025-03-29T19:54:00Z','2025-03-29T20:21:00Z'),
's0c6w5gmlcq3':('2025-04-03T21:27:00Z','2025-04-03T21:37:00Z'),
'bf1hsq5gbm9b':('2026-03-19T15:53:00Z','2026-03-19T16:14:00Z'),
'jbhf20wjmzrf':('2026-06-23T14:08:00Z','2026-06-23T15:33:00Z'),
'vcynh9cf33xp':('2026-07-21T15:28:00Z','2026-07-21T16:26:00Z'),
'q2kg8n613kr3':('2026-07-29T19:45:00Z','2026-07-29T21:26:00Z'),
'fvj2fgqrchsj':('2026-03-31T17:45:00Z','2026-04-01T05:52:00Z')}
NO_TIME=set('fwj5yn2lmbrc h4bygm7vgqkj 85cf5bgslwtw cpssy4797smx 72f99lh1cj2c h26lykctfnsz kygj9sjs8dxr 6rrnsb1y0kbn mzyhcbn140fg'.split())
CORE=['Claude.ai','API','Console','Claude Code','Cowork','Government']
def mapping(r):
 groups=sorted({M[c['id']]['group'] for c in r['components'] if c['id'] in M})
 return groups or ['Unmapped']
def phase(a,b,sev,groups,basis,**extra):
 return dict(start_at=iso(a),end_at=iso(b),severity=sev,service_groups=groups,time_basis=basis,right_censored=b==END,**extra)
def official_phases(r,groups):
 us=normalized_updates(r,'statuspage');us=[u for u in us if utc(u['at'])<=END];out=[];pending={}
 for u in us:
  t=utc(u['at'])
  for c in (u['component_statuses'] or []):
   cid=c.get('code',c.get('id'));grade=GRADES.get(c.get('new_status'))
   if cid in pending:
    a,old,uid=pending.pop(cid)
    if t>a:out.append(phase(a,t,old,[M.get(cid,{}).get('group','Unmapped')],'official_component_interval',component_id=cid,start_update_id=uid,end_update_id=u['id']))
   if grade:pending[cid]=(t,grade,u['id'])
  if u['status'] in ['resolved','completed','postmortem']:
   for cid,(a,grade,uid) in pending.items():
    if t>a:out.append(phase(a,t,grade,[M.get(cid,{}).get('group','Unmapped')],'official_component_interval',component_id=cid,start_update_id=uid,end_update_id=u['id'],end_is_resolution_proxy=True))
   pending={}
 for cid,(a,grade,uid) in pending.items():
  if END>a:out.append(phase(a,END,grade,[M.get(cid,{}).get('group','Unmapped')],'official_component_interval',component_id=cid,start_update_id=uid))
 if not out:
  grade={'critical':'full_outage','major':'partial_outage','minor':'degraded_performance'}.get(r['impact'])
  if grade:
   out=[phase(a,b,grade,groups,'announcement_proxy') for a,b in lifecycle_windows(us,END)]
 return out
rows=[];reference=[];reviewlog=[]
for entry in S['records']:
 r=entry['raw'];i=r['id'];row=normalize_record(entry,S);groups=mapping(r);us=normalized_updates(r,'statuspage');alltext=r['name']+'\n'+'\n'.join(u['body'] for u in us)
 rev=REV.get(i);groups=rev.get('groups',groups) if rev else groups
 # Explicit third-party-only titles never belong to first-party API; keep all source components untouched.
 if ('vertex' in r['name'].lower() or 'bedrock' in r['name'].lower()) and not any(x in r['name'].lower() for x in ['api,','claude.ai']):groups=['External']
 baseline=official_phases(r,groups)
 if groups in [['Other'],['External']]:
  for x in baseline:x['service_groups']=groups
 # Official component traces retained separately, including all original status transitions.
 row['official_intervals_json']={'derivation':'Reconstructed transition intervals, not vendor provided interval objects','transitions':[{'update_id':u['id'],'at':u['at'],'affected_components':u['component_statuses']} for u in us],'reference_intervals':copy.deepcopy(baseline)}
 row['service_groups_json']=groups;row['assessed_severity']='unknown';row['severity_basis']='semantic_assessment_pending';row['analysis_summary']='保留原始公告和官方历史状态；尚未完成逐阶段语义复核，官方标签不代表已确认的产品 Full/Partial。'
 row['impact_intervals_json']=[];row['review_status']='needs_review';row['time_complete']=False
 row['quality_flags_json']+=['semantic_classification_not_completed','reference_estimates_separate_from_assessed_intervals']
 evidence=[]
 if rev:
  row['assessed_severity']=rev['grade'];row['review_status']='assessed';row['severity_basis']='evidence_backed_assessment';row['analysis_summary']=rev['summary']
  row['quality_flags_json'].remove('semantic_classification_not_completed')
  # Evidence points to original title and each update, preserving full context; quotes are short.
  evidence=[{'kind':'summary','source_url':entry['source_urls'][0],'quote':r['name'],'reason':rev['summary']}]
  for u in us:
   if u['body']:evidence.append({'kind':'summary','source_url':entry['source_urls'][0],'update_id':u['id'],'quote':u['body'][:120],'reason':'判断依据完整正文见 updates_json 和 raw_incident_json'})
  if rev['grade']!='unknown' and i not in NO_TIME:
   ps=[]
   if i in TIMES:
    a,b=map(utc,TIMES[i]);ps=[phase(a,b,rev['grade'],groups,'explicit_impact')];row['time_complete']=True
   elif baseline:
    ps=copy.deepcopy(baseline)
    for x in ps:x['severity']=rev['grade'];x['service_groups']=groups
   else:
    ps=[phase(a,b,rev['grade'],groups,'announcement_proxy') for a,b in lifecycle_windows(us,END)]
   row['impact_intervals_json']=ps
  if i=='7542z654hwl8':
   a=utc('2025-07-09T00:11:32.504Z');b=utc('2025-07-09T21:36:00Z');c=utc('2025-07-09T21:52:00Z');d=utc('2025-07-09T23:09:08.008Z')
   row['impact_intervals_json']=[phase(a,b,'partial_outage',['Claude.ai'],'announcement_proxy'),phase(b,c,'full_outage',['Claude.ai','Console'],'explicit_impact'),phase(c,d,'partial_outage',['Claude.ai'],'announcement_proxy')]
  row['quality_flags_json'].append('focused_semantic_review_actual_timing_may_remain_incomplete')
  reviewlog.append({'incident_id':i,'source_record_sha256':digest(r),**rev,'evidence':evidence,'intervals':row['impact_intervals_json']})
 # Correct clear timing errors in reference baseline without pretending severity has been assessed.
 ref=copy.deepcopy(baseline)
 if i in NO_TIME:ref=[]
 elif i in TIMES or i in REFERENCE_TIMES:
  bounds=TIMES.get(i,REFERENCE_TIMES.get(i));grade=highest(x['severity'] for x in ref)
  if rev and rev['grade']!='unknown':grade=rev['grade']
  if grade!='unknown':ref=[phase(utc(bounds[0]),utc(bounds[1]),grade,groups,'explicit_impact')]
 elif rev and rev['grade']!='unknown' and row['impact_intervals_json']:ref=copy.deepcopy(row['impact_intervals_json'])
 if i=='7542z654hwl8':ref=copy.deepcopy(row['impact_intervals_json'])
 if i=='s9w82lp9dcn9':row['quality_flags_json'].append('intentional_model_access_suspension');row['severity_scope']='specified_models_unavailable_product_partial'
 if i=='f00h6l76tsjs':row['quality_flags_json'].append('body_PT_UTC_conversion_and_update_timestamp_conflict')
 if i=='mp4tfl9fwdjc':row['quality_flags_json'].append('body_PT_UTC_duration_conflict')
 if i=='0dv5d8qb9gy2':row['quality_flags_json'].append('body_month_conflicts_with_announcement_month')
 if i=='vtx2xkfwrk1l':row['quality_flags_json'].append('PST_label_during_daylight_saving_time_not_assumed')
 if rev:
  # Store traceable evidence for every assessment axis. Original full updates remain in CSV.
  evidence.append({'kind':'severity','source_url':entry['source_urls'][0],'quote':r['name'],'reason':rev['summary'],'supporting_update_ids':[u['id'] for u in us]})
  evidence.append({'kind':'service','source_url':entry['source_urls'][0],'quote':r['name'],'reason':'服务范围取正文核验或原始 components；映射未证明产品上线日期。','component_ids':[c['id'] for c in r['components']]})
  if row['impact_intervals_json']:
   for u in us:
    if u['body']:
     k=re.search(r'\d{1,2}:\d{2}',u['body']);q=u['body'][max(0,k.start()-25):k.start()+100] if k else u['body'][:100]
     evidence.append({'kind':'time','source_url':entry['source_urls'][0],'update_id':u['id'],'quote':q,'published_at':u['at'],'reason':'明确正文窗口优先；其余仅用有标记的状态/公告边界。'})
   for x in row['impact_intervals_json']:x['evidence_indices']=[j for j,e in enumerate(evidence) if e['kind']=='time']
  causes={'3667134hg62q':'负载均衡配置错误；撤销变更后恢复。','kn7mvrgb0c8m':'GCP 故障影响相关依赖服务。','pqpgkf52p3tg':'夏令时跳过的小时触发定时任务定位死循环。','4q9qw2g0nlcb':'推理栈发布造成输出质量退化；回滚修复。','r1pqn1kb4hvk':'Windows 更新导致工作区无法访问本地驱动器。','kfs1w8vywj9d':'有缺陷的边缘代理发布；已回滚。'}
  if i in causes:
   row['root_cause']=causes[i];row['root_cause_status']='vendor_stated'
   for u in us:
    if any(t in u['body'].lower() for t in ['due to','root cause','caused','update released','faulty']):
     evidence.append({'kind':'root_cause','source_url':entry['source_urls'][0],'update_id':u['id'],'quote':u['body'][:180],'reason':causes[i]})
  else:row['root_cause_status']='not_assessed'
 row['evidence_json']={'items':evidence,'reference_method':'Official historical component transitions first; mapped incident impact + announcement lifecycle otherwise; focused corrections recorded. This is a reference estimate, not a complete assessed timeline.','reference_intervals':ref}
 row['components_json']=[{'id':c['id'],'name':c['name'],'group':M.get(c['id'],{}).get('group','Unmapped')} for c in r['components']]
 ps=row['impact_intervals_json'];row['impact_start_at_utc']=min((x['start_at'] for x in ps),default=None);row['impact_end_at_utc']=max((x['end_at'] for x in ps),default=None)
 for key,allowed in [('impact_seconds',list(GRADES.values())),('known_full_seconds',['full_outage']),('known_full_partial_seconds',['full_outage','partial_outage']),('known_all_seconds',list(GRADES.values()))]:row[key]=union_seconds(ps,allowed) if ps else None
 row['time_basis']=';'.join(sorted({x['time_basis'] for x in ps})) or 'unknown';row['right_censored']=any(x['right_censored'] for x in ps)
 row['quality_flags_json']=sorted(set(row['quality_flags_json'])-{'unknown_impact_time','unknown_assessed_severity','impact_timeline_not_fully_verified'})
 if not ps:row['quality_flags_json'].append('unknown_assessed_impact_time')
 if row['assessed_severity']=='unknown':row['quality_flags_json'].append('unknown_assessed_severity')
 if not row['time_complete']:row['quality_flags_json'].append('impact_timeline_not_fully_verified')
 row['analysis_version']='anthropic-state-reference-v1.0';rows.append(row)
 reference.append({'id':i,'record_type':row['record_type'],'published_at':row['published_at_utc'],'groups':groups,'intervals':ref,'review_status':row['review_status'],'official_severity':row['official_severity']})
# Explicit observation starts reflect status-component creation/coverage, not product release or first incident.
starts={'Overall':'2023-07-11T00:00:00Z','Claude.ai':'2023-07-11T00:00:00Z','API':'2023-07-11T00:00:00Z','Console':'2023-07-11T00:00:00Z','Claude Code':'2025-05-23T00:00:00Z','Cowork':'2026-04-02T00:00:00Z','Government':'2026-02-18T00:00:00Z'}
windows={'company_id':'anthropic','overall_group':'Overall','service_windows':{g:{'start':a,'end':S['cutoff_utc']} for g,a in starts.items()},'basis':'Core three components use official start_date; newer components use first full UTC day after created_at to avoid pre-creation backfill. Not product launch dates. Overall includes components only after their own observation start.'}
def intervals_for(rec,group,a,b):
 out=[]
 for x in rec['intervals']:
  gs=set(x['service_groups'])&set(CORE)
  for g in gs:
   if group not in ['Overall',g]:continue
   aa=max(utc(x['start_at']),utc(starts[g]),a);bb=min(utc(x['end_at']),b)
   if aa<bb:out.append(dict(x,start_at=iso(aa),end_at=iso(bb)))
 return out
def calc(group,a,b,exclude=False,source=reference):
 included=[r for r in source if r['record_type']=='incident' and not(exclude and r['id']=='s9w82lp9dcn9')]
 relevant=[r for r in included if (set(r['groups'])&set(CORE) if group=='Overall' else group in r['groups']) or any((set(x['service_groups'])&set(CORE) if group=='Overall' else group in x['service_groups']) for x in r['intervals'])]
 phases=[x for r in relevant for x in intervals_for(r,group,a,b)];den=(b-a).total_seconds()
 count=[r for r in relevant if a<=utc(r['published_at'])<b]
 hrs=[union_seconds(phases,allowed,a,b)/3600 for allowed in [['full_outage'],['full_outage','partial_outage'],list(GRADES.values())]]
 return {'year':a.year,'group':group,'window_start':iso(a),'window_end':iso(b),'denominator_seconds':den,'incident_count':len(count),'unknown_time_count':sum(not r['intervals'] for r in count),'full_hours':hrs[0],'full_partial_hours':hrs[1],'all_hours':hrs[2],'availability_full':1-hrs[0]*3600/den,'availability_full_partial':1-hrs[1]*3600/den,'availability_all':1-hrs[2]*3600/den,'count_basis':'published_at_utc','metric_scope':'any_observed_core_component','estimate':True,'series':'official_state_reference_with_focused_corrections','exclude_intentional_suspension':exclude}
annual=[];matched=[]
for g,start in starts.items():
 for year in range(utc(start).year,END.year+1):
  a=max(utc(start),datetime(year,1,1,tzinfo=timezone.utc));b=min(END,datetime(year+1,1,1,tzinfo=timezone.utc))
  annual.append(calc(g,a,b))
  if g in ['Overall','Claude.ai','API','Console'] and year>=2024:matched.append(calc(g,datetime(year,1,1,tzinfo=timezone.utc),END.replace(year=year)))
full=[calc(g,utc(a),END) for g,a in starts.items()]
sensitivity=[calc(g,max(utc(a),datetime(2026,1,1,tzinfo=timezone.utc)),END,True) for g,a in starts.items()]
write_json(ROOT/'analysis.json',{'schema_version':1,'records':reviewlog,'review_policy':'Focused semantic assessments only; remaining records needs_review; no automated claim of full review.'})
write_json(ROOT/'reference-intervals.json',reference);write_json(ROOT/'service_windows.json',windows)
write_json(ROOT/'trend_data.json',{'schema_version':1,'cutoff_utc':S['cutoff_utc'],'annual':annual,'matched_windows':matched,'provenance':{'series':'official_state_reference_with_focused_corrections','NOT_full_semantic_assessment':True,'source':'incidents.csv evidence_json.reference_intervals','csv_schema':'incident-csv-v1','company_id':'anthropic'}})
write_json(ROOT/'summary-data.json',{'full_period':full,'sensitivity_2026_excluding_suspension':sensitivity})
# Write exactly 48 contract columns, then parse and validate the saved result.
out=ROOT/'incidents.csv'
with out.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
 for original in rows:
  row=dict(original);escaped=[]
  for k,v in row.items():
   if k in JSON_FIELDS:row[k]=js(v)
   elif isinstance(v,str) and v.lstrip().startswith(('=','+','-','@','\t','\r')):row[k]="'"+v;escaped.append(k)
  row['spreadsheet_escaped_fields_json']=js(escaped);w.writerow(row)
validation=validate_csv(out)
validation.update(csv_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),coverage=S['coverage'],review_counts=dict(collections.Counter(r['review_status'] for r in rows)),assessed_exact_timeline_count=sum(r['time_complete'] for r in rows),reference_unknown_time_count=sum(r['record_type']=='incident' and not ref['intervals'] for r,ref in zip(rows,reference)),reference_timing_counts=dict(collections.Counter(x['time_basis'] for r in reference for x in r['intervals'])),checks={'BOM':out.read_bytes().startswith(b'\xef\xbb\xbf'),'column_count':len(FIELDS),'history_ids_equal_snapshot_ids':set(json.loads((ROOT/'history-index.json').read_text())['ids'])==set(BY)})
write_json(ROOT/'incidents.validation.json',validation)
print(json.dumps(validation,ensure_ascii=False,indent=2));print('ANNUAL',json.dumps([r for r in annual if r['year']==2026],ensure_ascii=False))
