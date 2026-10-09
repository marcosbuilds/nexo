#!/usr/bin/env python3
"""Durable wake queue CLI: claim due work exactly once, never pretend a reminder fired."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from runtime.store import RuntimeStore

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--now'); ap.add_argument('--limit',type=int,default=20); args=ap.parse_args()
    now=args.now or datetime.now(timezone.utc).isoformat(); store=RuntimeStore.open()
    try:
        due=store.claim_due_wakes(now,args.limit); print(json.dumps({'claimed':due,'now':now},ensure_ascii=False,indent=2)); return 0
    finally: store.db.close()
if __name__=='__main__': raise SystemExit(main())
