#!/usr/bin/env python3
"""Repository shortcut to the self-contained incident-research Skill CLI."""
from pathlib import Path
import sys

SKILL_SCRIPTS = Path(__file__).resolve().parents[1] / '.agents/skills/incident-research/scripts'
sys.path.insert(0, str(SKILL_SCRIPTS))
from incident_pipeline import main

if __name__ == '__main__':
    raise SystemExit(main())
