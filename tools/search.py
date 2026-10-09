#!/usr/bin/env python3
"""Deterministic demand-generation planner for the continuous worker.

This does not browse the internet itself. It tells the external runtime what to
inspect next, why, and how to diversify when the immediate queue is empty.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

SOURCES = [
    "freelance_marketplaces",
    "job_boards",
    "direct_company_sites",
    "local_business_directories_and_maps",
    "public_social_profiles",
    "communities_and_forums",
    "existing_clients_and_repeat_demand",
    "referral_or_inbound_signals",
]


def _num(d: dict[str, Any], key: str) -> int:
    try:
        return max(0, int(d.get(key, 0)))
    except (TypeError, ValueError):
        return 0


def plan(state: dict[str, Any]) -> dict[str, Any]:
    active = _num(state, "active_jobs")
    pending = _num(state, "pending_outcomes")
    hot = _num(state, "hot_conversations")
    due = _num(state, "due_followups")
    repeat = _num(state, "repeat_candidates")
    qualified = _num(state, "qualified_opportunities")
    blocked = _num(state, "human_blockers")
    recent_sources = [str(x) for x in state.get("recent_sources", []) if str(x)]
    capability_gaps = [str(x) for x in state.get("capability_gaps", []) if str(x)]
    connected_platforms = [str(x) for x in state.get("connected_platforms", []) if str(x)]

    actions: list[dict[str, Any]] = []
    if active:
        actions.append({"type": "EXECUTE_ACTIVE_JOB", "priority": 100, "reason": "active paid work exists"})
    if pending:
        actions.append({"type": "VERIFY_EXTERNAL_OUTCOMES", "priority": 95, "reason": "previous actions can still generate consequences"})
    if hot or due:
        actions.append({"type": "HANDLE_CONVERSATION_QUEUE", "priority": 90, "reason": "customer communication can materially change revenue"})
    if repeat:
        actions.append({"type": "CHECK_REPEAT_DEMAND", "priority": 86, "reason": "existing relationships have lower acquisition friction"})
    if qualified:
        actions.append({"type": "ADVANCE_QUALIFIED_OPPORTUNITIES", "priority": 84, "reason": "qualified leads already have context"})

    # Once execution work is covered, create demand instead of ending.
    if not actions:
        used = set(recent_sources[-2:])
        fresh_sources = [s for s in SOURCES if s not in used]
        selected = fresh_sources[:2] or SOURCES[:2]
        for source in selected:
            actions.append({
                "type": "RESEARCH_DEMAND",
                "priority": 70,
                "source": source,
                "reason": "immediate queue is empty; actively seek legitimate demand",
                "query_strategy": "use multiple query families, inspect real need, score economics, save actionable leads only",
            })
        if "local_business_directories_and_maps" in connected_platforms:
            actions.append({
                "type": "DIRECT_PROSPECTING",
                "priority": 68,
                "source": "local_business_directories_and_maps",
                "reason": "connected research channel can surface businesses with public need signals",
                "constraint": "personalized, low-volume, relevance-first outreach; honor opt-outs and platform rules",
            })
        if any(p in connected_platforms for p in {"instagram", "facebook", "canva"}):
            actions.append({
                "type": "CONTENT_DISTRIBUTION",
                "priority": 64,
                "reason": "connected creative/social stack can create inbound demand while prospecting continues",
                "constraint": "use real work, useful insights and verifiable results; no filler or fabricated proof",
            })

        if capability_gaps:
            actions.append({
                "type": "CAPABILITY_PROBE",
                "priority": 55,
                "reason": "a small test may unlock additional economically useful work",
                "capabilities": capability_gaps[:3],
            })

    # Avoid staying on one channel just because it produced a result once.
    channel_counts: dict[str, int] = {}
    for source in recent_sources:
        channel_counts[source] = channel_counts.get(source, 0) + 1
    for action in actions:
        src = action.get("source")
        if src and channel_counts.get(src, 0) >= 2:
            action["diversify"] = True
            action["reason"] += "; diversify after repeated same-source cycles"

    actions.sort(key=lambda x: int(x.get("priority", 0)), reverse=True)
    if not actions:
        return {
            "decision": "WAIT_FOR_EVENT",
            "reason": "no proactive front available after evaluating the demand-generation policy",
            "next_action": "persist_next_wake_and_wait",
            "human_blockers": blocked,
        }
    return {
        "decision": "CONTINUE_WORK_SEEKING",
        "reason": "the worker must convert an empty execution queue into a demand-generation cycle",
        "actions": actions,
        "next_action": actions[0]["type"],
        "human_blockers": blocked,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    args = ap.parse_args()
    print(json.dumps(plan(json.loads(args.json)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
