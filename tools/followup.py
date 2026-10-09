#!/usr/bin/env python3
"""Decide whether a follow-up has a real reason to exist."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone

def decide(d):
    replied=bool(d.get('replied_since_last_contact',False)); optout=bool(d.get('opted_out',False)); attempts=int(d.get('attempts',0) or 0)
    new_value=bool(d.get('new_value',False)); due=bool(d.get('due',False)); waiting_on_customer=bool(d.get('waiting_on_customer',False))
    if optout: return {'decision':'STOP','reason':'opt_out'}
    if replied: return {'decision':'RESPOND','reason':'customer_replied'}
    if not due: return {'decision':'WAIT','reason':'not_due'}
    if attempts>=3 and not new_value: return {'decision':'STOP','reason':'followup_pressure_limit_reached'}
    if waiting_on_customer and not new_value: return {'decision':'WAIT','reason':'no_new_reason_to_interrupt_customer'}
    if not new_value and attempts>0: return {'decision':'WAIT','reason':'same_message_without_new_reason'}
    if new_value: return {'decision':'FOLLOW_UP','reason':'new_relevant_value_available'}
    return {'decision':'FOLLOW_UP','reason':'first_due_followup_with_contextual_reason'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True); print(json.dumps(decide(json.loads(ap.parse_args().json)),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
