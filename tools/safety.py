#!/usr/bin/env python3
"""Policy guard for the Opportunity -> Application -> Execution pipeline."""
from __future__ import annotations

import argparse
import json
import sys


def decide(state: dict) -> dict:
    accepted = bool(state.get("accepted"))
    execution_plan = bool(state.get("execution_plan"))
    environment_discovered = bool(state.get("environment_discovered"))
    build_requested = bool(state.get("build_requested"))
    bounded_proof = bool(state.get("bounded_proof"))
    environment_known = bool(state.get("environment_known"))

    if build_requested and not accepted and not bounded_proof:
        return {
            "decision": "BLOCK",
            "reason": "substantial_build_before_acceptance",
            "next_action": "application_or_bounded_proof",
        }
    if accepted and not execution_plan:
        return {
            "decision": "PLAN_REQUIRED",
            "reason": "accepted_job_without_execution_plan",
            "next_action": "create_execution_plan",
        }
    if accepted and not environment_discovered:
        return {
            "decision": "DISCOVER_ENVIRONMENT",
            "reason": "accepted_job_without_environment_discovery",
            "next_action": "inspect_accounts_apps_permissions_existing_assets",
        }
    if accepted and not environment_known and build_requested:
        return {
            "decision": "DISCOVER_ENVIRONMENT",
            "reason": "do_not_build_until_actual_environment_is_understood",
            "next_action": "inspect_available_tools_accounts_apps_and_existing_assets",
        }
    return {
        "decision": "ALLOW",
        "reason": "execution_gate_satisfied",
        "next_action": "execute_and_verify",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="JSON object describing the current state")
    args = parser.parse_args()
    try:
        state = json.loads(args.json)
        result = decide(state)
    except (json.JSONDecodeError, TypeError) as exc:
        print(json.dumps({"decision": "ERROR", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
