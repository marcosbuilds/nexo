#!/usr/bin/env python3
"""Canonical per-cycle guard sequence for the external runtime.

This wrapper makes the policy difficult to partially implement: authorization,
action liveness and owner-message gating are evaluated together.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from authorization import decide as authorization_decide  # noqa: E402
from liveness import decide as liveness_decide  # noqa: E402
from approve import decide as owner_guard_decide  # noqa: E402
from communicate import decide as communication_decide  # noqa: E402
from search import plan as work_seeking_plan  # noqa: E402


def tick(d: dict) -> dict:
    auth = authorization_decide(d)
    authorized = auth.get("decision") == "ALLOW"

    live = dict(d)
    live["requested"] = d.get("requested", True)
    live["authorized"] = d.get("authorized", authorized)
    live["capability_available"] = d.get("capability_available", bool(d.get("verified_resource") or d.get("account_permission") or not d.get("capability")))
    live["preconditions_met"] = d.get("preconditions_met", True)
    live_result = liveness_decide(live)

    owner = owner_guard_decide({
        "owner_channel": d.get("owner_channel", False),
        "authorized_and_executable": live_result.get("decision") == "EXECUTE_NOW",
        "message": d.get("message", "")
    })

    communication = communication_decide({
        "response_needed": d.get("response_needed", False),
        "draft": d.get("message", ""),
        "channel": d.get("channel", "whatsapp"),
        "recent_openings": d.get("recent_openings", []),
        "conversation_goal": d.get("conversation_goal"),
        "desired_next_customer_state": d.get("desired_next_customer_state"),
        "triage_reason": d.get("triage_reason")
    })

    work_seek = None
    if d.get("queue_empty"):
        work_seek = work_seeking_plan(d.get("work_state") or {})

    return {
        "authorization": auth,
        "liveness": live_result,
        "owner_message_guard": owner,
        "communication": communication,
        "work_seeking": work_seek,
        "terminal": (
            live_result.get("decision") in {"NO_ACTION", "HUMAN_REQUIRED"}
            and owner.get("decision") != "BLOCK"
            and communication.get("decision") not in {"REGENERATE", "REPLAN"}
            and not (d.get("queue_empty") and work_seek and work_seek.get("decision") == "CONTINUE_WORK_SEEKING")
        ),
        "next_action": (work_seek or {}).get("next_action") if work_seek and work_seek.get("decision") != "WAIT_FOR_EVENT" else live_result.get("next_action")
    }


def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--json", required=True)
    try:
        print(json.dumps(tick(json.loads(p.parse_args().json)), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"decision":"ERROR","reason":str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
