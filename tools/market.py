#!/usr/bin/env python3
"""Inspect and persist evidence for the worker's commercial niche experiments."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from core.market import snapshot, record_event
from db import connect


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-json", help="JSON event to record; otherwise prints the current strategy")
    args = parser.parse_args()
    conn = connect()
    try:
        result = record_event(conn, json.loads(args.record_json)) if args.record_json else snapshot(conn)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        conn.close()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
