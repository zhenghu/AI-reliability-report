import json,sys
from pathlib import Path
D=json.load(open(Path(__file__).resolve().parents[2]/'v1.0/review-docket.json'))
M={'rwppv331jlwc':'ai','0qbwn08sd68x':'console','k8w3r06qmzrp':'API','yyzkbfz2thpt':'code','bpp5gb3hpjcl':'cowork','0scnb50nvy53':'gov'}
S={'operational':'O','degraded_performance':'D','partial_outage':'P','major_outage':'F'}
for r in D[int(sys.argv[1]):int(sys.argv[2])]:
 print('\n',r['n'],r['id'],r['title'],r['components'])
 for u in reversed(r['updates']): print(u['id'],u['display_at'],u['status'],u['body'],'|',','.join(M.get(x['code'],x['code'])+':'+S.get(x['new_status'],x['new_status']) for x in (u['affected_components'] or [])))
