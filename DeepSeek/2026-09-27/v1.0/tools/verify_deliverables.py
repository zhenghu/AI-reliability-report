"""Independent CSV-to-annual sweep-line check plus report/link/hash checks."""
import json,csv,re,hashlib,collections,zipfile
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]
def ts(s):return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def sweep(xs):
 events=collections.Counter()
 for a,b in xs:
  if a<b:events[a]+=1;events[b]-=1
 depth=0;last=None;total=0
 for t,delta in sorted(events.items()):
  if last is not None and depth>0:total+=t-last
  depth+=delta;last=t
 assert depth==0
 return total
with (ROOT/'incidents.csv').open(encoding='utf-8-sig',newline='') as f:rr=list(csv.DictReader(f))
for r in rr:
 for k in list(r):
  if k.endswith('_json'):r[k]=json.loads(r[k])
 for x in r['impact_intervals_json']:
  ev=x['severity_evidence']
  if 'raw_field' in ev:
   val=r['raw_incident_json']
   for tok in re.findall(r'[A-Za-z_]+|\d+',ev['raw_field']):val=val[int(tok)] if tok.isdigit() else val[tok]
   assert val==ev['raw_value']
  if 'quote' in ev:assert ev['quote'] in r['raw_incident_json']['title'] or any(ev['quote'] in u['description'] for u in r['updates_json'])
data=json.loads((ROOT/'trend_data.json').read_text());rank={'full_outage':3,'partial_outage':2,'degraded_performance':1}
for row in data['annual']:
 a,b=ts(row['window_start']),ts(row['window_end']);assert row['denominator_seconds']==b-a
 for threshold,hour,avail in [(3,'full_hours','availability_full'),(2,'full_partial_hours','availability_full_partial'),(1,'all_hours','availability_all')]:
  xs=[(max(a,ts(x['start_at'])),min(b,ts(x['end_at']))) for r in rr if r['record_type']=='incident' for x in r['impact_intervals_json'] if rank[x['severity']]>=threshold and (row['group']=='Overall' or row['group'] in x['service_groups'])]
  n=sweep(xs);assert abs(n-row[hour]*3600)<1e-6;assert abs((1-n/(b-a))-row[avail])<1e-12
md=(ROOT/'DeepSeek_Availability_Report_2026-09-27_v1.0.md').read_text();ht=(ROOT/'DeepSeek_Availability_Report_2026-09-27_v1.0.html').read_text()
for row in data['annual']:assert f"{row['availability_all']*100:.4f}%" in md
for url in re.findall(r'\]\(([^)]+)\)',md):
 if not url.startswith(('https:','http:','#')):assert (ROOT/url).exists(),url
assert ht.count('class="incident"')==105;assert ht.count('data:image/svg+xml;base64,')==2
assert hashlib.sha256((ROOT/'incidents.csv').read_bytes()).hexdigest() in md
manifest=json.loads((ROOT/'publication_manifest.json').read_text())
for name,v in manifest['files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==v['sha256']
with zipfile.ZipFile(ROOT/'DeepSeek_Availability_Audit_2026-09-27_v1.0.zip') as z:assert z.testzip() is None
result={'passed':True,'annual_rows_independently_recomputed':len(data['annual']),'annual_modes_verified':len(data['annual'])*3,'phase_raw_field_evidence_verified':True,'csv_to_report_values_match':True,'local_report_links_exist':True,'html_incident_index_count':105,'embedded_charts':2,'manifest_hashes_verified':sum(n!='verification.json' for n in manifest['files']),'zip_crc_passed':True,'limitations':'Structural and numerical checks do not prove the completeness of real-world incidents or exact impact times.'}
(ROOT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
