#!/usr/bin/env python3
"""Canonical Autonomia 2.5 cycle: missions are first-class; gates are safety."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from core.mission import generate_default_missions
from communicate import decide as communication_gate
from context import load as load_context
from operate import preflight
from session import SessionState, decide as session_gate
from search import plan as work_seeking

def run(state:dict)->dict:
    context=load_context()
    if state.get('material_action'):
        action=preflight(state['material_action'])
        if action.get('decision') in {'ALLOW','ALLOW_EXECUTE','ALLOW_EXECUTE_BLOCK_END'}:
            return {'mode':'EXECUTE','context_version':context['version'],'action':action}
        if action.get('decision') in {'HUMAN_REQUIRED','MATERIAL_INPUT_REQUIRED','BLOCK'}:
            return {'mode':'BLOCKED_ACTION_CONTINUE_OTHER_WORK','context_version':context['version'],'action':action}

    if state.get('incoming_message') is not None:
        comm=communication_gate({
            'response_needed':state.get('response_needed',False),'draft':state.get('draft',''),'channel':state.get('channel','whatsapp'),
            'recent_openings':state.get('recent_openings',[]),'conversation_goal':state.get('conversation_goal'),
            'desired_next_customer_state':state.get('desired_next_customer_state'),'triage_reason':state.get('triage_reason'),
            'incoming_text':state.get('incoming_text') or state.get('incoming_message') or '',
            'history':state.get('history',[]),'relationship':state.get('relationship','unknown'),
            'customer_intent':state.get('customer_intent'),'stage':state.get('stage'),
            'active_commitment':state.get('active_commitment'),'explicit_question':state.get('explicit_question',False),
            'sticker_context':state.get('sticker_context'),
        })
        if comm['decision'] in {'SEND','REGENERATE','REPLAN'} or comm['decision']=='NO_SEND':
            if comm['decision']!='NO_SEND' or state.get('conversation_is_primary',False):
                return {'mode':'COMMUNICATION','context_version':context['version'],'communication':comm}

    # Mission generation is the autonomous default. This is what prevents the
    # runtime from turning an empty user inbox into an empty workday.
    mission_state=state.get('mission_state') or state
    missions=generate_default_missions(mission_state)
    if missions:
        top=missions[0].materialize_priority()
        return {'mode':'MISSION','context_version':context['version'],'mission':top,'alternatives':[m.materialize_priority() for m in missions[1:4]]}

    if state.get('queue_empty',False):
        seek=work_seeking(state.get('work_state') or state)
        if seek['decision']=='CONTINUE_WORK_SEEKING': return {'mode':'WORK_SEEKING','context_version':context['version'],'work_seeking':seek}

    defaults={'real_outcome':bool(state.get('real_outcome',False)),'active_jobs':int(state.get('active_jobs',0)),'urgent_conversations':int(state.get('urgent_conversations',0)),'hot_conversations':int(state.get('hot_conversations',0)),'due_followups':int(state.get('due_followups',0)),'pending_outcomes':int(state.get('pending_outcomes',0)),'qualified_opportunities':int(state.get('qualified_opportunities',0)),'independent_tasks':int(state.get('independent_tasks',0)),'human_blockers':int(state.get('human_blockers',0)),'critical_blocker':bool(state.get('critical_blocker',False)),'cheap_probe_available':bool(state.get('cheap_probe_available',False)),'next_action_persisted':bool(state.get('next_action_persisted',False)),'executable_commitments':int(state.get('executable_commitments',0)),'in_flight_commitments':int(state.get('in_flight_commitments',0)),'stalled_commitments':int(state.get('stalled_commitments',0)),'continuous_mode':bool(state.get('continuous_mode',True)),'proactive_fronts_checked':int(state.get('proactive_fronts_checked',0)),'demand_generation_available':bool(state.get('demand_generation_available',True))}
    session=session_gate(SessionState(**defaults)); return {'mode':session['decision'],'context_version':context['version'],'session':session}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True); print(json.dumps(run(json.loads(ap.parse_args().json)),ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
