"""Capture official History HTML and complete public incident JSON; no credentials."""
import sys,json,re,html,hashlib,time,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'.agents/skills/incident-research/scripts'))
from core import write_json,utc,digest
from adapters import Client
BASE='https://status.claude.com'
CUTOFF='2026-09-27T16:10:43Z'
def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
history=ROOT/'evidence/history';history.mkdir(parents=True,exist_ok=True)
requests=[];ids={};windows=[]
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
for page in range(1,41):
 url=BASE+'/history?page='+str(page);path=history/f'page-{page:02}.html'
 if path.exists(): b=path.read_bytes();meta=json.loads(path.with_suffix('.meta.json').read_text())
 else:
  with op.open(urllib.request.Request(url,headers={'User-Agent':'incident-research/1.0 public-research'}),timeout=30) as response:b=response.read()
  meta={'url':url,'retrieved_at_utc':now(),'sha256':hashlib.sha256(b).hexdigest(),'hash_object':'HTTP response body bytes','page':page}
  path.write_bytes(b);write_json(path.with_suffix('.meta.json'),meta);time.sleep(.3)
 match=re.search(r'data-react-class="HistoryIndex" data-react-props="([^"]+)"',b.decode())
 if not match:raise ValueError('Missing History data')
 d=json.loads(html.unescape(match[1]));write_json(path.with_suffix('.props.json'),d)
 win=(d['start_time'],d['end_time']);assert win not in windows;windows.append(win)
 count=0
 for m in d['months']:
  for i in m['incidents']:
   ids.setdefault(i['code'],{'history_urls':[],'history_rows':[]})['history_urls'].append(url)
   ids[i['code']]['history_rows'].append(i);count+=1
 requests.append(dict(meta,start=win[0],end=win[1],count=count));write_json(ROOT/'history-index.json',{'requests':requests,'ids':ids})
 print('history',page,win,count,'unique',len(ids),flush=True)
 created=d['page_status']['page']['created_at']
 if utc(win[1])<utc(created):
  assert count==0,'Unexpected pre-creation history';break
else:raise ValueError('UI history limit reached')
original=json.loads((ROOT/'collection/snapshot.json').read_text());old={r['raw']['id']:r for r in original['records']}
allids=sorted(set(ids)|set(old));results={};errors=[]
def fetch(i):
 c=Client(ROOT/'evidence/details',delay=.35)
 d,m=c.get(BASE+'/api/v2/incidents/'+i+'.json');r=d['incident'];assert r['id']==i
 return i,{'raw':r,'platform':'statuspage','record_type':'maintenance' if r.get('scheduled_for') else 'incident','source_urls':[BASE+'/incidents/'+i,m['url']]+ids.get(i,{}).get('history_urls',[]),'retrieved_at_utc':m['retrieved_at_utc']}
with ThreadPoolExecutor(max_workers=2) as pool:
 futures={pool.submit(fetch,i):i for i in allids}
 for f in as_completed(futures):
  try:i,r=f.result();results[i]=r
  except Exception as e:errors.append({'id':futures[f],'error':str(e)})
  if (len(results)+len(errors))%25==0:
   print('details',len(results),'/',len(allids),'errors',len(errors),flush=True)
   write_json(ROOT/'detail-progress.json',{'completed':sorted(results),'errors':errors})
# Separate maintenance endpoint: preserves maintenance even if History omits any.
c=Client(ROOT/'evidence/maintenance')
seen=set();maintenance_complete=False
for page in range(1,100):
 d,m=c.get(BASE+'/api/v2/scheduled-maintenances.json?page='+str(page));items=d['scheduled_maintenances']
 requests.append(dict(m,resource='maintenance',page=page,count=len(items)))
 if not items:maintenance_complete=True;break
 sig=digest([i['id'] for i in items])
 if sig in seen:
  errors.append({'resource':'maintenance','error':'repeated page; history is alternative enumeration'});break
 seen.add(sig)
 for r in items:
  if r['id'] not in results:results[r['id']]={'raw':r,'platform':'statuspage','record_type':'maintenance','source_urls':[BASE+'/incidents/'+r['id'],m['url']],'retrieved_at_utc':m['retrieved_at_utc']}
components=original['components'];names={'rwppv331jlwc':'Claude.ai','0qbwn08sd68x':'Console','k8w3r06qmzrp':'API','yyzkbfz2thpt':'Claude Code','bpp5gb3hpjcl':'Cowork','0scnb50nvy53':'Government'}
for cid,g in names.items():components[cid]['group']=g
records=[r for r in results.values() if utc(r['raw']['created_at'])<utc(CUTOFF)]
coverage={'status':'enumerated' if not errors else 'incomplete','method':'HistoryIndex 3-month windows through pre-page-creation empty quarter plus per-ID detail API','cross_check':'History IDs matched to detail API; recent list comparison separately recorded','history_unique_ids':len(ids),'detail_count':len(results),'recent_list_missing_from_history':sorted(set(old)-set(ids)),'history_windows':len(windows),'page_created_at':created,'declared_data_available_since':None,'pagination_complete':not errors,'maintenance_api_complete':maintenance_complete,'errors':errors,'known_failed_path':'incidents.json?page=2 repeats page=1; not used to establish full coverage','boundary_policy':'Collected all History through before page creation; undisclosed or deleted records and pre-page incidents cannot be ruled out.'}
snapshot=dict(original,records=sorted(records,key=lambda r:r['raw']['created_at']),components=components,run_id='anthropic-20260927T161043Z',retrieved_at_utc=now(),requests=requests,coverage=coverage)
write_json(ROOT/'snapshot.json',snapshot);print(json.dumps({'records':len(records),'coverage':coverage},indent=2),flush=True)
