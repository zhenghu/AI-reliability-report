"""Offline normalization and interval unions after agent review of all announcements.
Flashduty is retained as generic native JSON, not mislabelled Statuspage.
"""
import json,csv,hashlib,re,collections
from pathlib import Path
from datetime import datetime,timezone
from collect import ROOT,CUTOFF,iso,stamp,API,BASE
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def union(xs):
 out=[]
 for a,b in sorted(xs):
  if b<=a:continue
  if out and a<=out[-1][1]:out[-1][1]=max(out[-1][1],b)
  else:out.append([a,b])
 return out
def seconds(xs):return sum(b-a for a,b in union(xs))
GRADE={'full_outage':'full_outage','partial_outage':'partial_outage','degraded':'degraded_performance'}
RANK={'unknown':0,'degraded_performance':1,'partial_outage':2,'full_outage':3}
def highest(xs):return max(xs,key=lambda x:RANK[x],default='unknown')
PAGE=json.loads((ROOT/'page.json').read_text())['data']['page']
COMP={x['component_id']:x for x in PAGE['components']}
GROUP={k:('API' if 'API' in v['name'] else 'Upload' if 'Upload' in v['name'] else 'Search' if 'Search' in v['name'] else 'Chat') for k,v in COMP.items()}
GROUP.update({'01KY4ND2PN1CCNW2MFT5VW713H':'Chat','01KY4ND2PNJ6MFA4VJ0DSN6M2J':'Chat'})
LABEL={'Overall':'整体（任一纳入应用受影响）','API':'DeepSeek API（历史综合服务）','Chat':'对话服务（网页／APP）','Upload':'上传文件服务','Search':'搜索服务'}
WINDOW={g:min(c['available_since_seconds'] for k,c in COMP.items() if GROUP[k]==g) for g in ['API','Chat','Upload','Search']};WINDOW['Overall']=min(WINDOW.values())
RS=sorted(json.loads((ROOT/'records.json').read_text()),key=lambda r:min(u['at_seconds'] for u in r['updates']))
OI=json.loads((ROOT/'official-impacts.json').read_text())
# Explicit per-record semantic decisions made after reading the full update histories.
MODEL_IDS={4369272769582287,4298904025405287,3876691560339287,3806322816161287,3735954071983287,3665585327806287,3524847839450287,3384110351095287,3313741606917287,3243372862740287,2680422909318287,2187841700075287,2117472955897287,1835997979186287}
PROXY_IDS={4580379002115287:'full_outage',3173004118562287:'full_outage',3806322816161287:'partial_outage'}
NO_TIME={4087797792872287:'full_outage',3665585327806287:'partial_outage'}
rows=[];reviews=[]
for raw in RS:
 id=raw['change_id'];url=BASE+f'/incidents/{id}';updates=sorted(raw['updates'],key=lambda u:u['at_seconds']);rh=digest(raw)
 evidence=[{'kind':'summary','quote':raw['title'],'source_url':url,'raw_field':'title'}]
 for i,u in enumerate(raw['updates']):evidence.append({'kind':'update','quote':u['description'],'source_url':url,'update_id':u.get('update_id',''),'raw_field':f'updates[{i}].description','at_utc':iso(u['at_seconds'])})
 flags=['flashduty_native_json','publication_time_first_update_proxy','status_intervals_not_measured_request_uptime']
 if any(not u.get('update_id') for u in updates):flags.append('legacy_update_id_missing')
 if any(u['at_seconds']<raw['start_at_seconds'] for u in updates):flags.append('updates_precede_displayed_start')
 if raw.get('is_retrospective'):flags.append('retrospective')
 if any(GROUP.get(c.get('component_id'))=='API' for c in raw.get('affected_components',[])):flags.append('historical_component_names_may_be_backfilled')
 end=min(stamp(CUTOFF),raw.get('close_at_seconds') or stamp(CUTOFF));candidates=[];state={}
 # Changes are per-component deltas. Same-status updates still split phases for semantic review.
 for u in updates:
  t=u['at_seconds']
  if t>=stamp(CUTOFF):continue
  for c in u.get('component_changes',[]):
   cid=c['component_id']
   if cid in state:
    prev,at,src=state[cid]
    if prev in GRADE and t>at:candidates.append((at,t,cid,prev,src))
   state[cid]=(c['status'],t,u)
  if u['status'] in ['resolved','completed']:
   for cid,(prev,at,src) in list(state.items()):
    if prev in GRADE and t>at:candidates.append((at,t,cid,prev,src))
    state[cid]=('operational',t,u)
 for cid,(prev,at,src) in state.items():
  if prev in GRADE and end>at:candidates.append((at,end,cid,prev,src))
 intervals=[];semantic=[];reasons=[]
 for a,b,cid,code,src in candidates:
  if cid not in GROUP:
   if 'unnamed_legacy_component_preserved_not_attributed' not in flags:flags.append('unnamed_legacy_component_preserved_not_attributed')
   continue
  g=GROUP[cid];grade=GRADE[code];basis='official_color_fallback';reason='正文为处理状态模板或范围不足；采用此组件此阶段的官方状态代码。'
  # Named model or feature failure is partial at the application scope; preserve D phases.
  if id in MODEL_IDS and grade!='degraded_performance':grade='partial_outage';basis='semantic_assessment';reason='明确限定特定模型／Coder 路径，按综合 API／对话应用范围为局部不可用。'
  if cid in ['01KY4ND2PN1CCNW2MFT5VW713H','01KY4ND2PNJ6MFA4VJ0DSN6M2J'] and grade=='full_outage':grade='partial_outage';basis='semantic_assessment';reason='专家／识图模式是对话应用子功能，不能提升为整个对话服务 Full。'
  if id==1695260490831287:grade='degraded_performance';basis='semantic_assessment';reason='正文明确请求延迟增加。'
  if id==2539685420963287 and g=='API' and a>=1737948751:
   grade='partial_outage';basis='semantic_assessment';reason='R1 API 正常而 V3 仍在恢复；至明确恢复前按模型子集不可用。'
  if id==1976735467542287:
   if a>=1747133715:continue
   b=min(b,1747133715)
   if a>=1747132285:grade='partial_outage';basis='semantic_assessment';reason='对话已恢复，但历史读取与重新登录失败；以正文覆盖仍为红色的组件。'
  if id==1624891746653287 and a>=1754925161:grade='partial_outage';basis='semantic_assessment';reason='明确大部分服务恢复，仍有部分服务受影响。'
  if id==2328579188430287 and g=='Chat' and a in [1737994759,1738055230]:
   grade='partial_outage';basis='semantic_assessment';reason='已注册用户可登录、注册受限制；只校正有明确陈述的阶段。'
  if id==6768454253287:grade='partial_outage';basis='semantic_assessment';reason='公告明确 API 部分不可用。'
  if id==6741259174287 and grade!='degraded_performance':grade='partial_outage';basis='semantic_assessment';reason='搜索功能不可用；旧记录绑定对话组件，不回填后来新增的独立搜索组件。'
  if id==6927183076287 and grade=='full_outage':grade='partial_outage';basis='semantic_assessment';reason='公告明确网页/API部分中断，未证明应用整体完全不可用。'
  idx=next(i for i,u in enumerate(raw['updates']) if u is src)
  ci=next(i for i,c in enumerate(src['component_changes']) if c['component_id']==cid)
  se={'source_url':API+f'/change/info?change_id={id}','raw_field':f'updates[{idx}].component_changes[{ci}].status','raw_value':code,'mapped_grade':GRADE[code],'update_id':src.get('update_id',''),'component_id':cid,'reason':reason}
  intervals.append({'start_at':iso(a),'end_at':iso(min(b,stamp(CUTOFF))),'severity':grade,'service_groups':[g],'component_id':cid,'time_basis':'official_component_status','severity_basis':basis,'severity_evidence':se,'right_censored':b>stamp(CUTOFF),'source_record_sha256':rh})
  if basis=='semantic_assessment':semantic.append(grade);reasons.append(reason)
 if id==2398947932608287:
  cid=next(k for k,v in GROUP.items() if v=='Chat')
  # An operational component color at 09:xx did not restore the login/sign-up path.
  intervals=[x for x in intervals if not(x['service_groups']==['Chat'] and stamp(x['start_at'])>=1737982547)]
  intervals.append({'start_at':iso(1737982547),'end_at':iso(1737984749),'severity':'partial_outage','service_groups':['Chat'],'component_id':cid,'time_basis':'official_component_status_with_semantic_correction','severity_basis':'semantic_assessment','severity_evidence':{'source_url':url,'quote':'The account service still has some problem. You may not login or sign up at this time.','reason':'对话恢复不代表登录/注册路径恢复。'},'right_censored':False,'source_record_sha256':rh});semantic.append('partial_outage');reasons.append('对话恢复后账号路径仍失败，补回绿色组件造成的时间缺口。')
 if id in PROXY_IDS:
  grade=PROXY_IDS[id];semantic.append(grade);flags.append('announcement_lifecycle_proxy')
  reasons.append('历史组件阶段缺失；使用官方 start/close 字段作为有标记的公告活动期代理，不能认定真实起止。')
  for g in ['API','Chat']:intervals.append({'start_at':iso(raw['start_at_seconds']),'end_at':iso(end),'severity':grade,'service_groups':[g],'time_basis':'announcement_lifecycle_proxy','severity_basis':'semantic_assessment','severity_evidence':{'source_url':url,'quote':raw['title'],'reason':'命名服务不可用；Coder 限于特定模型，归应用局部故障。'},'right_censored':False,'source_record_sha256':rh})
 if id in NO_TIME:
  intervals=[];semantic.append(NO_TIME[id]);flags+=['unknown_impact_time','resolved_only_one_second_artifact'];reasons.append('只有结案更新且 start/close 相差一秒；不把迁移数据的一秒当作真实故障时长。')
 # API is an application group. One model component's full outage is partial here.
 api_ids={k for k,g in GROUP.items() if g=='API'};original=list(intervals);scoped=[]
 for x in original:
  if x['service_groups']!=['API'] or x['severity']!='full_outage' or 'component_id' not in x:scoped.append(x);continue
  a,b=stamp(x['start_at']),stamp(x['end_at'])
  peers=[z for z in original if z['service_groups']==['API'] and z['severity']=='full_outage' and 'component_id' in z]
  cuts=sorted({a,b}|{max(a,min(b,stamp(z[k]))) for z in peers for k in ['start_at','end_at']})
  for sa,sb in zip(cuts,cuts[1:]):
   z=dict(x);z['start_at']=iso(sa);z['end_at']=iso(sb)
   active={q['component_id'] for q in peers if stamp(q['start_at'])<=sa and stamp(q['end_at'])>=sb}
   if active!=api_ids:
    z['severity']='partial_outage';z['severity_basis']='semantic_assessment';z['severity_evidence']={**x['severity_evidence'],'reason':'只有 API 的部分模型组件处于 Full，按综合 API 应用范围降为 Partial。'};semantic.append('partial_outage');reasons.append('单一 API 模型组件 Full 不升级为整个 API Full。')
   scoped.append(z)
 intervals=scoped
 if raw['type']=='maintenance':intervals=[];flags.append('maintenance_excluded')
 official=highest(GRADE[c['status']] for u in updates for c in u.get('component_changes',[]) if c['status'] in GRADE)
 fallback=any(x['severity_basis']=='official_color_fallback' for x in intervals)
 if fallback:flags.append('official_color_fallback')
 if id==6800501267287:flags.append('late_resolved_updates_excluded');reasons.append('首次恢复后的两次结案更新不延长影响时间。')
 if id in [2328579188430287,2258210444252287]:flags.append('long_status_episode');reasons.append('多日状态公告，不能理解为所有请求持续失败；报告另列排除场景。')
 groups=sorted(set(g for x in intervals for g in x['service_groups']))
 if raw['type']=='maintenance':groups=sorted({GROUP[c['component_id']] for c in raw.get('affected_components',[]) if c['component_id'] in GROUP})
 if id in NO_TIME:groups=['API','Chat']
 if not groups and ('API' in raw['title'] or '网页' in raw['title']):groups=['API','Chat']
 severity=highest([x['severity'] for x in intervals]+semantic)
 basis='semantic_plus_official_color_fallback' if semantic and fallback else 'semantic_assessment' if semantic else 'official_color_fallback' if fallback else 'not_applicable_maintenance'
 times=[(stamp(x['start_at']),stamp(x['end_at'])) for x in intervals]
 known=[seconds([(stamp(x['start_at']),stamp(x['end_at'])) for x in intervals if RANK[x['severity']]>=rank]) if intervals else '' for rank in [3,2,1]]
 cause='';cause_status='not_disclosed'
 if id==2328579188430287:cause='厂商称大规模恶意攻击导致注册限制；不将其扩展为全部阶段的已确认根因。';cause_status='vendor_stated'
 if id==2047104211719287:cause='厂商称系统升级过程中导致故障。';cause_status='vendor_stated'
 if raw['type']=='maintenance':cause_status='not_assessed'
 summary='；'.join(dict.fromkeys(reasons)) or '已逐条读取全部更新；未提供可独立确定失败范围的细节，依历史组件状态逐阶段定级。'
 if raw['type']=='maintenance':summary='计划维护记录；保留原始更新并从故障可用性时长排除。'
 assessment={'semantic_grade':highest(semantic),'semantic_summary':summary,'source_record_sha256':rh,'read_update_count':len(updates),'official_fallback':fallback,'scope':'application_groups; API combines historical model component IDs','native_platform':'Flashduty','time_complete':False}
 resolved=[u['at_seconds'] for u in updates if u['status'] in ['resolved','completed']]
 meta=json.loads((ROOT/'raw'/f'detail-{id}.json.meta.json').read_text())
 row=dict(schema_version='incident-csv-v1',company_id='deepseek',company_name='DeepSeek',status_page_url=BASE,source_platform='generic',incident_id=str(id),incident_title=raw['title'],record_type=raw['type'],incident_status=raw['status'],published_at_utc=iso(min(u['at_seconds'] for u in updates)),first_update_at_utc=iso(min(u['at_seconds'] for u in updates)),first_resolved_at_utc=iso(min(resolved)) if resolved else '',last_update_at_utc=iso(max(u['at_seconds'] for u in updates)),official_severity=official,official_severity_codes_json=sorted(set(c['status'] for u in updates for c in u.get('component_changes',[]))),assessed_severity=severity,severity_basis=basis,severity_scope='; '.join(LABEL[g] for g in groups),service_groups_json=groups,components_json=raw.get('affected_components',[]),impact_start_at_utc=iso(min(a for a,b in times)) if times else '',impact_end_at_utc=iso(max(b for a,b in times)) if times else '',impact_seconds=known[2],known_full_seconds=known[0],known_full_partial_seconds=known[1],known_all_seconds=known[2],time_basis='announcement_lifecycle_proxy' if id in PROXY_IDS else 'official_component_status' if intervals else 'unknown',time_complete=False,right_censored=any(x['right_censored'] for x in intervals),review_status='assessed',analysis_summary=summary,root_cause=cause,root_cause_status=cause_status,evidence_json={'items':evidence,'assessment':assessment},updates_json=raw['updates'],impact_intervals_json=intervals,official_intervals_json=[x for x in OI if x['change_id']==id],source_urls_json=[url,API+f'/change/info?change_id={id}'],raw_incident_json=raw,raw_sha256=rh,quality_flags_json=flags,requested_start_utc='2024-02-01T00:00:00Z',cutoff_utc=CUTOFF,retrieved_at_utc=meta['retrieved_at_utc'],coverage_status='enumerated',collection_run_id='deepseek-20260927T193620Z',analysis_version='1.0.3-docs-only',spreadsheet_escaped_fields_json=[])
 rows.append(row);reviews.append({'incident_id':str(id),**assessment,'effective_grade':severity,'basis':basis})
HEAD='schema_version,company_id,company_name,status_page_url,source_platform,incident_id,incident_title,record_type,incident_status,published_at_utc,first_update_at_utc,first_resolved_at_utc,last_update_at_utc,official_severity,official_severity_codes_json,assessed_severity,severity_basis,severity_scope,service_groups_json,components_json,impact_start_at_utc,impact_end_at_utc,impact_seconds,known_full_seconds,known_full_partial_seconds,known_all_seconds,time_basis,time_complete,right_censored,review_status,analysis_summary,root_cause,root_cause_status,evidence_json,updates_json,impact_intervals_json,official_intervals_json,source_urls_json,raw_incident_json,raw_sha256,quality_flags_json,requested_start_utc,cutoff_utc,retrieved_at_utc,coverage_status,collection_run_id,analysis_version,spreadsheet_escaped_fields_json'.split(',')
with (ROOT/'incidents.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=HEAD);w.writeheader()
 for r in rows:
  out=dict(r);escaped=[]
  for k,v in out.items():
   if not k.endswith('_json') and isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')):out[k]="'"+v;escaped.append(k)
  out['spreadsheet_escaped_fields_json']=escaped
  for k in HEAD:
   if k.endswith('_json'):out[k]=canonical(out[k])
  w.writerow(out)
dump(ROOT/'analysis.json',reviews)
dump(ROOT/'service_windows.json',{'company_id':'deepseek','overall_group':'Overall','basis':'official component available_since_seconds; historical API identity, not model release dates','service_windows':{g:{'start':iso(a),'end':CUTOFF} for g,a in WINDOW.items()},'component_mapping':GROUP,'labels':LABEL})
def aggregate(year,g,exclude=()):
 a=max(WINDOW[g],stamp(f'{year}-01-01T00:00:00Z'));b=min(stamp(CUTOFF),stamp(f'{year+1}-01-01T00:00:00Z'))
 if a>=b:return None
 intervals=[x for r in rows if r['record_type']=='incident' and r['incident_id'] not in set(map(str,exclude)) for x in r['impact_intervals_json'] if g=='Overall' or g in x['service_groups']]
 sec=[seconds([(max(a,stamp(x['start_at'])),min(b,stamp(x['end_at']))) for x in intervals if RANK[x['severity']]>=rank]) for rank in [3,2,1]]
 count=sum(1 for r in rows if r['record_type']=='incident' and r['incident_id'] not in set(map(str,exclude)) and (g=='Overall' or g in r['service_groups_json']) and a<=stamp(r['impact_start_at_utc'] or r['published_at_utc'])<b)
 return dict(year=year,group=g,window_start=iso(a),window_end=iso(b),denominator_seconds=b-a,incident_count=count,full_hours=sec[0]/3600,full_partial_hours=sec[1]/3600,all_hours=sec[2]/3600,availability_full=1-sec[0]/(b-a),availability_full_partial=1-sec[1]/(b-a),availability_all=1-sec[2]/(b-a))
annual=[v for y in [2024,2025,2026] for g in LABEL if (v:=aggregate(y,g))]
dump(ROOT/'trend_data.json',{'schema_version':1,'cutoff_utc':CUTOFF,'annual':annual,'matched_windows':[]})
with (ROOT/'annual-data.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(annual[0]));w.writeheader();w.writerows(annual)
summary={'counts_by_publication_year':{y:dict(collections.Counter(r['record_type'] for r in rows if r['published_at_utc'].startswith(y))) for y in ['2024','2025','2026']},'grade_counts':dict(collections.Counter(r['assessed_severity'] for r in rows if r['record_type']=='incident')),'basis_counts':dict(collections.Counter(r['severity_basis'] for r in rows if r['record_type']=='incident')),'unknown_time_ids':[r['incident_id'] for r in rows if r['record_type']=='incident' and not r['impact_intervals_json']],'no_user_impact_incidents':0,'proxy_ids':list(PROXY_IDS),'root_cause_vendor_stated':sum(r['root_cause_status']=='vendor_stated' for r in rows),'sensitivity_exclude_two_long_2025':[aggregate(2025,g,[2328579188430287,2258210444252287]) for g in ['Overall','API','Chat']],'earliest_first_update_utc':min(r['first_update_at_utc'] for r in rows),'earliest_impact_utc':min(r['impact_start_at_utc'] for r in rows if r['impact_start_at_utc']),'latest_first_update_utc':max(r['first_update_at_utc'] for r in rows),'total_updates':sum(len(r['updates_json']) for r in rows)}
dump(ROOT/'summary-data.json',summary)
# Read back the actual deliverable and validate all JSON/hash/positive phases/unions/quotes.
with (ROOT/'incidents.csv').open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);assert reader.fieldnames==HEAD;rr=list(reader)
assert len(rr)==len(rows)==len({r['incident_id'] for r in rr})
for r in rr:
 for k in HEAD:
  if k.endswith('_json'):r[k]=json.loads(r[k])
 assert digest(r['raw_incident_json'])==r['raw_sha256']
 for e in r['evidence_json']['items']:assert e['quote']==r['raw_incident_json']['title'] or any(e['quote']==u['description'] for u in r['updates_json'])
 xs=r['impact_intervals_json']
 for x in xs:assert stamp(x['start_at'])<stamp(x['end_at'])<=stamp(CUTOFF)
 if xs:
  ns=[seconds([(stamp(x['start_at']),stamp(x['end_at'])) for x in xs if RANK[x['severity']]>=rank]) for rank in [3,2,1]]
  assert ns==[int(r[k]) for k in ['known_full_seconds','known_full_partial_seconds','known_all_seconds']];assert ns[0]<=ns[1]<=ns[2];assert int(r['impact_seconds'])==ns[2]
 else:assert r['impact_seconds']==''
dump(ROOT/'validation.json',{'structural_validation':'passed','records':len(rr),'columns':len(HEAD),'utf8_bom':(ROOT/'incidents.csv').read_bytes()[:3]==b'\xef\xbb\xbf','checks':['unique IDs','all JSON fields','raw canonical hashes','full update text round trip','evidence quote membership','UTC and positive intervals','cutoff bounds','per-record interval unions','nested duration monotonicity'],'csv_sha256':hashlib.sha256((ROOT/'incidents.csv').read_bytes()).hexdigest(),'not_claimed':['actual request success rate','all real outages disclosed','exact real impact boundaries']})
print(json.dumps(summary,ensure_ascii=False,indent=2))
