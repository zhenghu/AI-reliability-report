#!/usr/bin/env python3
"""Build a company-independent offline reading report from frozen inputs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from reliability.model import load_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path, help="Company/report JSON configuration")
    parser.add_argument("--output", type=Path, help="Output directory override, relative to the current working directory")
    parser.add_argument("--validate-only", action="store_true", help="Validate inputs and checksums without rendering or writing")
    parser.add_argument("--overwrite", action="store_true", help="Replace only a previous generated reading copy for the same company")
    args = parser.parse_args()
    try:
        report = load_report(args.config)
        if args.validate_only:
            result = {"valid": True, "company": report.company, "years": report.years,
                      "annual_rows": len(report.annual), "matched_rows": len(report.matched)}
        else:
            from reliability.publisher import build_report
            result = build_report(report, args.output, overwrite=args.overwrite)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
