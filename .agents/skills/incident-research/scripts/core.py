"""Evidence-preserving incident normalization and CSV interchange (stdlib only)."""
from __future__ import annotations
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = '1.0.0'
SEVERITIES = ('unknown', 'degraded_performance', 'partial_outage', 'full_outage')
STATUSPAGE_IMPACT = {'minor': 'degraded_performance', 'major': 'partial_outage', 'critical': 'full_outage'}
FIELDS = ('schema_version company_id company_name status_page_url source_platform incident_id '
          'incident_title record_type incident_status published_at_utc first_update_at_utc '
          'first_resolved_at_utc last_update_at_utc official_severity official_severity_codes_json '
          'assessed_severity severity_basis severity_scope service_groups_json components_json '
          'impact_start_at_utc impact_end_at_utc impact_seconds known_full_seconds '
          'known_full_partial_seconds known_all_seconds time_basis time_complete '
          'right_censored review_status analysis_summary root_cause root_cause_status '
          'evidence_json updates_json impact_intervals_json official_intervals_json '
          'source_urls_json raw_incident_json raw_sha256 quality_flags_json '
          'requested_start_utc cutoff_utc retrieved_at_utc coverage_status collection_run_id '
          'analysis_version spreadsheet_escaped_fields_json').split()
JSON_FIELDS = [f for f in FIELDS if f.endswith('_json')]


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def utc(value: str) -> datetime:
    require(isinstance(value, str), 'Timestamp must be an ISO string')
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError(f'Invalid timestamp: {value!r}') from exc
    require(dt.tzinfo is not None, f'Timestamp needs timezone: {value!r}')
    return dt.astimezone(timezone.utc)


def iso(value: str | datetime) -> str:
    return (utc(value) if isinstance(value, str) else value.astimezone(timezone.utc)).isoformat().replace('+00:00', 'Z')


def js(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True, allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(js(value).encode()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temp.replace(path)


def text(value: Any) -> str:
    """Preserve Markdown or recursively extract text-only legacy rich text."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return '\n'.join(filter(None, (text(x) for x in value)))
    if isinstance(value, dict):
        for key in ('markdown', 'body', 'message_string', 'text'):
            if isinstance(value.get(key), str) and value[key]:
                return value[key]
        return text(value.get('text_node', value.get('content', [])))
    return ''


def highest(values) -> str:
    return max((v for v in values if v in SEVERITIES), key=SEVERITIES.index, default='unknown')


def union_seconds(intervals: list[dict], allowed=SEVERITIES[1:], start=None, end=None) -> float:
    pairs = []
    for x in intervals:
        if x['severity'] not in allowed:
            continue
        a, b = utc(x['start_at']), utc(x['end_at'])
        if start is not None:
            a = max(a, start)
        if end is not None:
            b = min(b, end)
        if a < b:
            pairs.append((a, b))
    total, right = 0.0, None
    for a, b in sorted(pairs):
        if right is None or a >= right:
            total += (b - a).total_seconds()
        elif b > right:
            total += (b - right).total_seconds()
        right = b if right is None else max(right, b)
    return total


def component_map(summary: dict, platform: str) -> dict:
    result = {}
    if platform in ('incidentio', 'generic'):
        summary = summary.get('summary', summary)
        result = {c['id']: {'id': c['id'], 'name': c.get('name', c['id']), 'group': 'Unmapped'}
                  for c in summary.get('components', [])}
        for item in summary.get('structure', {}).get('items', []):
            group = item.get('group', {})
            for c in group.get('components', []):
                cid = c['component_id']
                result[cid] = {'id': cid, 'name': c.get('name', result.get(cid, {}).get('name', cid)),
                               'group': group.get('name', 'Unmapped')}
    else:
        components = summary.get('components', [])
        names = {c['id']: c.get('name', c['id']) for c in components}
        for c in components:
            if not c.get('group', False):
                result[c['id']] = {'id': c['id'], 'name': c.get('name', c['id']),
                                   'group': names.get(c.get('group_id'), c.get('name', c['id']))}
    return result


def normalized_updates(raw: dict, platform: str) -> list[dict]:
    source = raw.get('updates', []) if platform in ('incidentio', 'generic') else raw.get('incident_updates', [])
    result = []
    for u in source:
        when = u.get('published_at') or u.get('display_at') or u.get('created_at')
        if not when:
            continue
        result.append({'id': u.get('id', ''), 'at': iso(when),
                       'status': u.get('to_status', u.get('status', '')),
                       'body': u.get('message_string') or text(u.get('message', u.get('body', ''))),
                       'component_statuses': u.get('component_statuses', u.get('affected_components', []))})
    return sorted(result, key=lambda u: utc(u['at']))


def lifecycle_windows(updates: list[dict], cutoff: datetime) -> list[tuple]:
    """Do not extend resolved incidents to the later postmortem publication."""
    windows, begin = [], None
    for u in updates:
        when = utc(u['at'])
        if when > cutoff:
            continue
        if u['status'] in ('resolved', 'postmortem', 'completed'):
            if begin is not None and begin < when:
                windows.append((begin, when))
            begin = None
        elif u['status'] in ('investigating', 'identified', 'monitoring', 'in_progress', 'verifying'):
            if begin is None:
                begin = when
    if begin is not None and begin < cutoff:
        windows.append((begin, cutoff))
    return windows


def normalize_record(entry: dict, snapshot: dict, review: dict | None = None) -> dict:
    raw = entry['raw']
    platform = entry.get('platform', snapshot['platform'])
    require(platform in ('incidentio', 'statuspage', 'generic'), 'Import requires a supported native JSON shape')
    require(isinstance(raw, dict) and isinstance(raw.get('id'), str) and bool(raw['id']), 'Incident needs a string ID')
    mapping = snapshot.get('components', {})
    cutoff = utc(snapshot['cutoff_utc'])
    updates = normalized_updates(raw, platform)
    published = raw.get('published_at') or raw.get('created_at')
    require(bool(published), f"{raw['id']}: missing publication timestamp")
    published = iso(published)
    resolved = [u['at'] for u in updates if u['status'] in ('resolved', 'postmortem', 'completed')]
    status = raw.get('status', '')
    record_type = 'maintenance' if (entry.get('record_type') == 'maintenance' or raw.get('type') == 'maintenance'
                                  or status in ('scheduled', 'in_progress', 'verifying', 'completed')
                                  or raw.get('scheduled_for')) else 'incident'
    listed = raw.get('affected_components', []) if platform in ('incidentio', 'generic') else raw.get('components', [])
    cids = sorted(({x.get('component_id', x.get('id', '')) for x in listed}
                   | {x.get('component_id', '') for x in raw.get('component_impacts', [])}) - {''})
    components = [mapping.get(cid, {'id': cid, 'name': cid, 'group': 'Unmapped'}) for cid in cids]
    groups = sorted({x['group'] for x in components}) or ['Unmapped']
    codes = [x.get('status', '') for x in listed] if platform in ('incidentio', 'generic') else [raw.get('impact', '')]
    raw_intervals = (raw.get('component_impacts') or raw.get('status_summaries') or []) if platform != 'generic' else []
    codes += [x.get('status', x.get('worst_component_status', '')) for x in raw_intervals]
    codes = [] if platform == 'generic' else codes
    official = highest(codes if platform in ('incidentio', 'generic') else [STATUSPAGE_IMPACT.get(c, 'unknown') for c in codes])
    flags = ['synthetic_test_data'] if snapshot.get('synthetic', False) else []
    if official == 'unknown':
        flags.append('missing_official_severity')
    if groups == ['Unmapped']:
        flags.append('unmapped_service')
    flags.append('component_map_is_current_not_historical')
    if platform == 'statuspage':
        flags.append('impact_mapping_is_a_convention_not_proof_of_total_outage')
    windows = lifecycle_windows(updates, cutoff)
    intervals = []
    terminal = status in ('resolved', 'postmortem', 'completed')
    for x in raw_intervals:
        severity = x.get('status', x.get('worst_component_status'))
        if severity not in SEVERITIES[1:] or not x.get('start_at'):
            continue
        a = utc(x['start_at'])
        raw_end = x.get('end_at')
        b = utc(raw_end) if raw_end else cutoff
        basis = 'official_component_interval' if 'component_id' in x else 'official_status_summary'
        censored = not raw_end or b > cutoff
        if b < a:
            flags.append('invalid_official_interval')
            continue
        prior_states = [u['status'] for u in updates if utc(u['at']) <= a]
        if prior_states and prior_states[-1] in ('resolved', 'postmortem', 'completed'):
            flags.append('official_interval_after_resolution_requires_review')
            continue
        # Resolved updates provide an upper fence, not necessarily the real restoration time.
        # A description-backed review can supply a different explicit impact timeline.
        fences = [utc(u['at']) for u in updates if utc(u['at']) >= a
                  and u['status'] in ('resolved', 'postmortem', 'completed')]
        if terminal and fences and b > min(fences):
            b = min(fences)
            flags.append('official_interval_clipped_at_resolution')
        if terminal and not raw_end and not fences:
            flags.append('resolved_incident_missing_interval_end')
            continue
        b = min(b, cutoff)
        if a >= b:
            continue
        cid = x.get('component_id')
        sg = [mapping.get(cid, {}).get('group', 'Unmapped')] if cid else groups
        intervals.append({'start_at': iso(a), 'end_at': iso(b), 'severity': severity,
                          'service_groups': sg, 'component_id': cid, 'time_basis': basis,
                          'right_censored': censored and b == cutoff})
    if not intervals and official != 'unknown':
        for a, b in windows:
            intervals.append({'start_at': iso(a), 'end_at': iso(b), 'severity': official,
                              'service_groups': groups, 'component_id': None,
                              'time_basis': 'announcement_proxy', 'right_censored': not terminal and b == cutoff})
        if intervals:
            flags.append('announcement_proxy_not_actual_downtime')
    assessed, severity_basis = official, ('official_component_status' if platform in ('incidentio', 'generic') else 'mapped_official_impact')
    analysis_summary, root_cause, root_cause_status = '', '', 'not_assessed'
    evidence = []
    review_status = 'needs_review'
    review_json = None
    if review is not None:
        review_json = validate_review(review, entry, snapshot, updates)
        evidence = review['evidence']
        assessed = review.get('severity', official)
        severity_basis = 'evidence_backed_assessment'
        groups = review.get('service_groups', groups)
        analysis_summary = review.get('summary', '')
        root_cause = review.get('root_cause', '')
        root_cause_status = review.get('root_cause_status', 'not_assessed')
        if 'intervals' in review:
            intervals = review['intervals']
        elif assessed != official or 'service_groups' in review:
            # Changing overall severity/groups cannot silently relabel an existing stage timeline.
            require(not intervals, 'Changing severity/services requires an explicit reviewed interval list')
        review_status = 'assessed'
    if not intervals:
        flags.append('unknown_impact_time')
    if assessed == 'unknown':
        flags.append('unknown_assessed_severity')
    if any('Unmapped' in x['service_groups'] for x in intervals):
        flags.append('unmapped_interval_service')
    if intervals and highest(x['severity'] for x in intervals) != assessed:
        # Peak official component list may include a past state: retain, flag for review.
        flags.append('peak_severity_differs_from_timeline')
    seconds = union_seconds(intervals)
    first = min((x['start_at'] for x in intervals), key=utc, default=None)
    last = max((x['end_at'] for x in intervals), key=utc, default=None)
    time_complete = bool(intervals) and bool(review and review.get('time_complete', False))
    if not time_complete:
        flags.append('impact_timeline_not_fully_verified')
    urls = sorted(set(entry.get('source_urls', [])))
    require(bool(urls), 'Each incident requires a source URL')
    row = {
        'schema_version': 'incident-csv-v1', 'company_id': snapshot['company']['id'],
        'company_name': snapshot['company']['name'], 'status_page_url': snapshot['status_page_url'],
        'source_platform': platform, 'incident_id': raw['id'], 'incident_title': raw.get('name', ''),
        'record_type': record_type, 'incident_status': status, 'published_at_utc': published,
        'first_update_at_utc': updates[0]['at'] if updates else None,
        'first_resolved_at_utc': resolved[0] if resolved else raw.get('resolved_at'),
        'last_update_at_utc': updates[-1]['at'] if updates else None,
        'official_severity': official, 'official_severity_codes_json': sorted(set(codes) - {''}),
        'assessed_severity': assessed, 'severity_basis': severity_basis,
        'severity_scope': 'affected_component_or_documented_scope_not_whole_company',
        'service_groups_json': groups, 'components_json': components,
        'impact_start_at_utc': first, 'impact_end_at_utc': last,
        'impact_seconds': seconds if intervals else None,
        'known_full_seconds': union_seconds(intervals, ['full_outage']) if intervals else None,
        'known_full_partial_seconds': union_seconds(intervals, ['full_outage', 'partial_outage']) if intervals else None,
        'known_all_seconds': seconds if intervals else None,
        'time_basis': ';'.join(sorted({x['time_basis'] for x in intervals})) or 'unknown',
        'time_complete': time_complete, 'right_censored': any(x.get('right_censored', False) for x in intervals),
        'review_status': review_status, 'analysis_summary': analysis_summary, 'root_cause': root_cause,
        'root_cause_status': root_cause_status, 'evidence_json': evidence, 'updates_json': updates,
        'impact_intervals_json': intervals, 'official_intervals_json': raw_intervals,
        'source_urls_json': urls, 'raw_incident_json': raw, 'raw_sha256': digest(raw),
        'quality_flags_json': sorted(set(flags)), 'requested_start_utc': snapshot['start_utc'],
        'cutoff_utc': snapshot['cutoff_utc'], 'retrieved_at_utc': entry.get('retrieved_at_utc', snapshot['retrieved_at_utc']),
        'coverage_status': snapshot['coverage']['status'], 'collection_run_id': snapshot['run_id'],
        'analysis_version': VERSION, 'spreadsheet_escaped_fields_json': []}
    if review_json:
        row['evidence_json'] = {'items': evidence, 'assessment': review_json}
    return row


def validate_review(review: dict, entry: dict, snapshot: dict, updates: list[dict]) -> dict:
    """Verify provenance and syntax; semantic adequacy remains the agent's responsibility."""
    raw = entry['raw']
    require(review.get('source_record_sha256') == digest(raw), 'Stale assessment: raw SHA-256 mismatch')
    require(review.get('incident_id') == raw['id'], 'Assessment incident ID mismatch')
    require(review.get('severity', 'unknown') in SEVERITIES, 'Invalid assessed severity')
    sources = {url: '\n'.join([raw.get('name', ''), *[u['body'] for u in updates],
                              text(raw.get('write_up_contents', raw.get('postmortem', '')))])
               for url in entry.get('source_urls', [])}
    for source in entry.get('evidence_documents', []):
        require(source.get('sha256') == hashlib.sha256(source['text'].encode()).hexdigest(), 'Evidence document hash mismatch')
        sources[source['url']] = source['text']
    evidence = review.get('evidence', [])
    require(isinstance(evidence, list) and bool(evidence), 'Assessment requires evidence')
    for e in evidence:
        require(e.get('kind') in ('severity', 'time', 'service', 'root_cause', 'summary'), 'Invalid evidence kind')
        quote = e.get('quote', '')
        require(bool(quote) and quote in sources.get(e.get('source_url'), ''), 'Evidence quote not present in saved source')
        if e.get('update_id'):
            require(any(u['id'] == e['update_id'] and quote in u['body'] for u in updates), 'Evidence update ID mismatch')
    kinds = {e['kind'] for e in evidence}
    if 'severity' in review:
        require('severity' in kinds, 'Severity change requires severity evidence')
    if 'service_groups' in review:
        require('service' in kinds, 'Service mapping requires service evidence')
        require(isinstance(review['service_groups'], list) and bool(review['service_groups'])
                and all(isinstance(g, str) and g for g in review['service_groups']), 'Invalid service groups')
    require(review.get('root_cause_status', 'not_assessed') in ('not_assessed', 'not_disclosed', 'vendor_stated', 'hypothesis'),
            'Invalid root_cause_status')
    if review.get('root_cause'):
        require('root_cause' in kinds, 'Root-cause statement requires evidence')
        require(review.get('root_cause_status') in ('vendor_stated', 'hypothesis'), 'Root-cause attribution required')
    require(type(review.get('time_complete', False)) is bool, 'time_complete must be boolean')
    intervals = review.get('intervals', [])
    for x in intervals:
        require('time' in kinds, 'Reviewed interval requires time evidence')
        require(utc(x['start_at']) < utc(x['end_at']) <= utc(snapshot['cutoff_utc']), 'Invalid reviewed time interval')
        require(x['severity'] in SEVERITIES[1:], 'Reviewed interval requires a known severity')
        require(x.get('time_basis') in ('explicit_impact', 'timezone_inferred', 'official_component_interval',
                                      'official_status_summary', 'announcement_proxy'), 'Invalid time_basis')
        require(isinstance(x.get('service_groups'), list) and bool(x['service_groups'])
                and all(isinstance(g, str) and g for g in x['service_groups']), 'Interval requires services')
        if 'service_groups' in review:
            require(set(x['service_groups']) <= set(review['service_groups']), 'Interval services outside assessed scope')
        require(type(x.get('right_censored', False)) is bool, 'right_censored must be boolean')
        indices = x.get('evidence_indices', [])
        require(bool(indices) and all(type(i) is int and 0 <= i < len(evidence) for i in indices), 'Interval evidence indices invalid')
        require(any(evidence[i]['kind'] == 'time' for i in indices), 'Interval needs a time evidence link')
    if intervals:
        require(highest(x['severity'] for x in intervals) == review.get('severity'), 'Reviewed peak must match intervals')
    require(not review.get('time_complete') or bool(intervals), 'Complete timing requires explicit reviewed intervals')
    if review.get('time_complete'):
        require(all(x['time_basis'] != 'announcement_proxy' for x in intervals), 'Announcement proxy cannot prove complete actual timing')
    return review


def export_csv(snapshot: dict, output: Path, assessments: dict | None = None) -> dict:
    require(snapshot.get('schema_version') == 1, 'Unsupported snapshot schema')
    require(utc(snapshot['start_utc']) < utc(snapshot['cutoff_utc']), 'Empty or negative collection range')
    if assessments is not None:
        require(assessments.get('schema_version') == 1, 'Unsupported assessment schema')
    require(snapshot.get('coverage', {}).get('status') in ('enumerated', 'incomplete', 'unverified'), 'Missing collection coverage')
    reviews = (assessments or {}).get('records', [])
    by_id = {r['incident_id']: r for r in reviews}
    require(len(by_id) == len(reviews), 'Duplicate assessment IDs')
    entries = snapshot['records']
    ids = [e['raw']['id'] for e in entries]
    require(len(ids) == len(set(ids)), 'Duplicate incident IDs in snapshot')
    require(set(by_id) <= set(ids), 'Assessment refers to absent incident')
    rows = [normalize_record(e, snapshot, by_id.get(e['raw']['id'])) for e in entries]
    rows.sort(key=lambda r: (utc(r['published_at_utc']), r['incident_id']))
    require(not output.exists() and not output.with_suffix('.validation.json').exists(),
            'Output already exists; choose a new snapshot filename')
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(output.name + '.tmp')
    try:
        with tmp.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for original in rows:
                row, escaped = dict(original), []
                for key, value in row.items():
                    if key in JSON_FIELDS:
                        row[key] = js(value)
                    elif isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')):
                        row[key] = "'" + value
                        escaped.append(key)
                row['spreadsheet_escaped_fields_json'] = js(escaped)
                writer.writerow(row)
        result = validate_csv(tmp)
        require(result['rows'] == len(rows), 'CSV row count changed during serialization')
        tmp.replace(output)
    finally:
        tmp.unlink(missing_ok=True)
    result['csv'] = str(output)
    result['csv_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    result['collection_coverage'] = snapshot['coverage']
    write_json(output.with_suffix('.validation.json'), result)
    return result


def read_csv(path: Path) -> list[dict]:
    csv.field_size_limit(128 * 1024 * 1024)
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        require(reader.fieldnames == FIELDS, 'Unexpected CSV schema/column order')
        result = []
        for row in reader:
            require(None not in row and all(v is not None for v in row.values()), 'Malformed CSV row')
            for key in JSON_FIELDS:
                row[key] = json.loads(row[key])
            for key in row['spreadsheet_escaped_fields_json']:
                require(key in row and row[key].startswith("'"), 'Invalid formula-escape metadata')
                row[key] = row[key][1:]
            result.append(row)
        return result


def validate_csv(path: Path) -> dict:
    rows, keys, missing_time, unknown = read_csv(path), set(), 0, 0
    for row in rows:
        require(row['schema_version'] == 'incident-csv-v1', 'Unexpected row schema')
        key = (row['company_id'], row['incident_id'])
        require(key not in keys, 'Duplicate CSV incident key')
        keys.add(key)
        require(row['raw_sha256'] == digest(row['raw_incident_json']), 'Raw JSON checksum mismatch')
        require(row['incident_id'] == row['raw_incident_json']['id'], 'Raw ID mismatch')
        require(row['assessed_severity'] in SEVERITIES, 'Invalid CSV severity')
        require(row['record_type'] in ('incident', 'maintenance'), 'Invalid record type')
        require(row['coverage_status'] in ('enumerated', 'incomplete', 'unverified'), 'Invalid coverage status')
        for key2 in ('time_complete', 'right_censored'):
            require(row[key2] in ('True', 'False'), 'Invalid CSV boolean')
        for key2 in ('published_at_utc', 'first_update_at_utc', 'first_resolved_at_utc', 'last_update_at_utc',
                     'impact_start_at_utc', 'impact_end_at_utc', 'requested_start_utc', 'cutoff_utc', 'retrieved_at_utc'):
            if row[key2]:
                utc(row[key2])
        intervals = row['impact_intervals_json']
        for interval in intervals:
            require(utc(interval['start_at']) < utc(interval['end_at']) <= utc(row['cutoff_utc']), 'Invalid CSV interval')
            require(interval['severity'] in SEVERITIES[1:], 'Unknown interval severity')
        for col, allowed in [('known_full_seconds', ['full_outage']),
                             ('known_full_partial_seconds', ['full_outage', 'partial_outage']),
                             ('known_all_seconds', SEVERITIES[1:]), ('impact_seconds', SEVERITIES[1:])]:
            expected = union_seconds(intervals, allowed)
            require((not intervals and row[col] == '') or (bool(intervals) and abs(float(row[col]) - expected) < 1e-6),
                    'CSV duration/interval mismatch')
        missing_time += int(not intervals and row['record_type'] == 'incident')
        unknown += int(row['assessed_severity'] == 'unknown' and row['record_type'] == 'incident')
    years = {}
    for row in rows:
        year = str(utc(row['published_at_utc']).year)
        years.setdefault(year, {'incidents': 0, 'maintenance': 0})
        years[year]['incidents' if row['record_type'] == 'incident' else 'maintenance'] += 1
    return {'schema_version': 1, 'by_publication_year_utc': years, 'rows': len(rows), 'unique_incidents_and_maintenance': len(keys),
            'incidents': sum(r['record_type'] == 'incident' for r in rows),
            'maintenance': sum(r['record_type'] == 'maintenance' for r in rows),
            'unknown_time_records': missing_time, 'unknown_severity_records': unknown,
            'validation': 'passed', 'semantic_evidence_validation': 'agent_responsibility'}
