#!/usr/bin/env python3
"""Assess what the worker can safely do to receive payments."""
from __future__ import annotations
import argparse,json

def assess(d):
    verified_pix=bool(d.get('verified_pix_destination'))
    web=bool(d.get('logged_in_web_session'))
    api=bool(d.get('api_capability'))
    create_link=bool(d.get('can_create_payment_link'))
    verify=bool(d.get('can_verify_receipt'))
    if verify and (verified_pix or api or web): level='CAN_VERIFY_RECEIPT'
    elif verified_pix: level='CAN_RECEIVE_PIX'
    elif create_link and (web or api): level='CAN_CREATE_PAYMENT_LINK'
    elif web or api: level='CAN_REQUEST_PAYMENT'
    elif d.get('account_discovered'): level='ACCOUNT_VISIBLE'
    else: level='NONE'
    return {'level':level,'verified_pix':verified_pix,'payment_link':create_link and (web or api),'verify_receipt':verify,'next_action': 'use_verified_destination' if level in {'CAN_RECEIVE_PIX','CAN_CREATE_PAYMENT_LINK','CAN_VERIFY_RECEIPT'} else 'discover_or_request_real_payment_setup'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True)
    print(json.dumps(assess(json.loads(ap.parse_args().json)),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
