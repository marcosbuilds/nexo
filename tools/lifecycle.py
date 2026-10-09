#!/usr/bin/env python3
"""Resolve current commercial lifecycle from persisted evidence, not keyword memory."""
from __future__ import annotations
import argparse, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "tools"))
ORDER=["unknown","prospect","qualified","trial_requested","trial_started","trial_completed","offer_sent","negotiating","won","payment_requested","payment_verified","delivered","satisfaction_confirmed","review_requested","repeat_candidate"]

def resolve(contact_id:int)->dict:
    from db import connect
    con=connect()
    trial=con.execute("SELECT * FROM trials WHERE contact_id=? ORDER BY COALESCE(completed_at,started_at,requested_at,created_at) DESC LIMIT 1",(contact_id,)).fetchone()
    job=con.execute("SELECT * FROM jobs WHERE client_id=? ORDER BY id DESC LIMIT 1",(contact_id,)).fetchone()
    lc=con.execute("SELECT * FROM customer_lifecycle WHERE contact_id=? LIMIT 1",(contact_id,)).fetchone()
    con.close()
    stage=(lc['stage'] if lc else 'unknown')
    facts=[]
    if trial:
        facts.append({'source':'trial','status':trial['status'],'trial_id':trial['id']})
        if trial['status']=='completed' and ORDER.index(stage)<ORDER.index('trial_completed'): stage='trial_completed'
        elif trial['status']=='started' and ORDER.index(stage)<ORDER.index('trial_started'): stage='trial_started'
    if job:
        facts.append({'source':'job','status':job['status'],'revenue':job['revenue']})
        if job['status'] in {'active','accepted'} and ORDER.index(stage)<ORDER.index('won'): stage='won'
        if job['status'] in {'completed','delivered'} and ORDER.index(stage)<ORDER.index('delivered'): stage='delivered'
    next_action={
      'unknown':'recover_history_before_action','prospect':'understand_need','qualified':'advance_to_next_small_commitment',
      'trial_requested':'follow_trial_progress','trial_started':'wait_for_or_verify_trial_result','trial_completed':'do_not_repeat_completed_trial',
      'offer_sent':'handle_reply_or_follow_up_contextually','negotiating':'resolve_objection_or_clarify_terms','won':'prepare_payment_or_execution',
      'payment_requested':'verify_payment','payment_verified':'execute_or_deliver','delivered':'check_satisfaction',
      'satisfaction_confirmed':'request_review_when_contextually_appropriate','review_requested':'record_response_and_watch_for_repeat','repeat_candidate':'look_for_legitimate_next_demand'
    }.get(stage,'recover_history_before_action')
    return {'contact_id':contact_id,'stage':stage,'next_action':next_action,'facts':facts,'has_completed_trial':any(f.get('status')=='completed' for f in facts if f.get('source')=='trial')}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--contact-id',type=int,required=True); args=ap.parse_args()
    from db import connect
    con=connect(); exists=con.execute('SELECT 1 FROM contacts WHERE id=?',(args.contact_id,)).fetchone(); con.close()
    if not exists: raise SystemExit('contact not found')
    print(json.dumps(resolve(args.contact_id),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
