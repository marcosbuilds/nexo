#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core.account import resolve_account, owner_identity

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True); d=json.loads(ap.parse_args().json)
    out=resolve_account(d.get('accounts',[]),provider=d.get('provider',''),purpose=d.get('purpose'),preferred_email=d.get('preferred_email'),required_permission=d.get('required_permission'))
    if d.get('owner_profile'):
        out['owner_identity']=owner_identity(d['owner_profile'],out.get('account'))
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
