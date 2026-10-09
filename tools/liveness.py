#!/usr/bin/env python3
"""Global action-liveness supervisor.

This guard exists to prevent an agent from repeatedly asking, planning, or ending
while an already-authorized action is executable. It is domain-agnostic: the
runtime supplies the action, capability, risk and evidence state.

The model may choose *what* should happen. This layer decides whether the next
runtime state is EXECUTE, VERIFY, RECOVER, WAIT, or HUMAN_REQUIRED.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any

TERMINAL = {"VERIFIED", "BLOCKED", "CANCELLED"}
EXECUTABLE = {"PLANNED", "READY", "RETRY_READY", "RECOVERY_READY"}
IN_FLIGHT = {"RUNNING", "SUBMITTED"}


def intent_key(d: dict[str, Any]) -> str:
    raw = json.dumps(
        {
            "scope": d.get("scope"),
            "action": d.get("action"),
            "target": d.get("target"),
            "payload": d.get("payload", {}),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def decide(d: dict[str, Any]) -> dict[str, Any]:
    requested = bool(d.get("requested", True))
    authorized = bool(d.get("authorized"))
    capability_available = bool(d.get("capability_available"))
    preconditions_met = bool(d.get("preconditions_met"))
    status = str(d.get("status", "READY")).upper()
    attempts = int(d.get("execution_attempts", 0))
    no_progress_cycles = int(d.get("no_progress_cycles", 0))
    confirmation_requests = int(d.get("confirmation_requests", 0))
    evidence = bool(d.get("execution_evidence"))
    expected_result = bool(d.get("expected_result"))
    recovery_available = bool(d.get("recovery_available"))
    independent_work = bool(d.get("independent_work_available"))
    human_required = bool(d.get("human_required"))
    session_end_requested = bool(d.get("session_end_requested"))

    key = intent_key(d)

    if status in TERMINAL:
        return {
            "decision": "NO_ACTION",
            "reason": "action_is_terminal",
            "action_key": key,
        }

    if session_end_requested and (status in EXECUTABLE or status in IN_FLIGHT):
        return {
            "decision": "BLOCK_SESSION_END",
            "reason": "executable_or_in_flight_action_must_reach_terminal_state",
            "next_action": "resume_or_execute_action",
            "action_key": key,
        }

    # Highest priority: an already-authorized action that can run now must run.
    # Any prior owner confirmation requests become evidence of a failed decision,
    # not a reason to ask again.
    if requested and authorized and capability_available and preconditions_met and status in EXECUTABLE:
        reason = "authorized_action_ready_for_execution"
        if confirmation_requests > 0:
            reason = "repeated_confirmation_is_invalid_when_action_is_already_executable"
        return {
            "decision": "EXECUTE_NOW",
            "reason": reason,
            "next_action": "invoke_tool_and_record_execution_receipt",
            "forbid_owner_confirmation": True,
            "action_key": key,
        }

    if status in IN_FLIGHT:
        if evidence:
            return {
                "decision": "VERIFY_OUTCOME",
                "reason": "execution_evidence_exists_but_postcondition_is_not_terminal",
                "next_action": "verify_expected_result",
                "action_key": key,
            }
        if no_progress_cycles >= 1:
            return {
                "decision": "RESUME_OR_INSPECT",
                "reason": "in_flight_action_has_no_progress_receipt",
                "next_action": "inspect_tool_run_or_browser_state_before_repeating",
                "action_key": key,
            }
        return {
            "decision": "WAIT_FOR_RECEIPT",
            "reason": "action_is_in_flight",
            "next_action": "wait_for_tool_receipt_or_heartbeat",
            "action_key": key,
        }

    if status in {"EXECUTED", "SUCCEEDED"}:
        if expected_result and not evidence:
            return {
                "decision": "VERIFY_OUTCOME",
                "reason": "execution_claim_without_evidence",
                "next_action": "verify_expected_result",
                "action_key": key,
            }
        return {
            "decision": "RECORD_AND_CONTINUE",
            "reason": "execution_completed",
            "next_action": "persist_result_and_choose_next_action",
            "action_key": key,
        }

    if recovery_available:
        return {
            "decision": "RECOVER",
            "reason": "known_recovery_path_available",
            "next_action": "run_recovery_strategy_before_new_owner_request",
            "action_key": key,
        }

    if human_required:
        return {
            "decision": "HUMAN_REQUIRED",
            "reason": "material_boundary_or_missing_capability_blocks_execution",
            "next_action": "persist_blocker_and_batch_owner_intervention",
            "action_key": key,
        }

    if no_progress_cycles > 0 and independent_work:
        return {
            "decision": "CONTINUE_INDEPENDENT_WORK",
            "reason": "current_action_has_no_progress_and_independent_work_exists",
            "next_action": "isolate_stalled_action_and_advance_other_work",
            "action_key": key,
        }

    if requested and not capability_available:
        return {
            "decision": "CAPABILITY_RECOVERY",
            "reason": "requested_action_cannot_execute_with_current_capability",
            "next_action": "discover_or_restore_capability_then_resume",
            "action_key": key,
        }

    if requested and not preconditions_met:
        return {
            "decision": "RESOLVE_PRECONDITIONS",
            "reason": "requested_action_is_not_ready",
            "next_action": "resolve_only_material_missing_preconditions",
            "action_key": key,
        }

    if attempts >= 1 and not evidence:
        return {
            "decision": "INSPECT_BEFORE_REPEAT",
            "reason": "prior_attempt_has_no_receipt_or_result_evidence",
            "next_action": "inspect_tool_run_and_external_state",
            "action_key": key,
        }

    return {
        "decision": "WAIT",
        "reason": "action_not_requested_or_no_safe_progress_path",
        "next_action": "persist_next_wake_or_new_work",
        "action_key": key,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", required=True)
    try:
        data = json.loads(p.parse_args().json)
        print(json.dumps(decide(data), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"decision": "ERROR", "reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
