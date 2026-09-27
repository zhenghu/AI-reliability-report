"""Rebuild reviewed CSV and union-time estimates from frozen evidence. No network."""
import sys,json,csv,hashlib,collections,copy,ast
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]; OLD=ROOT.parent/'v1.0'; REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'.agents/skills/incident-research/scripts'))
from core import read_csv,normalized_updates,lifecycle_windows,utc,iso,js,digest,union_seconds,FIELDS,JSON_FIELDS,write_json,validate_csv
S=json.loads((OLD/'snapshot.json').read_text()); END=utc(S['cutoff_utc']); M=copy.deepcopy(S['components']); M['vy0zz4d9qxr9']={'id':'vy0zz4d9qxr9','name':'Message Batches API','group':'API'}
W=json.loads((OLD/'service_windows.json').read_text()); START={g:utc(v['start']) for g,v in W['service_windows'].items()}; CORE=set(START)-{'Overall'}
REV=[r for f in ['early','middle','recent'] for r in json.loads((ROOT/'reviews'/f'{f}.json').read_text())]
assert len(REV)==920 and len({r['incident_id'] for r in REV})==920
D={r['incident_id']:r for r in REV}; PRIOR={r['incident_id']:r for r in json.loads((OLD/'analysis.json').read_text())['records']}
# Read explicit constants without executing or rewriting the original report.
const={}
for n in ast.parse((OLD/'tools/analyze.py').read_text()).body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['TIMES','REFERENCE_TIMES']:
  const[n.targets[0].id]=ast.literal_eval(n.value)
GM={'major_outage':'full_outage','partial_outage':'partial_outage','degraded_performance':'degraded_performance'}; grades=set(GM.values())
def phase(a,b,grade,groups,basis,**kw):
 return dict(start_at=iso(a),end_at=iso(b),severity=grade,service_groups=groups,time_basis=basis,right_censored=b==END,**kw)
def candidates(raw,groups,grade):
 """Historical per-component boundaries; no cross-product replication."""
 us=normalized_updates(raw,'statuspage');out=[];pending={}
 for u in us:
  t=utc(u['at'])
  if t>END:continue
  for c in u['component_statuses'] or []:
   cid=c.get('code',c.get('id'));sg=M.get(cid,{}).get('group','Unmapped');state=c.get('new_status')
   if cid in pending:
    a,old,uid=pending.pop(cid)
    if a<t:out.append(phase(a,t,grade,[sg],'official_component_interval',start_update_id=uid,end_update_id=u['id'],official_state=old))
   if state in GM and sg in groups:pending[cid]=(t,state,u['id'])
  if u['status'] in ['resolved','completed','postmortem']:
   for cid,(a,old,uid) in pending.items():
    if a<t:out.append(phase(a,t,grade,[M.get(cid,{}).get('group','Unmapped')],'official_component_interval',start_update_id=uid,end_update_id=u['id'],official_state=old,end_is_resolution_proxy=True))
   pending={}
 for cid,(a,old,uid) in pending.items():
  if a<END:out.append(phase(a,END,grade,[M.get(cid,{}).get('group','Unmapped')],'official_component_interval',start_update_id=uid,official_state=old))
 # Where corrected semantic groups have no historical transitions, a separately labelled lifecycle proxy.
 present={g for x in out for g in x['service_groups']}
 for sg in sorted(set(groups)-present):
  out.extend(phase(a,b,grade,[sg],'announcement_proxy') for a,b in lifecycle_windows(us,END) if a<b)
 return out
rows=read_csv(OLD/'incidents.csv');series=[];issues=[]
for row in rows:
 i=row['incident_id']; rev=copy.deepcopy(D[i]);
 # Independent service-scope audit: current component associations that stayed operational are not affected products.
 omit={'mwl16r45ph0h':{'Console'},'9x13dhrf7nxf':{'Claude.ai'},'1gw39bglyd46':{'Claude.ai'}}.get(i,set())
 if omit:
  rev['groups']=[g for g in rev['groups'] if g not in omit];rev.setdefault('flags',[]).append('operational_component_not_expanded');rev['summary']+=' 独立复核：移除全程 operational 且正文未指明受影响的组件 '+', '.join(sorted(omit))+'。'
 raw=row['raw_incident_json']; us={u['id']:u for u in raw['incident_updates']};assert digest(raw)==row['raw_sha256']
 assert rev['grade'] in grades|{'unknown'}
 evidence=rev['evidence'];assert evidence,(i,'missing evidence')
 for e in evidence:
  q=e['quote'];src=us[e['update_id']]['body'] if e.get('update_id') else raw['name'];assert q in src,(i,e)
  e['source_url']='https://status.claude.com/incidents/'+i
 rev['source_record_sha256']=digest(raw); groups=rev['groups']; mode=rev['time_mode']; intervals=copy.deepcopy(rev.get('intervals') or [])
 flags=list(rev.get('flags') or [])
 if row['record_type']=='maintenance':flags.append('maintenance'); intervals=[];mode='none'
 if not intervals and mode!='none':
  if rev.get('use_prior_explicit') and i in const['TIMES']:
   a,b=map(utc,const['TIMES'][i]);intervals=[phase(a,b,rev['grade'],groups,'explicit_impact')]
  elif i in const['REFERENCE_TIMES']:
   a,b=map(utc,const['REFERENCE_TIMES'][i]);intervals=[phase(a,b,rev['grade'],groups,'explicit_impact')]
  else:intervals=candidates(raw,groups,rev['grade'])
 for x in intervals:
  a,b=utc(x['start_at']),min(utc(x['end_at']),END);assert a<b,(i,x)
  x['start_at']=iso(a);x['end_at']=iso(b);x['right_censored']=b==END
  x.setdefault('severity',rev['grade']);x.setdefault('service_groups',groups);x.setdefault('time_basis','announcement_proxy')
  x['evidence_indices']=list(range(len(evidence)))
  assert x['severity'] in grades|{'unknown'}
 assessed=[x for x in intervals if x['severity']!='unknown'];unknown=[x for x in intervals if x['severity']=='unknown']
 if 'no_user_impact' in flags or 'maintenance' in flags:assessed=[];unknown=[]
 for e in evidence:e.setdefault('kind','severity')
 groups=sorted(set(groups)|{g for x in assessed+unknown for g in x['service_groups']});rev['groups']=groups
 rev['intervals']=assessed;rev['uncertain_intervals']=unknown
 row.update(assessed_severity=rev['grade'],severity_basis='complete_record_semantic_review',severity_scope='whole_product_per_named_service; Overall is any included product affected, not company-wide outage',service_groups_json=groups,review_status='assessed',analysis_summary=rev['summary']+' 时间：'+rev.get('time_note',''),root_cause=rev.get('root_cause',''),root_cause_status=rev.get('root_cause_status','not_disclosed'),impact_intervals_json=assessed,time_complete=bool(rev.get('time_complete',False)) and bool(assessed) and not unknown,analysis_version='incident-research-1.0.1-docs-only/anthropic-reviewed-v1.1')
 row['evidence_json']={'items':evidence,'assessment':rev,'unknown_severity_candidate_intervals':unknown}
 row['impact_start_at_utc']=min((x['start_at'] for x in assessed),default=None);row['impact_end_at_utc']=max((x['end_at'] for x in assessed),default=None)
 for key,allow in [('impact_seconds',grades),('known_full_seconds',{'full_outage'}),('known_full_partial_seconds',{'full_outage','partial_outage'}),('known_all_seconds',grades)]:row[key]=union_seconds(assessed,allow) if assessed else None
 row['time_basis']=';'.join(sorted({x['time_basis'] for x in assessed})) or 'unknown';row['right_censored']=any(x['right_censored'] for x in assessed)
 if rev['grade']=='unknown':flags.append('unknown_assessed_severity')
 if not assessed:flags.append('no_assessed_located_interval')
 if not row['time_complete']:flags.append('actual_timeline_incomplete_or_proxy')
 if any(x['time_basis']=='announcement_proxy' for x in assessed):flags.append('announcement_proxy')
 if any(x['time_basis']=='official_component_interval' for x in assessed):flags.append('historical_status_time_proxy')
 if i=='s9w82lp9dcn9':flags.append('intentional_model_access_suspension')
 row['quality_flags_json']=sorted(set(flags))
 series.append(dict(id=i,record_type=row['record_type'],published_at=row['published_at_utc'],groups=groups,grade=rev['grade'],intervals=assessed,unknown_intervals=unknown,time_complete=row['time_complete'],flags=flags))
 D[i]=rev

def clips(r,g,a,b,scenario):
 out=[]
 xs=r['intervals']
 if scenario=='exclude_suspension' and r['id']=='s9w82lp9dcn9':return []
 if scenario=='exclude_intermittent_envelopes' and any('intermittent' in f for f in r['flags']):return []
 if scenario=='explicit_only':xs=[x for x in xs if x['time_basis'] in ['explicit_impact','timezone_inferred']]
 if scenario=='unknown_as_full':xs=xs+[dict(x,severity='full_outage') for x in r['unknown_intervals']]
 for x in xs:
  for sg in set(x['service_groups'])&CORE:
   if g not in ['Overall',sg]:continue
   aa=max(utc(x['start_at']),START[sg],a);bb=min(utc(x['end_at']),b)
   if aa<bb:out.append(dict(x,start_at=iso(aa),end_at=iso(bb)))
 return out

def calc(g,a,b,scenario='reviewed'):
 records=[r for r in series if r['record_type']=='incident' and not(scenario=='exclude_suspension' and r['id']=='s9w82lp9dcn9')]
 relevant=[r for r in records if (set(r['groups'])&CORE if g=='Overall' else g in r['groups'])]
 phases=[x for r in relevant for x in clips(r,g,a,b,scenario)];den=(b-a).total_seconds()
 # Both incident counts retained: publication comparable to History, impact-first recommended for trend bridge.
 published=[r for r in relevant if a<=utc(r['published_at'])<b]
 def when(r):
  own=[utc(x['start_at']) for x in r['intervals'] if (set(x['service_groups'])&CORE if g=='Overall' else g in x['service_groups'])]
  return min(own) if own else utc(r['published_at'])
 counted=[r for r in relevant if a<=when(r)<b]
 secs=[union_seconds(phases,z,a,b) for z in [{'full_outage'},{'full_outage','partial_outage'},grades]]
 return dict(year=a.year,group=g,window_start=iso(a),window_end=iso(b),denominator_seconds=den,incident_count=len(counted),publication_count=len(published),unknown_grade_count=sum(r['grade']=='unknown' or any((set(x['service_groups'])&CORE if g=='Overall' else g in x['service_groups']) for x in r['unknown_intervals']) for r in published),no_assessed_interval_count=sum(not clips(r,g,a,b,'reviewed') for r in published),full_hours=secs[0]/3600,full_partial_hours=secs[1]/3600,all_hours=secs[2]/3600,availability_full=1-secs[0]/den,availability_full_partial=1-secs[1]/den,availability_all=1-secs[2]/den,count_basis='first_assessed_impact_else_publication_utc',series=scenario,estimate=True)
annual=[];matched=[];monthly=[]
for g,start in START.items():
 for y in range(start.year,END.year+1):
  a=max(start,datetime(y,1,1,tzinfo=timezone.utc));b=min(END,datetime(y+1,1,1,tzinfo=timezone.utc));annual.append(calc(g,a,b))
  if g in ['Overall','Claude.ai','API','Console'] and y>=2024:matched.append(calc(g,datetime(y,1,1,tzinfo=timezone.utc),END.replace(year=y)))
 for y in range(start.year,END.year+1):
  for m in range(1,13):
   a=max(start,datetime(y,m,1,tzinfo=timezone.utc));b=min(END,datetime(y+int(m==12),m%12+1,1,tzinfo=timezone.utc))
   if a<b:monthly.append(dict(calc(g,a,b),month=f'{y}-{m:02}'))
sensitivity=[calc(g,max(start,datetime(2026,1,1,tzinfo=timezone.utc)),END,sc) for sc in ['reviewed','exclude_suspension','explicit_only','unknown_as_full','exclude_intermittent_envelopes'] for g,start in START.items()]
write_json(ROOT/'analysis.json',{'schema_version':1,'records':list(D.values()),'review_policy':'All 920 records reviewed against complete frozen updates; unknown findings retained.'})
write_json(ROOT/'assessed-intervals.json',series);write_json(ROOT/'service_windows.json',W)
write_json(ROOT/'trend_data.json',dict(schema_version=1,cutoff_utc=S['cutoff_utc'],annual=annual,matched_windows=matched,monthly=monthly,provenance={'series':'reviewed_semantics_with_labelled_time_proxies','source':'incidents.csv impact_intervals_json','not_request_success_rate':True}))
write_json(ROOT/'summary-data.json',dict(sensitivity_2026=sensitivity,review_counts=dict(collections.Counter(r['review_status'] for r in rows)),grade_counts=dict(collections.Counter(r['assessed_severity'] for r in rows if r['record_type']=='incident')),unknown_grade_incidents=sum(r['record_type']=='incident' and r['assessed_severity']=='unknown' for r in rows),no_assessed_interval_incidents=sum(r['record_type']=='incident' and not r['impact_intervals_json'] for r in rows),complete_actual_timeline_incidents=sum(r['record_type']=='incident' and r['time_complete'] for r in rows),timing_phase_counts=dict(collections.Counter(x['time_basis'] for r in series for x in r['intervals'])),root_cause_counts=dict(collections.Counter(r['root_cause_status'] for r in rows if r['record_type']=='incident'))))
with (ROOT/'incidents.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
 for original in rows:
  r=dict(original);escaped=[]
  for k,v in r.items():
   if k in JSON_FIELDS:r[k]=js(v)
   elif isinstance(v,str) and v.lstrip().startswith(('=','+','-','@','\t','\r')):r[k]="'"+v;escaped.append(k)
  r['spreadsheet_escaped_fields_json']=js(escaped);w.writerow(r)
for name,data in [('annual-results',annual),('matched-window-results',matched),('monthly-results',monthly),('sensitivity-2026',sensitivity)]:
 with (ROOT/f'{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
v=validate_csv(ROOT/'incidents.csv');v['sha256']=hashlib.sha256((ROOT/'incidents.csv').read_bytes()).hexdigest();v['review_counts']=dict(collections.Counter(r['review_status'] for r in rows));write_json(ROOT/'incidents.validation.json',v)
print(json.dumps(v,ensure_ascii=False,indent=2))
