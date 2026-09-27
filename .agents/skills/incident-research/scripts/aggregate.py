"""Convert the incident CSV into the repository's trend-data-v1 input.

This is a known-impact-time estimate, not a request-based SLI or vendor SLA.
Observation windows are explicit inputs, never inferred from first incident dates.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from core import read_csv, require, utc, iso, union_seconds, highest, write_json, validate_csv


def aggregate(csv_path: Path, windows: dict, *, allow_estimates=False, allow_incomplete=False) -> dict:
    validate_csv(csv_path)
    rows = read_csv(csv_path)
    require(bool(rows), 'Empty CSV cannot establish an observed zero-incident window')
    require(len({r['collection_run_id'] for r in rows}) == 1, 'Do not mix different collection snapshots')
    require({r['company_id'] for r in rows} == {windows.get('company_id')}, 'Company/window configuration mismatch')
    cutoff_values = {r['cutoff_utc'] for r in rows}
    require(len(cutoff_values) == 1, 'Mixed CSV cutoff timestamps')
    cutoff = utc(next(iter(cutoff_values)))
    scopes = windows.get('service_windows', {})
    overall = windows.get('overall_group', 'Overall')
    require(bool(scopes) and overall in scopes, 'Explicit overall and service observation windows required')
    complete = all(r['coverage_status'] == 'enumerated' for r in rows)
    require(complete or allow_incomplete, 'Collection not fully enumerated; refuse publishable availability by default')
    incidents = [r for r in rows if r['record_type'] == 'incident']
    uncertain = [r for r in incidents if r['time_complete'] != 'True' or r['review_status'] != 'assessed'
                 or r['assessed_severity'] == 'unknown' or 'Unmapped' in r['service_groups_json']]
    require(not uncertain or allow_estimates, 'Unreviewed/unknown/proxy evidence remains; --allow-estimates is required')
    annual = []
    for group, bounds in scopes.items():
        start, end = utc(bounds['start']), utc(bounds.get('end', iso(cutoff)))
        require(start < end <= cutoff, 'Invalid observation window')
        require(start >= min(utc(r['requested_start_utc']) for r in rows), 'Observation starts before requested collection coverage')
        relevant = [r for r in incidents if group == overall or group in r['service_groups_json']
                    or any(group in i['service_groups'] for i in r['impact_intervals_json'])]
        selected = []
        for r in relevant:
            phases = [i for i in r['impact_intervals_json'] if group == overall or group in i['service_groups']]
            anchor = min((utc(i['start_at']) for i in phases), default=utc(r['published_at_utc']))
            grade = highest(i['severity'] for i in phases) if phases else r['assessed_severity']
            selected.append((r, phases, anchor, grade))
        for year in range(start.year, end.year + 1):
            a = max(start, datetime(year, 1, 1, tzinfo=timezone.utc))
            b = min(end, datetime(year + 1, 1, 1, tzinfo=timezone.utc))
            if a >= b:
                continue
            counted = [x for x in selected if a <= x[2] < b]
            phases = [i for _, xs, _, _ in selected for i in xs]
            durations = [union_seconds(phases, allowed, a, b) / 3600 for allowed in
                         (['full_outage'], ['full_outage', 'partial_outage'],
                          ['full_outage', 'partial_outage', 'degraded_performance'])]
            denominator = (b - a).total_seconds()
            annual.append({'year': year, 'group': group, 'window_start': iso(a), 'window_end': iso(b),
                           'denominator_seconds': denominator, 'incident_count': len(counted),
                           'full_count': sum(x[3] == 'full_outage' for x in counted),
                           'partial_count': sum(x[3] == 'partial_outage' for x in counted),
                           'degraded_count': sum(x[3] == 'degraded_performance' for x in counted),
                           'unknown_severity_count': sum(x[3] == 'unknown' for x in counted),
                           'unknown_time_count': sum(not x[1] for x in counted),
                           'unverified_time_count': sum(x[0]['time_complete'] != 'True' for x in counted),
                           'full_hours': durations[0], 'full_partial_hours': durations[1], 'all_hours': durations[2],
                           'availability_full': 1 - durations[0] * 3600 / denominator,
                           'availability_full_partial': 1 - durations[1] * 3600 / denominator,
                           'availability_all': 1 - durations[2] * 3600 / denominator,
                           'count_basis': 'first_known_service_impact_else_publication',
                           'metric_scope': 'any_included_affected_component', 'estimate': bool(uncertain) or not complete})
    return {'schema_version': 1, 'cutoff_utc': iso(cutoff), 'annual': annual, 'matched_windows': [],
            'synthetic': any('synthetic_test_data' in r['quality_flags_json'] for r in rows),
            'provenance': {'source': csv_path.name, 'collection_run_id': rows[0]['collection_run_id'],
                           'coverage': rows[0]['coverage_status'], 'unverified_incidents': len(uncertain),
                           'unknowns_are_excluded_from_known_time_not_confirmed_zero': True,
                           'limitations': ['No request/user-traffic weighting; not a contractual SLA.',
                                           'Publication-window acquisition can miss earlier carry-in incidents.',
                                           'Missing durations/severity are not proof of zero impact.',
                                           'Service group complete outage is not implied by one component outage.']}}
