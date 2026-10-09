#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core.payment import prepare_link

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True); print(json.dumps(prepare_link(json.loads(ap.parse_args().json)),ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
