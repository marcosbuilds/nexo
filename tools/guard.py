#!/usr/bin/env python3
"""Prevent contact/account/context mixups before external side effects."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def validate_send(d):
    expected=str(d.get('conversation_id') or '')
    recipient=str(d.get('recipient_id') or '')
    confirmed=str(d.get('resolved_recipient_id') or '')
    account=str(d.get('account_id') or '')
    current=str(d.get('current_account_id') or '')
    checks=[]
    for name,ok in [
        ('conversation_present',bool(expected)),('recipient_present',bool(recipient)),
        ('recipient_exact_match',bool(recipient and confirmed and recipient==confirmed)),
        ('account_present',bool(account)),('account_context_match',bool(account and current and account==current)),
        ('explicit_send_intent',bool(d.get('send_intent',False))),
        ('history_loaded',bool(d.get('history_loaded',False))),
    ]: checks.append({'check':name,'ok':ok})
    passed=all(c['ok'] for c in checks)
    return {'decision':'ALLOW_SEND' if passed else 'BLOCK_SEND','checks':checks,'reason':'exact recipient + account + history required before side effect'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True); print(json.dumps(validate_send(json.loads(ap.parse_args().json)),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
