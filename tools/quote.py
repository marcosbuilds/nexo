#!/usr/bin/env python3
"""Backward-compatible CLI for the autonomous Price Brain."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core.pricing import recommend_quote

def quote(d:dict)->dict:
    return recommend_quote(d)

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True); print(json.dumps(quote(json.loads(ap.parse_args().json)),ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
