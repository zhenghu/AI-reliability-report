"""Audit frozen input without changing it; Python standard library only."""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import sys

csv.field_size_limit(sys.maxsize)
parser = argparse.ArgumentParser()
parser.add_argument('input', type=Path)
args = parser.parse_args()
out = Path(__file__).resolve().parent

def node_text(node):
    if isinstance(node, list):
        return '\n'.join(filter(None, (node_text(x) for x in node)))
    if not isinstance(node, dict):
        return ''
    if isinstance(node.get('text'), str):
        return node['text']
    return '\n'.join(filter(None, (node_text(x) for x in node.get('content', []))))

def message_text(message):
    if not message:
        return ''
    if isinstance(message, str):
        return message
    if isinstance(message, list):
        return '\n'.join(message_text(x) for x in message)
    return message.get('markdown') or node_text(message.get('text_node', message))

rows = list(csv.DictReader(args.input.open(encoding='utf-8-sig')))
assert len({r['incident_id'] for r in rows}) == len(rows), 'Duplicate incident IDs'
reviews = []
for r in rows:
    if not r['write_up_contents_json']:
        continue
    obj = json.loads(r['write_up_contents_json'])
    body = message_text(obj)
    assert body.strip(), r['incident_id']
    reviews.append(dict(incident_id=r['incident_id'], title=r['incident_title'],
        published_at_utc=r['published_at_utc'], source_url=r['source_url'],
        write_up_url=r['write_up_url'] or r['source_url']+'/write-up',
        extraction='markdown' if isinstance(obj,dict) and obj.get('markdown') else 'text_node',
        text=body, text_sha256=hashlib.sha256(body.encode()).hexdigest()))

incidents = [r for r in rows if r['record_type']=='incident']
annual = collections.Counter(r['publication_year_utc'] for r in incidents)
annual_reviews = collections.Counter(r['published_at_utc'][:4] for r in reviews)
duplicate_bodies = collections.defaultdict(list)
for r in reviews:
    duplicate_bodies[r['text_sha256']].append(r['incident_id'])
summary = dict(input_name=args.input.name,
    input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
    rows=len(rows), fields=len(rows[0]), record_types=dict(collections.Counter(r['record_type'] for r in rows)),
    updates=sum(int(r['update_count']) for r in rows),
    retrieved_at_utc=sorted(set(r['retrieved_at_utc'] for r in rows)),
    writeups=len(reviews), writeup_share_of_incident_records=len(reviews)/len(incidents),
    extraction_types=dict(collections.Counter(r['extraction'] for r in reviews)),
    annual=[dict(year=y, incidents=n, writeups=annual_reviews[y]) for y,n in sorted(annual.items())],
    identical_writeup_groups=[v for v in duplicate_bodies.values() if len(v)>1],
    limitations=['Write-up coverage is not root-cause disclosure coverage.',
        'No-write-up incidents may still contain causes in updates; these are not fully adjudicated here.',
        'Publication year is not necessarily actual impact year.',
        'Exact text deduplication does not establish independent physical root causes.'])
(out/'writeups.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2)+'\n')
(out/'verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
