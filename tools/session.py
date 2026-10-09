#!/usr/bin/env python3
"""Deterministic continuity gate for a genuinely continuous worker."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass

@dataclass(frozen=True)
class SessionState:
    real_outcome: bool
    active_jobs: int
    urgent_conversations: int
    hot_conversations: int
    due_followups: int
    pending_outcomes: int
    qualified_opportunities: int
    independent_tasks: int
    human_blockers: int
    critical_blocker: bool
    cheap_probe_available: bool
    next_action_persisted: bool
    executable_commitments: int = 0
    in_flight_commitments: int = 0
    stalled_commitments: int = 0
    continuous_mode: bool = True
    proactive_fronts_checked: int = 0
    demand_generation_available: bool = True


def decide(state: SessionState) -> dict:
    if state.executable_commitments > 0:
        return {"decision":"CONTINUE_EXECUTABLE_COMMITMENTS","reason":"executable commitment must reach terminal state","next_action":"run_action_liveness_and_execute"}
    if state.in_flight_commitments > 0:
        return {"decision":"CONTINUE_IN_FLIGHT_COMMITMENTS","reason":"in-flight action requires receipt or recovery","next_action":"inspect_receipt_or_recover"}
    if state.critical_blocker:
        return {"decision":"END_BLOCKED","reason":"a global critical blocker prevents safe continuation","next_action":"human_intervention"}
    if state.active_jobs > 0 or state.urgent_conversations > 0:
        return {"decision":"CONTINUE_PRIORITY_WORK","reason":"active or urgent work exists"}
    if state.due_followups > 0 or state.hot_conversations > 0:
        return {"decision":"CONTINUE_CONVERSATIONS","reason":"conversation work is available"}
    if state.pending_outcomes > 0:
        return {"decision":"VERIFY_OUTCOMES","reason":"previous actions can still produce consequences"}
    if state.qualified_opportunities > 0:
        return {"decision":"CONTINUE_OPPORTUNITY_WORK","reason":"qualified opportunities are actionable"}
    if state.independent_tasks > 0:
        return {"decision":"CONTINUE_QUEUE","reason":"independent useful tasks exist"}
    if state.cheap_probe_available:
        return {"decision":"RUN_USEFUL_PROBE","reason":"cheap uncertainty reduction is available"}
    if state.demand_generation_available and state.proactive_fronts_checked < 2:
        return {"decision":"CONTINUE_WORK_SEEKING","reason":"empty execution queue must trigger demand-generation before waiting","next_action":"run_work_seeking_cycle"}
    if not state.real_outcome:
        return {"decision":"CONTINUE_WORK_SEEKING","reason":"session has no real outcome yet","next_action":"run_work_seeking_cycle"}
    if state.continuous_mode:
        if state.next_action_persisted:
            return {"decision":"WAIT_FOR_EVENT","reason":"proactive fronts are exhausted; keep autonomous runtime alive","next_action":"sleep_until_next_event"}
        return {"decision":"CONTINUE_STATE_PERSISTENCE","reason":"continuous mode requires a persisted wake plan","next_action":"persist_next_action_and_wake_plan"}
    if state.human_blockers > 0 and state.next_action_persisted:
        return {"decision":"END_WITH_BLOCKERS","reason":"only human blockers remain in non-continuous mode"}
    if state.next_action_persisted:
        return {"decision":"END_COMPLETE","reason":"result and queue conditions are satisfied"}
    return {"decision":"CONTINUE_STATE_PERSISTENCE","reason":"cannot end without persisted next action"}


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument('--json',required=True)
    data=json.loads(p.parse_args().json)
    defaults={"active_jobs":0,"urgent_conversations":0,"hot_conversations":0,"due_followups":0,"pending_outcomes":0,"qualified_opportunities":0,"independent_tasks":0,"human_blockers":0,"critical_blocker":False,"cheap_probe_available":False,"next_action_persisted":False,"continuous_mode":True,"real_outcome":False,"executable_commitments":0,"in_flight_commitments":0,"stalled_commitments":0,"proactive_fronts_checked":0,"demand_generation_available":True}
    defaults.update(data)
    print(json.dumps(decide(SessionState(**defaults)),ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
