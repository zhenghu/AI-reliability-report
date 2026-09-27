#!/usr/bin/env python3
"""Render provider-neutral trend figures; input statistics are not recomputed."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from reliability.model import load_report
from reliability.publisher import check_destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="An empty output directory; chart subdirectory comes from config")
    args = parser.parse_args()
    try:
        report = load_report(args.config)
        check_destination(report, args.output, False)
        from reliability.charts import render_charts
        paths = render_charts(report, args.output)
        print(json.dumps({"company": report.company, "files": len(paths), "output": str(args.output.resolve())}, ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
