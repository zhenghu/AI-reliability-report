#!/usr/bin/env python3
"""Incident research CLI; use SKILL.md for evidence review and browser fallback."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from adapters import collect
from aggregate import aggregate
from core import export_csv, validate_csv, write_json, require


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    gather = sub.add_parser('collect', help='Discover public JSON, checkpoint each history page/window')
    gather.add_argument('url')
    gather.add_argument('--output', type=Path, required=True)
    gather.add_argument('--company-id')
    gather.add_argument('--company-name')
    gather.add_argument('--start', help='Inclusive ISO UTC timestamp; default discover earliest public history')
    gather.add_argument('--end', help='Exclusive ISO UTC timestamp; default frozen now')
    gather.add_argument('--adapter', choices=['auto', 'incidentio', 'statuspage'], default='auto')
    gather.add_argument('--window-days', type=int, default=30)
    gather.add_argument('--max-pages', type=int, default=500)
    export = sub.add_parser('export', help='Native/imported snapshot plus evidence assessments -> one CSV')
    export.add_argument('--snapshot', type=Path, required=True)
    export.add_argument('--analysis', type=Path)
    export.add_argument('--output', type=Path, required=True)
    validate = sub.add_parser('validate', help='Validate the CSV round-trip, hashes, timestamps, durations and IDs')
    validate.add_argument('csv', type=Path)
    convert = sub.add_parser('aggregate', help='CSV + explicit service windows -> trend_data.json')
    convert.add_argument('--csv', type=Path, required=True)
    convert.add_argument('--windows', type=Path, required=True)
    convert.add_argument('--output', type=Path, required=True)
    convert.add_argument('--allow-estimates', action='store_true')
    convert.add_argument('--allow-incomplete', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'collect':
            result = collect(args.url, args.output, company_id=args.company_id, company_name=args.company_name,
                             start=args.start, end=args.end, adapter=args.adapter,
                             window_days=args.window_days, max_pages=args.max_pages)
            print(json.dumps({'snapshot': str(args.output / 'snapshot.json'), 'company': result['company'],
                              'records': len(result['records']), 'coverage': result['coverage']}, ensure_ascii=False, indent=2))
            return 0 if result['coverage']['status'] == 'enumerated' else 2
        if args.command == 'export':
            result = export_csv(load(args.snapshot), args.output, load(args.analysis) if args.analysis else None)
        elif args.command == 'validate':
            result = validate_csv(args.csv)
        else:
            require(not args.output.exists(), 'Output already exists; choose a new snapshot filename')
            result = aggregate(args.csv, load(args.windows), allow_estimates=args.allow_estimates,
                               allow_incomplete=args.allow_incomplete)
            write_json(args.output, result)
            result = {'output': str(args.output), 'annual_rows': len(result['annual']), 'provenance': result['provenance']}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
