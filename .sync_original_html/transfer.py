"""Lossless transfer of the user-approved original HTML; never render the report."""
import base64
import hashlib
import json
import lzma
import os
import re
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path('.sync_original_html')
META = json.loads((ROOT / 'metadata.json').read_text())
REPO = 'zhenghu/AI-reliability-report'
ARCHIVE = 'OpenAI/2026-09-27/v1.1/'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def check(ok, message):
    if not ok:
        raise RuntimeError(message)

check(os.environ.get('GITHUB_REPOSITORY') == REPO, 'Unexpected destination repository')
# Reuse byte-identical existing artwork. SVG differences are only deterministic
# byte substitutions for original IDs/date, verified against the ORIGINAL hashes.
# No plotting or HTML template rendering occurs in this transfer.
images = []
for item in META['images']:
    data = subprocess.check_output(['git', 'show', META['base_commit'] + ':' + ARCHIVE + item['path']])
    if item['mime'] == 'image/svg+xml':
        ids = re.findall(rb'id="([mp][0-9a-f]{10})"', data)
        check(len(ids) == len(item['ids']) and len(ids) == len(set(ids)), 'SVG ID count mismatch: ' + item['path'])
        canon_ids = {v: ('ORIGINAL_ID_%02d' % i).encode() for i, v in enumerate(ids)}
        canonical = re.sub(rb'\b[mp][0-9a-f]{10}\b', lambda m: canon_ids[m[0]], data)
        canonical = re.sub(rb'<dc:date>.*?</dc:date>', b'<dc:date>ORIGINAL_DATE</dc:date>', canonical)
        check(sha(canonical) == item['canonical_sha256'], 'SVG artwork differs: ' + item['path'])
        original_ids = {v: w.encode() for v, w in zip(ids, item['ids'])}
        data = re.sub(rb'\b[mp][0-9a-f]{10}\b', lambda m: original_ids[m[0]], data)
        data, count = re.subn(rb'<dc:date>.*?</dc:date>', b'<dc:date>' + item['date'].encode() + b'</dc:date>', data)
        check(count == 1, 'SVG date count mismatch')
    check(len(data) == item['bytes'] and sha(data) == item['sha256'], 'Original image bytes differ: ' + item['path'])
    images.append(b'data:' + item['mime'].encode() + b';base64,' + base64.b64encode(data))
print(json.dumps({'verified_original_images': len(images), 'mode': 'lossless transfer, no rendering'}))
if not (ROOT / 'parts.json').exists():
    print('Image preflight passed. Original HTML body has not been uploaded yet.')
    raise SystemExit(0)
parts = json.loads((ROOT / 'parts.json').read_text())
check(len(parts) == META['parts_count'], 'Incomplete body transfer')
encoded = []
for item in parts:
    data = (ROOT / item['file']).read_bytes()
    check(sha(data) == item['sha256'], 'Body transfer chunk failed hash: ' + item['file'])
    encoded.append(data.strip())
compressed = base64.b64decode(b''.join(encoded), validate=True)
check(sha(compressed) == META['transport_sha256'], 'Compressed body checksum mismatch')
body = lzma.decompress(compressed)
check(sha(body) == META['template_sha256'], 'Original body checksum mismatch')
for index, image in enumerate(images):
    marker = ('@@EXACT_ORIGINAL_IMAGE_%02d@@' % index).encode()
    check(body.count(marker) == 1, 'Image placeholder count mismatch')
    body = body.replace(marker, image)
check(len(body) == META['source_bytes'] and sha(body) == META['source_sha256'], 'Complete HTML differs from original')
git_sha = hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()
check(git_sha == META['source_git_blob'], 'Original Git blob mismatch')
match = re.search(rb'<script[^>]*id="audit-data"[^>]*>(.*?)</script>', body, re.S)
check(match is not None and len(json.loads(match[1])) == 1006, 'Original incident index missing')
headers = {'Authorization': 'Bearer ' + os.environ['GH_TOKEN'], 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json', 'X-GitHub-Api-Version': '2022-11-28'}
url = 'https://api.github.com/repos/' + REPO + '/git/blobs'
request = urllib.request.Request(url, data=json.dumps({'content': base64.b64encode(body).decode(), 'encoding': 'base64'}).encode(), headers=headers, method='POST')
with urllib.request.urlopen(request, timeout=90) as response:
    stored = json.load(response)
check(stored['sha'] == git_sha, 'Stored Git blob differs')
# Read back the uploaded blob from GitHub and recompute SHA-256.
with urllib.request.urlopen(urllib.request.Request(url + '/' + git_sha, headers=headers), timeout=90) as response:
    fetched = json.load(response)
check(fetched['encoding'] == 'base64', 'Unexpected GitHub blob encoding')
received = base64.b64decode(fetched['content'])
check(received == body and sha(received) == META['source_sha256'], 'Remote roundtrip failed')
print(json.dumps({'uploaded_blob_sha': git_sha, 'sha256': sha(received), 'bytes': len(received), 'incident_index_records': 1006, 'remote_roundtrip': 'passed', 'byte_identical_to_local_original': True}))
# Remove only the temporary branch created for this one-off transfer.
cleanup = urllib.request.Request('https://api.github.com/repos/' + REPO + '/git/refs/heads/chore/sync-original-openai-html', headers=headers, method='DELETE')
with urllib.request.urlopen(cleanup, timeout=30) as response:
    print('Temporary transfer branch removed:', response.status)
