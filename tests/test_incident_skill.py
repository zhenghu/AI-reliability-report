"""Offline tests of the reusable incident Skill. All constructed events are synthetic."""
import copy
import hashlib
import json
import socket
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/incident-research'
sys.path.insert(0, str(SKILL / 'scripts'))
from core import (FIELDS, digest, export_csv, normalize_record, read_csv, text, union_seconds,
                  validate_csv, component_map, utc)
from adapters import collect, public_url, base_url, discover
from aggregate import aggregate

URL = 'https://status.example.com'
START, END = '2024-01-01T00:00:00Z', '2024-01-03T00:00:00Z'
BODY = 'All API requests failed from 00:00 UTC to 00:10 UTC on January 1, 2024.'


def fixture(platform='incidentio'):
    summary = {'summary': {'name': 'ExampleAI', 'data_available_since': START,
                           'components': [{'id': 'api', 'name': 'Inference'}],
                           'structure': {'items': [{'group': {'name': 'API', 'components': [{'component_id': 'api', 'name': 'Inference'}]}}]}}}
    raw = {'id': 'one', 'name': 'Synthetic API incident', 'published_at': START, 'status': 'resolved', 'type': 'incident',
           'updates': [{'id': 'u1', 'published_at': START, 'to_status': 'investigating', 'message_string': BODY},
                       {'id': 'u2', 'published_at': '2024-01-01T00:10:00Z', 'to_status': 'resolved', 'message_string': 'Restored.'}],
           'affected_components': [{'component_id': 'api', 'status': 'full_outage'}],
           'component_impacts': [{'start_at': START, 'end_at': '2024-01-01T00:10:00Z', 'component_id': 'api', 'status': 'full_outage'}]}
    if platform == 'statuspage':
        summary = {'page': {'name': 'ExampleAI'}, 'components': [{'id': 'api', 'name': 'API'}]}
        raw = {'id': 'one', 'name': 'Synthetic API incident', 'created_at': START, 'status': 'resolved', 'impact': 'critical',
               'components': [{'id': 'api', 'name': 'API', 'status': 'operational'}],
               'incident_updates': [{'id': 'u1', 'display_at': START, 'status': 'investigating', 'body': BODY},
                                    {'id': 'u2', 'display_at': '2024-01-01T00:10:00Z', 'status': 'resolved', 'body': 'Restored.'}]}
    snap = {'schema_version': 1, 'platform': platform, 'company': {'id': 'example', 'name': 'ExampleAI'},
            'status_page_url': URL, 'start_utc': START, 'cutoff_utc': END, 'retrieved_at_utc': END,
            'run_id': 'synthetic-test', 'components': component_map(summary, platform),
            'coverage': {'status': 'enumerated', 'cross_check': 'synthetic_fixture_only', 'errors': []},
            'records': [{'raw': raw, 'source_urls': [URL + '/incidents/one']}]}
    return snap, summary


def review_for(snap):
    return {'schema_version': 1, 'records': [{
        'incident_id': 'one', 'source_record_sha256': digest(snap['records'][0]['raw']),
        'severity': 'full_outage', 'service_groups': ['API'], 'summary': 'Synthetic API outage.',
        'root_cause_status': 'not_disclosed', 'time_complete': True,
        'evidence': [{'kind': kind, 'source_url': URL + '/incidents/one', 'quote': BODY, 'update_id': 'u1'}
                     for kind in ('severity', 'service', 'time')],
        'intervals': [{'start_at': START, 'end_at': '2024-01-01T00:10:00Z', 'severity': 'full_outage',
                       'service_groups': ['API'], 'time_basis': 'explicit_impact', 'evidence_indices': [0, 1, 2]}]}]}


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.snap, _ = fixture()
        self.entry = self.snap['records'][0]

    def normalize(self, review=None):
        return normalize_record(self.entry, self.snap, review)

    def test_native_interval(self):
        row = self.normalize()
        self.assertEqual(row['impact_seconds'], 600)
        self.assertEqual(row['service_groups_json'], ['API'])
        self.assertEqual(row['review_status'], 'needs_review')
        self.assertFalse(row['time_complete'])

    def test_component_duplicates_not_added(self):
        self.entry['raw']['component_impacts'] *= 4
        self.assertEqual(self.normalize()['known_full_seconds'], 600)

    def test_overlap_union(self):
        phases = [{'start_at': START, 'end_at': '2024-01-01T00:10:00Z', 'severity': 'full_outage'},
                  {'start_at': '2024-01-01T00:05:00Z', 'end_at': '2024-01-01T00:15:00Z', 'severity': 'partial_outage'}]
        self.assertEqual(union_seconds(phases), 900)
        self.assertEqual(union_seconds(phases, ['full_outage']), 600)

    def test_postmortem_does_not_extend(self):
        self.entry['raw']['component_impacts'][0]['end_at'] = '2024-01-02T00:00:00Z'
        self.entry['raw']['updates'].append({'id': 'pm', 'published_at': '2024-01-02T00:00:00Z',
                                            'to_status': 'resolved', 'message_string': 'Postmortem published.'})
        row = self.normalize()
        self.assertEqual(row['impact_seconds'], 600)
        self.assertIn('official_interval_clipped_at_resolution', row['quality_flags_json'])

    def test_unknown_is_not_operational(self):
        self.entry['raw'].pop('component_impacts')
        self.entry['raw']['affected_components'] = []
        row = self.normalize()
        self.assertEqual(row['assessed_severity'], 'unknown')
        self.assertIsNone(row['impact_seconds'])
        self.assertEqual(row['service_groups_json'], ['Unmapped'])

    def test_resolved_only_not_zero(self):
        self.entry['raw']['component_impacts'] = []
        self.entry['raw']['updates'] = [self.entry['raw']['updates'][1]]
        self.assertIsNone(self.normalize()['impact_seconds'])

    def test_negative_official_interval_flagged(self):
        self.entry['raw']['component_impacts'][0]['end_at'] = '2023-12-31T00:00:00Z'
        self.assertIn('invalid_official_interval', self.normalize()['quality_flags_json'])

    def test_ongoing_right_censored(self):
        self.entry['raw']['status'] = 'investigating'
        self.entry['raw']['updates'] = self.entry['raw']['updates'][:1]
        self.entry['raw']['component_impacts'][0]['end_at'] = None
        row = self.normalize()
        self.assertTrue(row['right_censored'])
        self.assertEqual(row['impact_seconds'], 172800)

    def test_statuspage_impact_proxy(self):
        snap, _ = fixture('statuspage')
        row = normalize_record(snap['records'][0], snap)
        self.assertEqual(row['official_severity'], 'full_outage')
        self.assertEqual(row['time_basis'], 'announcement_proxy')
        self.assertIn('impact_mapping_is_a_convention_not_proof_of_total_outage', row['quality_flags_json'])

    def test_maintenance_retained(self):
        self.entry['raw']['type'] = 'maintenance'
        self.assertEqual(self.normalize()['record_type'], 'maintenance')

    def test_legacy_rich_text(self):
        self.assertEqual(text({'text_node': {'content': [{'text': 'a'}, {'text': 'b'}]}}), 'a\nb')

    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            utc('2024-01-01T00:00:00')

    def test_review_valid(self):
        r = review_for(self.snap)['records'][0]
        row = self.normalize(r)
        self.assertTrue(row['time_complete'])
        self.assertEqual(row['review_status'], 'assessed')

    def test_review_stale_rejected(self):
        r = review_for(self.snap)['records'][0]
        self.entry['raw']['name'] = 'Changed'
        with self.assertRaisesRegex(ValueError, 'Stale'):
            self.normalize(r)

    def test_review_fabricated_quote_rejected(self):
        r = review_for(self.snap)['records'][0]
        r['evidence'][0]['quote'] = 'not present'
        with self.assertRaisesRegex(ValueError, 'quote'):
            self.normalize(r)

    def test_review_wrong_update_rejected(self):
        r = review_for(self.snap)['records'][0]
        r['evidence'][0]['update_id'] = 'absent'
        with self.assertRaisesRegex(ValueError, 'update ID'):
            self.normalize(r)

    def test_review_future_interval_rejected(self):
        r = review_for(self.snap)['records'][0]
        r['intervals'][0]['end_at'] = '2024-01-04T00:00:00Z'
        with self.assertRaisesRegex(ValueError, 'time interval'):
            self.normalize(r)

    def test_review_rootcause_without_evidence_rejected(self):
        r = review_for(self.snap)['records'][0]
        r['root_cause'] = 'a database'
        with self.assertRaisesRegex(ValueError, 'Root-cause'):
            self.normalize(r)

    def test_review_bad_indices_rejected(self):
        r = review_for(self.snap)['records'][0]
        r['intervals'][0]['evidence_indices'] = [22]
        with self.assertRaisesRegex(ValueError, 'indices'):
            self.normalize(r)

    def test_review_needs_timeline_for_changed_severity(self):
        r = review_for(self.snap)['records'][0]
        r.pop('intervals'); r['time_complete'] = False; r['severity'] = 'partial_outage'
        with self.assertRaisesRegex(ValueError, 'explicit reviewed'):
            self.normalize(r)

    def test_generic_not_fabricated_official(self):
        self.snap['platform'] = 'generic'
        row = self.normalize()
        self.assertEqual(row['official_severity'], 'unknown')
        self.assertEqual(row['impact_intervals_json'], [])


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'incidents.csv'
        self.snap, _ = fixture()
    def tearDown(self):
        self.tmp.cleanup()

    def test_csv_roundtrip(self):
        result = export_csv(self.snap, self.path, review_for(self.snap))
        self.assertEqual(result['rows'], 1)
        self.assertEqual(self.path.read_bytes()[:3], b'\xef\xbb\xbf')
        row = read_csv(self.path)[0]
        self.assertEqual(row['raw_incident_json'], self.snap['records'][0]['raw'])
        self.assertEqual(list(row), FIELDS)

    def test_long_multiline_unicode(self):
        self.snap['records'][0]['raw']['name'] = '中文,引号"换行\n' + 'x' * 150000
        export_csv(self.snap, self.path)
        self.assertEqual(read_csv(self.path)[0]['incident_title'], self.snap['records'][0]['raw']['name'])

    def test_formula_safe_roundtrip(self):
        self.snap['records'][0]['raw']['name'] = '=HYPERLINK("bad","bad")'
        export_csv(self.snap, self.path)
        self.assertIn(b"'=HYPERLINK", self.path.read_bytes())
        self.assertTrue(read_csv(self.path)[0]['incident_title'].startswith('='))

    def test_duplicate_ids_rejected(self):
        self.snap['records'] *= 2
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            export_csv(self.snap, self.path)

    def test_maintenance_count(self):
        self.snap['records'][0]['raw']['type'] = 'maintenance'
        result = export_csv(self.snap, self.path)
        self.assertEqual((result['incidents'], result['maintenance']), (0, 1))

    def test_never_overwrites(self):
        self.path.write_text('do not replace')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            export_csv(self.snap, self.path)
        self.assertEqual(self.path.read_text(), 'do not replace')

    def test_tampered_raw_detected(self):
        export_csv(self.snap, self.path)
        content = self.path.read_text(encoding='utf-8-sig').replace('Synthetic API incident', 'Tampered')
        self.path.write_text(content, encoding='utf-8-sig')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            validate_csv(self.path)

    def test_bridge_contract(self):
        export_csv(self.snap, self.path, review_for(self.snap))
        windows = {'company_id': 'example', 'overall_group': 'Overall',
                   'service_windows': {g: {'start': START, 'end': END} for g in ('Overall', 'API')}}
        data = aggregate(self.path, windows)
        self.assertEqual(len(data['annual']), 2)
        self.assertAlmostEqual(data['annual'][0]['full_hours'], 1/6)
        sys.path.insert(0, str(ROOT / 'scripts'))
        from reliability.model import normalize_rows
        normalized = normalize_rows(data['annual'], ['Overall', 'API'], utc(END), annual=True)
        self.assertEqual(len(normalized), 2)

    def test_estimates_gate(self):
        export_csv(self.snap, self.path)
        windows = {'company_id': 'example', 'overall_group': 'Overall',
                   'service_windows': {'Overall': {'start': START, 'end': END}}}
        with self.assertRaisesRegex(ValueError, 'allow-estimates'):
            aggregate(self.path, windows)
        self.assertTrue(aggregate(self.path, windows, allow_estimates=True)['annual'][0]['estimate'])

    def test_incomplete_gate(self):
        self.snap['coverage']['status'] = 'incomplete'
        export_csv(self.snap, self.path, review_for(self.snap))
        w = {'company_id': 'example', 'service_windows': {'Overall': {'start': START, 'end': END}}}
        with self.assertRaisesRegex(ValueError, 'not fully enumerated'):
            aggregate(self.path, w)

    def test_unknown_not_filled_zero(self):
        self.snap['records'][0]['raw']['component_impacts'] = []
        self.snap['records'][0]['raw']['affected_components'] = []
        export_csv(self.snap, self.path)
        self.assertEqual(read_csv(self.path)[0]['known_all_seconds'], '')


class FakeClient:
    def __init__(self, platform='incidentio', repeat=False, fail=False):
        self.snap, self.summary = fixture(platform)
        self.platform, self.repeat, self.fail, self.calls = platform, repeat, fail, []
    def get(self, url, **kw):
        self.calls.append(url)
        meta = {'url': url, 'retrieved_at_utc': END, 'sha256': 'fixture-only'}
        if url.endswith('/summary'):
            if self.platform != 'incidentio':
                raise ValueError('Not incident.io')
            return self.summary, meta
        if url.endswith('summary.json'):
            return self.summary, meta
        if self.fail:
            raise OSError('Simulated network outage')
        if 'scheduled-maintenances' in url:
            return {'scheduled_maintenances': []}, meta
        if self.platform == 'statuspage' and 'page=2' in url and not self.repeat:
            return {'incidents': []}, meta
        return {'incidents': [self.snap['records'][0]['raw']]}, meta


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / 'run'
    def tearDown(self):
        self.tmp.cleanup()
    def run_collect(self, client, **kw):
        return collect(URL, self.out, company_id='example', start=START, end=END, client=client, **kw)

    def test_window_enumeration(self):
        s = self.run_collect(FakeClient(), window_days=1)
        self.assertEqual(s['coverage']['status'], 'enumerated')
        self.assertEqual(len(s['requests']), 2)
        self.assertEqual(len(s['records']), 1)
        self.assertTrue((self.out / 'snapshot.json').exists())

    def test_failure_checkpoint(self):
        s = self.run_collect(FakeClient(fail=True))
        self.assertEqual(s['coverage']['status'], 'incomplete')
        self.assertIn('Simulated', s['coverage']['errors'][0])
        self.assertTrue((self.out / 'snapshot.json').exists())

    def test_page_limit_is_incomplete(self):
        s = self.run_collect(FakeClient(), window_days=1, max_pages=1)
        self.assertEqual(s['coverage']['status'], 'incomplete')
        self.assertEqual(len(s['records']), 1)

    def test_statuspage_empty_termination(self):
        s = self.run_collect(FakeClient('statuspage'), max_pages=2)
        self.assertEqual(s['coverage']['status'], 'enumerated')
        self.assertEqual(len(s['records']), 1)

    def test_ignored_pagination_detected(self):
        s = self.run_collect(FakeClient('statuspage', repeat=True), max_pages=4)
        self.assertEqual(s['coverage']['status'], 'incomplete')
        self.assertIn('repeated', s['coverage']['errors'][0])

    def test_resume_scope_protected(self):
        self.run_collect(FakeClient())
        with self.assertRaisesRegex(ValueError, 'cutoff'):
            collect(URL, self.out, company_id='example', start=START, end='2024-01-04T00:00:00Z', client=FakeClient())

    def test_history_url_entrance(self):
        self.assertEqual(base_url('status.example.com/history/'), URL)

    def test_private_network_refused(self):
        with patch('adapters.socket.getaddrinfo', return_value=[(None, None, None, None, ('127.0.0.1', 443))]):
            with self.assertRaisesRegex(ValueError, 'Private'):
                public_url(URL)

    def test_credentials_refused(self):
        with self.assertRaises(ValueError):
            public_url('https://user:pass@status.example.com')

    def test_cross_origin_redirect_refused(self):
        with self.assertRaisesRegex(ValueError, 'Cross-origin'):
            public_url('https://evil.example.net/', URL)

    def test_nonempty_directory_protected(self):
        self.out.mkdir(); (self.out / 'user.txt').write_text('keep')
        with self.assertRaisesRegex(ValueError, 'Non-empty'):
            self.run_collect(FakeClient())


class BoundaryTests(unittest.TestCase):
    def test_reopened_incident_keeps_separate_periods(self):
        snap, _ = fixture()
        raw = snap['records'][0]['raw']
        raw['component_impacts'] = []
        raw['updates'] += [{'id':'u3','published_at':'2024-01-01T00:20:00Z','to_status':'investigating','message_string':'Reopened.'},
                           {'id':'u4','published_at':'2024-01-01T00:25:00Z','to_status':'resolved','message_string':'Fixed again.'},
                           {'id':'u5','published_at':'2024-01-02T00:00:00Z','to_status':'resolved','message_string':'Postmortem.'}]
        row = normalize_record(snap['records'][0], snap)
        self.assertEqual(len(row['impact_intervals_json']), 2)
        self.assertEqual(row['impact_seconds'], 900)

    def test_component_after_resolution_not_postmortem_outage(self):
        snap, _ = fixture()
        raw = snap['records'][0]['raw']
        raw['component_impacts'][0].update(start_at='2024-01-01T00:20:00Z',end_at='2024-01-02T00:00:00Z')
        raw['updates'].append({'id':'pm','published_at':'2024-01-02T00:00:00Z','to_status':'resolved','message_string':'Postmortem'})
        row = normalize_record(snap['records'][0], snap)
        self.assertIn('official_interval_after_resolution_requires_review', row['quality_flags_json'])
        self.assertEqual(row['impact_seconds'],600) # explicit proxy fallback, not one day
        self.assertEqual(row['time_basis'],'announcement_proxy')

    def test_proxy_cannot_be_complete_actual_time(self):
        snap, _ = fixture()
        review = review_for(snap)['records'][0]
        review['intervals'][0]['time_basis']='announcement_proxy'
        with self.assertRaisesRegex(ValueError,'proxy cannot'):
            normalize_record(snap['records'][0],snap,review)

    def test_review_interval_service_scope(self):
        snap, _ = fixture()
        review = review_for(snap)['records'][0]
        review['intervals'][0]['service_groups']=['Wrong service']
        with self.assertRaisesRegex(ValueError,'outside assessed'):
            normalize_record(snap['records'][0],snap,review)

    def test_cross_year_union_is_clipped(self):
        intervals=[{'start_at':'2023-12-31T23:50:00Z','end_at':'2024-01-01T00:10:00Z','severity':'full_outage'}]
        self.assertEqual(union_seconds(intervals,start=utc(START),end=utc(END)),600)
        self.assertEqual(union_seconds(intervals,end=utc(START)),600)

    def test_leap_year_denominator(self):
        snap,_=fixture()
        snap['cutoff_utc']='2025-01-01T00:00:00Z'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'incidents.csv'
            export_csv(snap,p,review_for(snap))
            data=aggregate(p,{'company_id':'example','service_windows':{'Overall':{'start':START,'end':snap['cutoff_utc']}}})
            self.assertEqual(data['annual'][0]['denominator_seconds'],366*86400)

    def test_empty_csv_not_zero_incident_proof(self):
        snap,_=fixture();snap['records']=[]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'empty.csv';export_csv(snap,p)
            self.assertEqual(validate_csv(p)['rows'],0)
            with self.assertRaisesRegex(ValueError,'Empty CSV'):
                aggregate(p,{'company_id':'example','service_windows':{'Overall':{'start':START,'end':END}}})


if __name__ == '__main__':
    unittest.main()
