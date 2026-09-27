"""Public Flashduty snapshot collector; resume from saved response bytes, no credentials."""
import json, re, gzip, hashlib, time, urllib.request
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]; RAW=ROOT/'raw'
CUTOFF='2026-09-27T19:36:20Z'
BASE='https://status.deepseek.com'; API=BASE+'/api/status-page/6410630422455'
def iso(t): return datetime.fromtimestamp(t,timezone.utc).isoformat().replace('+00:00','Z')
def stamp(s):return int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp())
def fetch(url,name):
 p=RAW/name;meta=RAW/(name+'.meta.json')
 if not meta.exists():
  req=urllib.request.Request(url,headers={'User-Agent':'Public-status-research/1.0','Accept-Encoding':'identity'})
  try:
   with urllib.request.urlopen(req,timeout=40) as r:
    b=r.read();h={k:v for k,v in r.headers.items() if k.lower() not in {'set-cookie','authorization','cookie','proxy-authorization'}};status=r.status
  except Exception as exc:
   with (ROOT/'collection-errors.jsonl').open('a') as f:f.write(json.dumps({'url':url,'at':iso(time.time()),'error':str(exc)})+'\n')
   raise
  p.write_bytes(b);meta.write_text(json.dumps({'url':url,'retrieved_at_utc':iso(time.time()),'status':status,'headers':h,'sha256':hashlib.sha256(b).hexdigest(),'hash_object':'HTTP response body bytes'},ensure_ascii=False,indent=2))
  time.sleep(.15)
 b=p.read_bytes();return (gzip.decompress(b) if b[:2]==b'\x1f\x8b' else b).decode()
def rsc(text):
 out=[]
 for s in re.findall(r'<script[^>]*>(.*?)</script>',text,re.S):
  m=re.search(r'self.__next_f.push\((.*)\)',s,re.S)
  if m:
   a=json.loads(m[1]);
   if len(a)>1 and isinstance(a[1],str):out.append(a[1])
 return ''.join(out)
def extract(text,key):
 dec=json.JSONDecoder();found=[]
 for m in re.finditer('"'+key+'":',text):
  try:found.append(dec.raw_decode(text[m.end():])[0])
  except ValueError: pass
 return found
if __name__=='__main__':
 active=json.loads(fetch(API+'/summary/active','active.json'))
 (ROOT/'page.json').write_text(json.dumps(active,ensure_ascii=False,indent=2))
 records={};windows=[];impacts=[]
 for year in range(2024,2027):
  for month in range(1,13):
   a=stamp(f'{year}-{month:02}-01T00:00:00Z');b=stamp(f'{year+month//12}-{month%12+1:02}-01T00:00:00Z')
   if a>=stamp(CUTOFF):continue
   b=min(b,stamp(CUTOFF));tag=f'{year}-{month:02}'
   url=f'{API}/change/list?start_at_seconds={a}&end_at_seconds={b}'
   data=json.loads(fetch(url,'list-'+tag+'.json'))['data'];assert 'items' in data
   items=data['items'];windows.append({'start':iso(a),'end':iso(b),'count':len(items),'ids':[x['change_id'] for x in items],'url':url,'extra_keys':list(set(data)-{'items'})})
   for x in items:records[x['change_id']]=x
   st=json.loads(fetch(f'{API}/summary/structure?start_at_from_seconds={a}&start_at_to_seconds={b}','structure-'+tag+'.json'))['data']
   impacts.extend(st.get('component_impacts',[]))
   print(tag,len(items),flush=True)
 (ROOT/'enumeration.json').write_text(json.dumps(windows,indent=2))
 for id in sorted(records):
  x=json.loads(fetch(API+f'/change/info?change_id={id}',f'detail-{id}.json'))['data']
  records[id]=x
 (ROOT/'records.json').write_text(json.dumps(list(records.values()),ensure_ascii=False,indent=2))
 (ROOT/'official-impacts.json').write_text(json.dumps(list({json.dumps(x,sort_keys=True):x for x in impacts}.values()),ensure_ascii=False,indent=2))
 checks=[]
 for year,month in [(y,m) for y in range(2024,2027) for m in range(2,13,2) if y<2026 or m<=8]+[(2026,9)]:
  tag=f'{year}-{month:02}';u=BASE+'/history?month='+tag
  s=rsc(fetch(u,'history-'+tag+'.html')); arr=extract(s,'initialChanges')
  checks.append({'url':u,'ids':[x['change_id'] for a in arr for x in a]})
 (ROOT/'history-crosscheck.json').write_text(json.dumps(checks,indent=2))
 print('DONE',len(records),len(impacts))
