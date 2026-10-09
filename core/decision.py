"""Small, explicit decision contract for the autonomous worker.

This is a scaffold for useful reasoning: it makes the next move, its expected
effect, cost, evidence and recovery visible to the executor without asking the
LLM to rediscover the same checklist every turn.
"""
from __future__ import annotations

from typing import Any

from core.mission import Mission, generate_default_missions


def _context_lock(state: dict[str, Any], mission: Mission) -> dict[str, Any]:
    metadata = mission.metadata or {}
    return {
        "account": state.get("account_id") or state.get("current_account"),
        "person": state.get("contact_id") or metadata.get("contact_id"),
        "conversation": state.get("conversation_id") or metadata.get("conversation_id"),
        "platform": state.get("platform"),
        "goal": mission.goal_id or state.get("goal_id"),
    }


def _fallback(mission: Mission) -> str:
    if mission.current_state in {"active_job", "accepted_job"}:
        return "inspect_environment_then_resume_or_persist_material_blocker"
    if mission.current_state == "conversation":
        return "retriage_from_latest_message_and_preserve_context_lock"
    if mission.current_state == "pending_consequence":
        return "check_likely_destinations_before_assuming_failure"
    if mission.current_state in {"demand_generation", "idle_to_demand"}:
        return "change_query_or_source_and_record_research_evidence"
    return "switch_to_the_next_ranked_mission_or_persist_blocker"


def build_plan(
    state: dict[str, Any],
    mission: Mission | None = None,
) -> dict[str, Any]:
    """Return one executable plan, never a list of vague intentions."""
    if mission is None:
        mission = generate_default_missions(state)[0]

    metadata = mission.metadata or {}
    if int(state.get("executable_commitments", 0) or 0) > 0:
        action = "resume_execution_commitment"
        current_state = "executable_commitment"
        expected = "the persisted commitment reaches a receipt, verification or real blocker"
    elif int(state.get("in_flight_commitments", 0) or 0) > 0:
        action = "inspect_in_flight_commitment"
        current_state = "in_flight_commitment"
        expected = "a receipt or recovery state is obtained without duplicating the side effect"
    else:
        action = mission.next_action or "choose_next_action"
        current_state = mission.current_state
        expected = mission.success_condition or "the chosen mission produces a verifiable state change"

    return {
        "goal": mission.objective,
        "context_lock": _context_lock(state, mission),
        "current_state": current_state,
        "action": action,
        "expected_result": expected,
        "success_evidence": "tool receipt plus external postcondition when the action has an external effect",
        "cost": {
            "expected_minutes": mission.expected_minutes,
            "expected_cost": mission.expected_cost,
            "context_switch": mission.context_switch_cost,
        },
        "risk": {
            "level": mission.risk,
            "uncertainty": mission.uncertainty,
            "human_dependency": mission.human_dependency,
        },
        "authorization_basis": (
            "connected_account_or_verified_resource_plus_mandate"
            if state.get("account_permission") or state.get("connected_account") or state.get("verified_resource")
            else "mandate_or_low_risk_internal_action"
        ),
        "fallback": _fallback(mission),
        "next_action": action,
        "stop_condition": "verified_result_or_persisted_material_blocker",
        "mission": {
            "title": mission.title,
            "state": mission.current_state,
            "metadata": metadata,
        },
    }
