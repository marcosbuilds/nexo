#!/usr/bin/env python3
"""Build the small context packet used by every worker cycle.

The model receives decisions and contracts, not a concatenation of every
policy/document in the repository. Detailed files remain available for
on-demand retrieval when the current decision actually depends on them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "memory" / "cache.json"
CORE_FILES = [
    "docs/core.md",
    "docs/context.md",
    "config/authorization.json",
    "config/runtime.json",
    "config/recovery.json",
    "config/communication.json",
]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(force: bool = False) -> dict[str, Any]:
    sources: dict[str, dict[str, Any]] = {}
    changed = force or not CACHE.exists()
    previous: dict[str, Any] = {}
    if CACHE.exists() and not force:
        try:
            previous = json.loads(CACHE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            changed = True

    for rel in CORE_FILES:
        path = ROOT / rel
        if not path.exists():
            raise FileNotFoundError(rel)
        stat = path.stat()
        digest = _digest(path)
        sources[rel] = {
            "sha256": digest,
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }
        if (previous.get("sources") or {}).get(rel) != sources[rel]:
            changed = True

    if CACHE.exists() and not changed and previous:
        return previous

    packet = {
        "version": "0.3.0",
        "purpose": "compact_decision_context",
        "source_of_truth": "docs/core.md",
        "foundation_reference": "docs/foundations.md",
        "load_policy": {
            "load_once_per_cycle": True,
            "retrieve_only_relevant_detail": True,
            "never_load_full_project_for_routine_work": True,
            "historical_plans_are_not_runtime_rules": True,
        },
        "non_negotiables": [
            "worker_owns_outcomes; owner_supplies_identity_access_and_human_boundaries",
            "connected_access_plus_mandate_plus_allowed_platform_plus_in_limit_risk_means_execute",
            "never_request_micro_confirmation_for_authorized_executable_routine_work",
            "every material action has expected result, evidence, recovery and next action",
            "context_lock prevents mixing account person conversation platform and goal",
            "silence is valid; research must change a decision; no cosmetic busywork",
            "never claim success without a receipt or external evidence",
        ],
        "decision_contract": [
            "goal",
            "context_lock",
            "current_state",
            "action",
            "expected_result",
            "success_evidence",
            "cost",
            "risk",
            "authorization_basis",
            "fallback",
            "next_action",
            "stop_condition",
        ],
        "priority": [
            "in_flight_commitment",
            "pending_consequence",
            "accepted_work",
            "urgent_or_active_conversation",
            "qualified_opportunity",
            "research_or_demand_generation",
            "cheap_capability_probe",
            "persisted_wait",
        ],
        "authorization": {
            "routine_connected_scope": [
                "read",
                "research",
                "send_message",
                "start_or_continue_dm",
                "create_edit_archive_delete_conversation",
                "calendar",
                "authorized_content",
                "follow_up",
            ],
            "human_only": [
                "identity_or_manual_verification",
                "legal_binding_acceptance",
                "security_incident",
                "spend_above_limit",
                "financial_transfer_out",
                "material_fact_not_discoverable",
            ],
            "invalid_transition": "ask_permission_or_end_when_action_is_authorized_and_executable",
        },
        "communication": [
            "recover_history_and_stage",
            "choose_one_goal",
            "send_smallest_useful_next_step",
            "use_NO_SEND_when_silence_is_better",
            "run_humanizer_and_channel_gate_before_send",
        ],
        "research": [
            "turn_uncertainty_into_a_decision_question",
            "compare_offer_x_buyer_hypotheses",
            "use_diverse_recent_sources",
            "record_url_date_fact_inference_and_decision_changed",
        ],
        "recovery": [
            "classify_error",
            "inspect_external_state",
            "change_one_variable",
            "retry_once_only_after_state_or_route_change",
            "verify_or_persist_blocker_and_continue_independent_work",
        ],
        "learning": [
            "expected_observed_evidence_cause_change_regression",
            "one_occurrence_is_a_hypothesis",
            "promote_practice_only_after_repeat_or_comparable_test",
        ],
        "cost_control": [
            "prefer_existing_tool_or_cheap_probe",
            "do_not_repeat_without_new_information",
            "do_not_write_a_report_when_a_decision_or_action_is_due",
            "retrieve_only_facts_that_can_change_the_current_decision",
        ],
        "sources": sources,
    }

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(
        json.dumps(packet, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return packet


def load() -> dict[str, Any]:
    return build(force=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = build(force=args.refresh)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Runtime context loaded.")
        for rule in result["non_negotiables"]:
            print(f"- {rule}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
