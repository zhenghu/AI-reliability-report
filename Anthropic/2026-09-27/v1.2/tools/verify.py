"""Independent sweep-line verification of final CSV, evidence, statistics and artifacts."""
import sys,json,csv,hashlib,re,collections,os
from pathlib import Path
from datetime import datetime,timedelta
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'v1.0';REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'.agents/skills/incident-research/scripts'))
from core import read_csv,validate_csv,utc,digest,write_json
R=read_csv(ROOT/'incidents.csv');S=json.loads((OLD/'snapshot.json').read_text());H=json.loads((OLD/'history-index.json').read_text());W=json.loads((ROOT/'service_windows.json').read_text())['service_windows'];T=json.loads((ROOT/'trend_data.json').read_text());D=json.loads((ROOT/'summary-data.json').read_text());I=json.loads((ROOT/'assessed-intervals.json').read_text());IB={r['id']:r for r in I};B={e['raw']['id']:e['raw'] for e in S['records']};core=set(W)-{'Overall'};cut=utc(S['cutoff_utc'])
assert len(R)==len(B)==len(H['ids'])==920
assert {r['incident_id'] for r in R}==set(B)==set(H['ids'])
assert sum(r['record_type']=='maintenance' for r in R)==4
assert all(r['review_status']=='assessed' for r in R)
assert (ROOT/'incidents.csv').read_bytes().startswith(b'\xef\xbb\xbf')
quotes=0;phases=0
for r in R:
 raw=r['raw_incident_json'];i=r['incident_id'];rev=r['evidence_json']['assessment'];u={a['id']:a['body'] for a in raw['incident_updates']}
 assert raw==B[i] and digest(raw)==r['raw_sha256']==rev['source_record_sha256']
 assert IB[i]['intervals']==r['impact_intervals_json']
 assert rev['incident_id']==i
 for e in r['evidence_json']['items']:
  assert e['quote'] in (u[e['update_id']] if e.get('update_id') else raw['name']),(i,e)
  assert e['source_url']=='https://status.claude.com/incidents/'+i;quotes+=1
 for x in r['impact_intervals_json']+r['evidence_json']['unknown_severity_candidate_intervals']:
  assert utc(x['start_at'])<utc(x['end_at'])<=cut
  assert bool(x['right_censored'])==(utc(x['end_at'])==cut)
  assert set(x['service_groups'])<=set(r['service_groups_json'])
  if x in r['impact_intervals_json']:assert x['severity'] in ['full_outage','partial_outage','degraded_performance']
  phases+=1
 if r['record_type']=='maintenance':assert not r['impact_intervals_json']
 if r['time_complete']=='True':assert r['impact_intervals_json'] and not any(x['time_basis'] in ['announcement_proxy','official_component_interval'] for x in r['impact_intervals_json'])

# Independent validation of user policy, raw color evidence, and unchanged semantic phases.
prior={r['incident_id']:r for r in read_csv(ROOT.parent/'v1.1/incidents.csv')}
color_map={'critical':'full_outage','major':'partial_outage','minor':'degraded_performance','major_outage':'full_outage','partial_outage':'partial_outage','degraded_performance':'degraded_performance'}
def color_check(raw,e):
 if e['raw_field']=='impact':assert raw['impact']==e['raw_value']
 else:
  u=next(u for u in raw['incident_updates'] if u['id']==e['update_id'])
  assert any(c['code']==e['component_id'] and c['new_status']==e['raw_value'] for c in u['affected_components'])
 assert color_map[e['raw_value']]==e['mapped_grade']
 assert e['source_url']=='https://status.claude.com/incidents/'+raw['id']
def sig(x):return (x['start_at'],x['end_at'],x['severity'],tuple(x['service_groups']),x['time_basis'])
fallback_checks=0;semantic_preserved=0
for r in R:
 old=prior[r['incident_id']];rev=r['evidence_json']['assessment'];raw=r['raw_incident_json']
 assert rev['semantic_grade']==old['assessed_severity']
 preserved=[x for x in r['impact_intervals_json'] if 'severity_evidence' not in x]
 assert collections.Counter(map(sig,preserved))==collections.Counter(map(sig,old['impact_intervals_json'])),r['incident_id']
 semantic_preserved+=len(preserved)
 assert (r['record_type'],r['service_groups_json'])==(old['record_type'],old['service_groups_json'])
 if 'no_user_impact' in r['quality_flags_json']:assert r['assessed_severity']=='unknown' and not r['impact_intervals_json']
 for x in r['impact_intervals_json']:
  if 'severity_evidence' not in x:continue
  ev=x['severity_evidence'];color_check(raw,ev);assert x['severity']==ev['mapped_grade']
  # Every filled segment was inside an existing unknown-severity candidate; no invented timing.
  assert any(set(x['service_groups'])<=set(y['service_groups']) and utc(y['start_at'])<=utc(x['start_at'])<utc(x['end_at'])<=utc(y['end_at']) for y in old['evidence_json']['unknown_severity_candidate_intervals']),(r['incident_id'],x)
  fallback_checks+=1
 if rev.get('official_fallback',{}).get('incident_grade_evidence'):color_check(raw,rev['official_fallback']['incident_grade_evidence'])
assert fallback_checks==D['fallback_phase_count']
assert D['previously_unknown_filled']==93 and D['unresolved_impact_grade_records']==8 and D['no_impact_records']==3

# Different algorithm: boundary sweep over intervals independently read from CSV.
def seconds(group,start,end,allowed,scenario):
 ev=[]
 for r in R:
  if r['record_type']!='incident':continue
  if scenario=='exclude_suspension' and r['incident_id']=='s9w82lp9dcn9':continue
  if scenario=='exclude_intermittent_envelopes' and any('intermittent' in f for f in r['quality_flags_json']):continue
  xs=r['impact_intervals_json']
  if scenario=='explicit_only':xs=[x for x in xs if x['time_basis'] in ['explicit_impact','timezone_inferred']]
  if scenario=='unknown_as_full':xs=xs+[dict(x,severity='full_outage') for x in r['evidence_json']['unknown_severity_candidate_intervals']]
  for x in xs:
   if x['severity'] not in allowed:continue
   for g in set(x['service_groups'])&core:
    if group not in ['Overall',g]:continue
    a=max(start,utc(x['start_at']),utc(W[g]['start']));b=min(end,utc(x['end_at']))
    if a<b:ev.extend([(a,1),(b,-1)])
 n=0;last=None;total=0
 for time,delta in sorted(ev):
  if n and last is not None:total+=(time-last).total_seconds()
  n+=delta;last=time
 assert n==0
 return total
checks=0
for row in T['annual']+T['matched_windows']+T['monthly']+D['sensitivity_2026']:
 a,b=utc(row['window_start']),utc(row['window_end']);den=(b-a).total_seconds();assert den==row['denominator_seconds']
 for hour,rate,allow in [('full_hours','availability_full',{'full_outage'}),('full_partial_hours','availability_full_partial',{'full_outage','partial_outage'}),('all_hours','availability_all',{'full_outage','partial_outage','degraded_performance'})]:
  s=seconds(row['group'],a,b,allow,row['series']);assert abs(s/3600-row[hour])<1e-7,(row,hour);assert abs(1-s/den-row[rate])<1e-10;checks+=1
 assert 0<=row['full_hours']<=row['full_partial_hours']<=row['all_hours']<=den/3600

# Frozen acquisition and v1.0 manifest integrity.
http=0
for meta in OLD.rglob('*.meta.json'):
 d=json.loads(meta.read_text());body=meta.with_name(meta.name.replace('.meta.json','.json'))
 if not body.exists():body=meta.with_name(meta.name.replace('.meta.json','.html'))
 if 'sha256' in d and body.exists():assert hashlib.sha256(body.read_bytes()).hexdigest()==d['sha256'];http+=1
frozen_files=0
for line in (OLD/'SHA256SUMS').read_text().splitlines():
 expected,relative=line.split('  ',1);assert hashlib.sha256((OLD/relative).read_bytes()).hexdigest()==expected,relative;frozen_files+=1
prior_files=0
for line in (ROOT.parent/'v1.1/SHA256SUMS').read_text().splitlines():
 expected,relative=line.split('  ',1);assert hashlib.sha256((ROOT.parent/'v1.1'/relative).read_bytes()).hexdigest()==expected,relative;prior_files+=1
for a,b in zip(H['requests'],H['requests'][1:]):assert utc(b['end'])+timedelta(seconds=1)==utc(a['start'])
assert H['requests'][-1]['count']==0
class Page(HTMLParser):
 def __init__(self):super().__init__();self.ids=set();self.links=[];self.details=0;self.svg=0
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if 'id' in a:assert a['id'] not in self.ids,a['id'];self.ids.add(a['id'])
  if t=='a':self.links.append(a['href'])
  if t=='details':self.details+=1
  if t=='svg':self.svg+=1
p=ROOT.parent.parent/'Anthropic_Claude_Availability_Report_2026-09-27_v1.2.html';h=Page();h.feed(p.read_text());assert h.details==920 and h.svg==6
for link in h.links:
 if link.startswith('#'):assert link[1:] in h.ids
 elif not re.match('https?://',link) and not link.endswith('/verification.json'):assert (p.parent/link).is_file(),link
assert '<script src=' not in p.read_text()
assert len(list((ROOT/'figures').glob('*.png')))==6
# Charts' CSV numeric source checks.
f=list(csv.DictReader((ROOT/'figures/03_product_availability.csv').open(encoding='utf-8-sig')))
for a,b in zip(f,[r for r in T['annual'] if r['year']==2026]):
 for label,k in [('F only','availability_full'),('F + P','availability_full_partial'),('F + P + D','availability_all')]:assert abs(float(a[label])-100*b[k])<1e-6
# All observed product-year points use the same metric; unobserved years are absent.
f=list(csv.DictReader((ROOT/'figures/02_annual_availability.csv').open(encoding='utf-8-sig')))
annual={(r['group'],r['year']):r for r in T['annual']}
assert len(f)==len(annual)==20
assert {(r['group'],int(r['year'])) for r in f}==set(annual)
for a in f:
 b=annual[a['group'],int(a['year'])]
 assert (a['window_start'],a['window_end'])==(b['window_start'],b['window_end'])
 assert abs(float(a['FPD_pct'])-100*b['availability_all'])<1e-10
assert p.read_text().index('年度可用性总结</h2>')<p.read_text().index('图 1：年度可用性趋势折线图')
assert {x.name for x in p.parent.glob('Anthropic_Claude_Availability_Report_*')}=={p.name,p.with_suffix('.md').name}
res={'validation':'passed','csv_structure':validate_csv(ROOT/'incidents.csv'),'official_color_fallback_phase_checks':fallback_checks,'original_semantic_phases_preserved':semantic_preserved,'semantic_review_records':920,'pending_review_records':0,'review_scope':'Reuses full v1.1 semantic review; user-approved official color fallback validated directly against raw fields; no new timing invented','source_objects_identical_to_frozen_snapshot':920,'quotes_checked':quotes,'phases_checked':phases,'independent_interval_and_ratio_checks':checks,'raw_HTTP_body_hashes_checked':http,'v1_0_manifest_files_unchanged':frozen_files,'v1_1_archive_manifest_files_checked':prior_files,'history_contiguous_pages':16,'HTML_index_records':h.details,'embedded_SVG_figures':h.svg,'local_and_anchor_links':'passed','not_measured':['Actual request-weighted success rates','Undisclosed/deleted incidents','Full bodies of inaccessible supplementary postmortems','True duration of unlocated or intermittent effects']}
write_json(ROOT/'verification.json',res)
# Hash all final artifact bytes, excluding the manifest itself.
files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name not in ['SHA256SUMS','integrity-manifest.json'] and '__pycache__' not in p.parts)
files+= [ROOT.parent.parent/('Anthropic_Claude_Availability_Report_2026-09-27_v1.2'+ext) for ext in ['.html','.md']]
manifest=[{'path':os.path.relpath(p,ROOT),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
write_json(ROOT/'integrity-manifest.json',{'files':manifest,'frozen_input_snapshot_sha256':hashlib.sha256((OLD/'snapshot.json').read_bytes()).hexdigest(),'cutoff_utc':S['cutoff_utc']})
(ROOT/'SHA256SUMS').write_text(''.join(f"{r['sha256']}  {r['path']}\n" for r in manifest))
print(json.dumps(res,ensure_ascii=False,indent=2))
