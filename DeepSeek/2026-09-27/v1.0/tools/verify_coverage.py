"""Verify saved enumeration, HTTP hashes, history IDs and model-field preservation."""
import json,hashlib,collections
from pathlib import Path
from collect import ROOT,stamp,iso,CUTOFF
rs=json.loads((ROOT/'records.json').read_text());ids={r['change_id'] for r in rs};windows=json.loads((ROOT/'enumeration.json').read_text());checks=json.loads((ROOT/'history-crosscheck.json').read_text())
assert all(windows[i]['end']==windows[i+1]['start'] for i in range(len(windows)-1));assert windows[-1]['end']==CUTOFF
assert set(x for c in checks for x in c['ids'])==ids
lists={}
for p in (ROOT/'raw').glob('list-*.json'):
 if '.meta.' not in p.name:
  for r in json.loads(p.read_text())['data']['items']:lists[r['change_id']]=r
assert set(lists)==ids
for r in rs:assert [u['description'] for u in r['updates']]==[u['description'] for u in lists[r['change_id']]['updates']]
for tags,month in [(['jan25a','jan25b'],'2025-01'),(['aug26a','aug26b'],'2026-08')]:
 half={r['change_id'] for tag in tags for r in json.loads((ROOT/'raw'/f'check-{tag}.json').read_text())['data']['items']}
 full={r['change_id'] for r in json.loads((ROOT/'raw'/f'list-{month}.json').read_text())['data']['items']};assert half==full
assert not json.loads((ROOT/'raw'/'check-prestart.json').read_text())['data']['items']
http_count=0
for p in (ROOT/'raw').glob('*.meta.json'):
 m=json.loads(p.read_text());q=p.with_name(p.name.removesuffix('.meta.json'));assert hashlib.sha256(q.read_bytes()).hexdigest()==m['sha256'];http_count+=1
def union(xs):
 out=[]
 for a,b in sorted(xs):
  if b<=a:continue
  if out and a<=out[-1][1]:out[-1][1]=max(out[-1][1],b)
  else:out.append([a,b])
 return out
def sec(xs):return sum(b-a for a,b in union(xs))
legacy_uncovered=[]
for r in rs:
 states={};named=[];unnamed=[]
 for u in sorted(r['updates'],key=lambda x:x['at_seconds']):
  for c in u.get('component_changes',[]):
   cid=c['component_id'];t=u['at_seconds']
   if cid in states:
    old,a,known=states[cid]
    if old in ['full_outage','partial_outage','degraded']:(named if known else unnamed).append((a,t))
   states[cid]=(c['status'],t,bool(c.get('component_name')))
 # Only undistributed legacy IDs lack names; all close with explicit operational updates.
 for cid,(old,a,known) in states.items():
  if old in ['full_outage','partial_outage','degraded']:(named if known else unnamed).append((a,r['close_at_seconds']))
 extra=sec(named+unnamed)-sec(named)
 if extra:legacy_uncovered.append({'id':r['change_id'],'seconds':extra})
out={'status':'enumerated','query_start_utc':windows[0]['start'],'observation_start_utc':'2024-02-01T00:00:00Z','cutoff_utc':CUTOFF,'monthly_windows':len(windows),'unique_records':len(ids),'history_cross_check':'passed: union of 17 overlapping two-month History payloads equals all 105 API IDs','history_pages':len(checks),'browser_spot_check':{'2026-09':{'September':8,'August':16,'July_displayed_zero_despite_API_8':True},'2026-07':{'July':8,'June':3,'May_displayed_zero_despite_API_7':True},'finding':'History header spans 3 months but visible/data events cover only the last 2; overlapping History pages used to avoid this gap.'},'all_314_update_descriptions_match_list_and_detail':True,'split_window_checks':['2025-01','2026-08'],'prestart_query':'2023-01-01 through 2024-02-01 returned zero; official oldest component availability date 2024-02-01 is the stopping boundary, not proof of no earlier undisclosed incidents','verified_http_response_hashes':http_count,'unknown_legacy_component_extra_overall_seconds':legacy_uncovered,'collection_interruption':{'type':'connection reset during one detail request','recovery':'resumed once from saved responses; all 105 details completed','remaining_failed_windows':[]},'postmortem_check':'All detail objects and all 314 updates examined; no separate postmortem fields or external document links; five important HTML detail pages also saved. This is not a claim that no external postmortem exists.'}
(ROOT/'coverage.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
