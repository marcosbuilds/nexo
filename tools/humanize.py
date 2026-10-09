#!/usr/bin/env python3
"""Command-line wrapper for the installed wording gate."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from vendor.humanizer import analyze  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--recent-openings", default="[]")
    args = ap.parse_args()
    print(json.dumps(analyze(args.text, json.loads(args.recent_openings)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
