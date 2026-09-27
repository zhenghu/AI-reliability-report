"""Independent, read-only arithmetic/evidence checks for the frozen report."""
import sys,json,hashlib,re,collections
from pathlib import Path
from datetime import datetime,timedelta
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'.agents/skills/incident-research/scripts'))
from core import read_csv,validate_csv,utc,write_json,digest
S=json.loads((ROOT/'snapshot.json').read_text());R=read_csv(ROOT/'incidents.csv');T=json.loads((ROOT/'trend_data.json').read_text());W=json.loads((ROOT/'service_windows.json').read_text());D=json.loads((ROOT/'summary-data.json').read_text());REF=json.loads((ROOT/'reference-intervals.json').read_text());H=json.loads((ROOT/'history-index.json').read_text());core=set(W['service_windows'])-{'Overall'}
assert len(R)==len(S['records'])==len(H['ids'])==920
assert {r['incident_id'] for r in R}==set(H['ids'])
assert sum(r['record_type']=='maintenance' for r in R)==4
# Continuous history windows are closed seconds in original History metadata.
for a,b in zip(H['requests'],H['requests'][1:]):assert utc(b['end'])+timedelta(seconds=1)==utc(a['start'])
assert H['requests'][-1]['count']==0
# Raw saved bytes: each .meta.json hash must match its associated response body.
checked=0
for meta in ROOT.rglob('*.meta.json'):
 d=json.loads(meta.read_text());body=meta.with_name(meta.name.replace('.meta.json','.json'))
 if not body.exists():body=meta.with_name(meta.name.replace('.meta.json','.html'))
 if 'sha256' in d and body.exists():
  assert hashlib.sha256(body.read_bytes()).hexdigest()==d['sha256'],str(meta);checked+=1
# Exact quoted text, assessment source hash, and original update linkage.
quotes=0
for row in R:
 raw=row['raw_incident_json'];text=raw['name']+'\n'+'\n'.join(u['body'] for u in raw['incident_updates']);updates={u['id']:u['body'] for u in raw['incident_updates']}
 assert digest(raw)==row['raw_sha256']
 for e in row['evidence_json']['items']:
  assert e['quote'] in text,(row['incident_id'],e)
  if e.get('update_id'):assert e['quote'] in updates[e['update_id']]
  quotes+=1
 for x in row['impact_intervals_json']+row['evidence_json']['reference_intervals']:
  assert utc(x['start_at'])<utc(x['end_at'])<=utc(row['cutoff_utc'])
  if x['right_censored']:assert utc(x['end_at'])==utc(row['cutoff_utc'])
# Independent sweep-line union, distinct from core.union_seconds.
def duration(series,g,a,b,allowed,exclude=False):
 events=[]
 for r in series:
  if r['record_type']!='incident' or (exclude and r['id']=='s9w82lp9dcn9'):continue
  for x in r['intervals']:
   if x['severity'] not in allowed:continue
   for sg in set(x['service_groups'])&core:
    if g not in ['Overall',sg]:continue
    start=max(a,utc(x['start_at']),utc(W['service_windows'][sg]['start']));end=min(b,utc(x['end_at']))
    if start<end:events.extend([(start,1),(end,-1)])
 count=0;previous=None;seconds=0
 for time,delta in sorted(events):
  if count and previous is not None:seconds+=(time-previous).total_seconds()
  count+=delta;previous=time
 assert count==0
 return seconds
checks=0
series=T['annual']+T['matched_windows']+D['full_period']+D['sensitivity_2026_excluding_suspension']
for r in series:
 a,b=utc(r['window_start']),utc(r['window_end']);den=(b-a).total_seconds()
 for names,allowed in [(('full_hours','availability_full'),{'full_outage'}),(('full_partial_hours','availability_full_partial'),{'full_outage','partial_outage'}),(('all_hours','availability_all'),{'full_outage','partial_outage','degraded_performance'})]:
  seconds=duration(REF,r['group'],a,b,allowed,r.get('exclude_intentional_suspension',False))
  assert abs(seconds/3600-r[names[0]])<1e-7,(r,names)
  assert abs(1-seconds/den-r[names[1]])<1e-10
  checks+=1
 assert 0<=r['full_hours']<=r['full_partial_hours']<=r['all_hours']<=den/3600
# Report local/anchor links, and every record appears exactly once in interactive appendix.
class Page(HTMLParser):
 def __init__(self):super().__init__();self.ids=set();self.links=[];self.details=0
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if 'id' in a:assert a['id'] not in self.ids;self.ids.add(a['id'])
  if t=='a':self.links.append(a['href'])
  if t=='details':self.details+=1
p=next(ROOT.glob('Anthropic_Claude_Availability_Report_*.html'));parser=Page();parser.feed(p.read_text());assert parser.details==920
for link in parser.links:
 if link.startswith('#'):assert link[1:] in parser.ids,link
 elif not re.match(r'https?://',link):assert (ROOT/link).is_file(),link
assert '<script src=' not in p.read_text()
result={'validation':'passed','csv_structure':validate_csv(ROOT/'incidents.csv'),'raw_HTTP_body_hashes_checked':checked,'evidence_quotes_checked':quotes,'independent_interval_and_ratio_checks':checks,'history_pages_contiguous':16,'HTML_index_records':920,'HTML_local_and_anchor_links':'passed','semantic_completeness':'NOT complete; report explicitly discloses pending records','not_verified':['All event semantics and historical component assignment','Actual request-weighted uptime','Vendor undisclosed outages','Extra linked postmortem full HTTP body (403)']}
write_json(ROOT/'verification.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
