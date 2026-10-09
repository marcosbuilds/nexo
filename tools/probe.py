#!/usr/bin/env python3
"""Create a small capability test record without declaring proficiency prematurely."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "tools"))

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--capability", required=True)
    p.add_argument("--objective", required=True)
    p.add_argument("--toolchain", default="")
    p.add_argument("--status", default="planned")
    args = p.parse_args()
    from db import connect
    con = connect()
    con.execute(
        "INSERT INTO capability_tests(capability, objective, toolchain, status) VALUES(?,?,?,?)",
        (args.capability, args.objective, args.toolchain, args.status),
    )
    con.commit()
    row = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.close()
    print(json.dumps({"capability_test_id": row, "status": args.status}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
