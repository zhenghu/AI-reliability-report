"""Read-only public status-page collectors with durable page-level checkpoints."""
from __future__ import annotations
import hashlib
import ipaddress
import json
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from core import component_map, digest, iso, require, utc, write_json

MAX_BYTES = 20 * 1024 * 1024


def public_url(url: str, origin: str | None = None) -> str:
    p = urllib.parse.urlsplit(url)
    require(p.scheme == 'https' and bool(p.hostname) and not p.username and not p.password,
            'Use a public HTTPS URL without credentials')
    require(p.port in (None, 443), 'Only HTTPS default port is allowed')
    require(not p.fragment, 'URL fragments are not network endpoints')
    if origin:
        require(p.netloc == urllib.parse.urlsplit(origin).netloc, 'Cross-origin redirect refused')
    try:
        addresses = {a[4][0] for a in socket.getaddrinfo(p.hostname, 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise OSError(f'Unable to resolve {p.hostname}; use the connected browser adapter and import saved JSON') from exc
    require(bool(addresses) and all(ipaddress.ip_address(x).is_global for x in addresses),
            'Private, loopback, link-local or reserved destinations refused')
    return url


class SameOriginRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl, req.full_url)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Client:
    def __init__(self, root: Path, delay: float = 0.3):
        require(delay >= 0, 'Delay must be nonnegative')
        self.root, self.delay, self.last = root, delay, 0.0
        self.root.mkdir(parents=True, exist_ok=True)
        # Do not inherit proxy credentials; never read tokens from the environment.
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), SameOriginRedirect())
        self.requests = 0

    def get(self, url: str, *, refresh: bool = False) -> tuple[dict, dict]:
        key = hashlib.sha256(url.encode()).hexdigest()
        body_path, meta_path = self.root / (key + '.json'), self.root / (key + '.meta.json')
        if not refresh and body_path.exists() and meta_path.exists():
            body, meta = body_path.read_bytes(), json.loads(meta_path.read_text())
            require(meta['url'] == url and hashlib.sha256(body).hexdigest() == meta['sha256'], 'Corrupt page cache')
            return json.loads(body), meta
        public_url(url)
        for attempt in range(3):
            time.sleep(max(0.0, self.delay - (time.monotonic() - self.last)))
            request = urllib.request.Request(url, headers={'User-Agent': 'incident-research/1.0 (public-read-only)',
                                                           'Accept': 'application/json'})
            try:
                with self.opener.open(request, timeout=30) as response:
                    self.requests += 1
                    body = response.read(MAX_BYTES + 1)
                    require(len(body) <= MAX_BYTES, 'Response exceeds 20 MiB; reduce window size')
                    data = json.loads(body)
                    require(isinstance(data, dict), 'Expected JSON object')
                    meta = {'url': url, 'final_url': response.url, 'status': response.status,
                            'retrieved_at_utc': iso(datetime.now(timezone.utc)),
                            'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body),
                            'cache_file': 'raw/' + body_path.name}
                body_path.write_bytes(body)
                write_json(meta_path, meta)
                self.last = time.monotonic()
                return data, meta
            except urllib.error.HTTPError as exc:
                if exc.code in (401, 403):
                    raise PermissionError(f'HTTP {exc.code}: protected or blocked endpoint, not bypassed: {url}') from exc
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise
                retry = exc.headers.get('Retry-After', '')
                time.sleep(min(float(retry) if retry.isdigit() else 2 ** attempt, 60))
        raise RuntimeError('Request retries exhausted')


def base_url(value: str) -> str:
    value = value if '://' in value else 'https://' + value
    p = urllib.parse.urlsplit(value)
    require(p.scheme == 'https' and p.hostname and not p.username and not p.password and not p.query,
            'Supply an HTTPS status-page entrance without query parameters or credentials')
    path = p.path.rstrip('/')
    if path.endswith('/history'):
        path = path[:-8]
    return urllib.parse.urlunsplit((p.scheme, p.netloc, path, '', ''))


def endpoint(base: str, path: str) -> str:
    return base.rstrip('/') + '/' + path.lstrip('/')


def discover(base: str, client, adapter: str) -> tuple[str, dict, dict, str]:
    host = urllib.parse.urlsplit(base).netloc
    candidates = [('incidentio', endpoint(base, f'proxy/{host}/summary')),
                  ('statuspage', endpoint(base, 'api/v2/summary.json'))]
    errors = []
    for kind, url in candidates:
        if adapter != 'auto' and adapter != kind:
            continue
        try:
            data, meta = client.get(url)
            if kind == 'incidentio':
                require(isinstance(data.get('summary'), dict) and 'structure' in data['summary'], 'Not incident.io JSON')
                api = endpoint(base, f'proxy/{host}')
            else:
                require('page' in data and isinstance(data.get('components'), list), 'Not Statuspage JSON')
                api = endpoint(base, 'api/v2')
            return kind, data, meta, api
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
    raise ValueError('No supported public JSON source confirmed. Inspect History/network with a connected browser; '
                     'import the saved native JSON. Do not infer that no history exists. ' + '; '.join(errors))


def collect(url: str, output: Path, *, company_id: str | None = None, company_name: str | None = None,
            start: str | None = None, end: str | None = None, adapter: str = 'auto',
            window_days: int = 30, max_pages: int = 500, client=None) -> dict:
    require(1 <= window_days <= 60 and max_pages > 0, 'window-days must be 1..60; max-pages positive')
    base = base_url(url)
    snapshot_file = output / 'snapshot.json'
    if output.exists() and any(output.iterdir()) and not snapshot_file.exists():
        raise ValueError('Non-empty output directory is not a resumable collection')
    output.mkdir(parents=True, exist_ok=True)
    client = client or Client(output / 'raw')
    if snapshot_file.exists():
        saved = json.loads(snapshot_file.read_text(encoding='utf-8'))
        require(saved['status_page_url'] == base, 'Resume source mismatch')
        if end:
            require(iso(end) == saved['cutoff_utc'], 'Resume cutoff cannot change')
        if start:
            require(iso(start) == saved.get('user_start_utc'), 'Resume start cannot change')
        if company_id:
            require(company_id == saved['company']['id'], 'Resume company mismatch')
        if company_name:
            require(company_name == saved['company']['name'], 'Resume company name mismatch')
        end = saved['cutoff_utc']
    else:
        saved = None
    cutoff = utc(end) if end else datetime.now(timezone.utc)
    require(cutoff <= datetime.now(timezone.utc) + timedelta(minutes=1), 'Cutoff cannot be in the future')
    kind, summary, meta, api = discover(base, client, adapter)
    provider = summary.get('summary', summary.get('page', {}))
    declared = provider.get('data_available_since')
    # Retrieve a cushion before the portal's declared start for backdated announcements.
    effective_start = utc(start) if start else (utc(declared) - timedelta(days=31) if declared else datetime(1970, 1, 1, tzinfo=timezone.utc))
    require(effective_start < cutoff, 'start must precede cutoff')
    ident = company_id or (saved or {}).get('company', {}).get('id') or re.sub('[^a-z0-9.-]+', '-', urllib.parse.urlsplit(base).hostname.lower())
    name = company_name or provider.get('name') or ident
    require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]*', ident) is not None, 'Invalid company ID')
    snapshot = {'schema_version': 1, 'platform': kind, 'company': {'id': ident, 'name': name},
                'status_page_url': base, 'start_utc': iso(effective_start), 'cutoff_utc': iso(cutoff),
                'user_start_utc': iso(start) if start else None, 'declared_data_available_since': declared,
                'retrieved_at_utc': meta['retrieved_at_utc'], 'run_id': digest([base, iso(effective_start), iso(cutoff)])[:20],
                'components': component_map(summary, kind), 'records': [], 'requests': [],
                'coverage': {'status': 'incomplete', 'selection': 'published_at_in_requested_window',
                             'boundary_policy': 'Backdated or carry-in impacts outside the publication window may be absent; '
                                                'this is not proof of complete impact coverage.',
                             'pagination_complete': False, 'cross_check': 'not_performed', 'errors': []}}
    records = {}

    def save():
        snapshot['records'] = sorted(records.values(), key=lambda x: x['raw']['id'])
        snapshot['coverage']['record_count'] = len(records)
        write_json(snapshot_file, snapshot)

    def ingest(items: list, request_meta: dict, record_type='incident'):
        require(isinstance(items, list), 'Missing incident list (not treated as empty)')
        snapshot['requests'].append(request_meta)
        for raw in items:
            require(isinstance(raw, dict) and raw.get('id'), 'Malformed incident object')
            when = raw.get('published_at') or raw.get('created_at')
            require(bool(when), 'Incident missing publication date')
            if not effective_start <= utc(when) < cutoff:
                continue
            incident_url = endpoint(base, 'incidents/' + urllib.parse.quote(raw['id'], safe=''))
            entry = {'raw': raw, 'platform': kind, 'record_type': raw.get('type', record_type),
                     'source_urls': [incident_url, request_meta['url']],
                     'retrieved_at_utc': request_meta['retrieved_at_utc']}
            previous = records.get(raw['id'])
            if previous and digest(previous['raw']) != digest(raw):
                snapshot['coverage'].setdefault('changed_record_ids', []).append(raw['id'])
            if previous:
                entry['source_urls'] = sorted(set(entry['source_urls'] + previous['source_urls']))
            records[raw['id']] = entry
        save()

    save()
    try:
        if kind == 'incidentio':
            begin, windows = effective_start, 0
            while begin < cutoff:
                require(windows < max_pages, 'Window safety limit reached; collection remains incomplete')
                finish = min(begin + timedelta(days=window_days), cutoff)
                query = urllib.parse.urlencode({'start_at': iso(begin), 'end_at': iso(finish)})
                data, info = client.get(endpoint(api, 'incidents') + '?' + query)
                require('incidents' in data, 'Response has no incidents key')
                # Public frontend contract is not stable: fail rather than discard a new cursor.
                require(not any(data.get(k) for k in ('next_cursor', 'next_page', 'has_more', 'pagination')),
                        'Unexpected pagination metadata; adapter needs updating')
                info = dict(info, window_start=iso(begin), window_end=iso(finish), returned=len(data['incidents']))
                ingest(data['incidents'], info)
                begin, windows = finish, windows + 1
            snapshot['coverage']['pagination_complete'] = True
            snapshot['coverage']['status'] = 'enumerated'
        else:
            for resource, list_key, record_type in [('incidents', 'incidents', 'incident'),
                                                    ('scheduled-maintenances', 'scheduled_maintenances', 'maintenance')]:
                seen, terminated = set(), False
                for page in range(1, max_pages + 1):
                    data, info = client.get(endpoint(api, resource + '.json') + '?page=' + str(page))
                    require(list_key in data, f'Missing {list_key} list')
                    items = data[list_key]
                    require(isinstance(items, list), 'Invalid history page')
                    sig = digest(sorted(str(x.get('id')) for x in items))
                    if not items:
                        terminated = True
                        snapshot['requests'].append(dict(info, page=page, returned=0, resource=resource))
                        break
                    require(sig not in seen, 'Pagination repeated a page; server may ignore page=. History incomplete')
                    seen.add(sig)
                    ingest(items, dict(info, page=page, returned=len(items), resource=resource), record_type)
                require(terminated, 'Page limit reached before an empty terminal page')
            snapshot['coverage']['pagination_complete'] = True
            snapshot['coverage']['status'] = 'enumerated'
        snapshot['coverage']['duplicate_policy'] = 'same ID deduplicated; separate IDs are not merged by title or root cause'
    except (OSError, ValueError, KeyError, TypeError) as exc:
        snapshot['coverage']['errors'].append(str(exc))
        snapshot['coverage']['status'] = 'incomplete'
    save()
    return snapshot
