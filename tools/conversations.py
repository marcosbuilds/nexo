#!/usr/bin/env python3
"""Persist conversation plan and relationship state without losing previous facts."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'tools'))
from db import connect

def upsert(d):
    c=connect()
    try:
        cid=int(d['conversation_id'])
        c.execute("INSERT INTO conversation_plans(conversation_id,stage,conversation_goal,customer_problem_or_goal,known_facts,unknown_that_matters,value_hypothesis,desired_next_customer_state,next_action,objection_focus,follow_up_state,stop_condition,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(conversation_id) DO UPDATE SET stage=excluded.stage,conversation_goal=excluded.conversation_goal,customer_problem_or_goal=excluded.customer_problem_or_goal,known_facts=excluded.known_facts,unknown_that_matters=excluded.unknown_that_matters,value_hypothesis=excluded.value_hypothesis,desired_next_customer_state=excluded.desired_next_customer_state,next_action=excluded.next_action,objection_focus=excluded.objection_focus,follow_up_state=excluded.follow_up_state,stop_condition=excluded.stop_condition,updated_at=CURRENT_TIMESTAMP",
            (cid,d.get('stage','new'),d.get('conversation_goal'),d.get('customer_problem_or_goal'),json.dumps(d.get('known_facts',[]),ensure_ascii=False),json.dumps(d.get('unknown_that_matters',[]),ensure_ascii=False),d.get('value_hypothesis'),d.get('desired_next_customer_state'),d.get('next_action'),d.get('objection_focus'),d.get('follow_up_state'),d.get('stop_condition')))
        c.commit(); return {'status':'saved','conversation_id':cid}
    finally:c.close()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True); print(json.dumps(upsert(json.loads(ap.parse_args().json)),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
