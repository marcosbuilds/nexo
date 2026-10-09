"""Autonomous worker: restore -> observe -> choose mission -> act -> verify -> learn."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable

from core.mission import Mission, generate_default_missions
from core.conversation import triage
from core.pricing import recommend_quote
from core.decision import build_plan


@dataclass
class ActionReceipt:
    action: str
    status: str
    result: dict[str, Any]
    evidence_ref: str | None = None
    blocker: str | None = None


class AutonomousWorker:
    """Decision engine independent of any particular browser/channel implementation."""
    def __init__(self, *, store, executor: Callable[[Mission], ActionReceipt] | None = None, now: Callable[[], datetime] | None = None):
        self.store = store
        self.executor = executor
        self.now = now or (lambda: datetime.now(timezone.utc))

    def observe(self) -> dict[str, Any]:
        return self.store.snapshot()

    def choose_mission(self, state: dict[str, Any]) -> Mission:
        missions = generate_default_missions(state)
        return missions[0]

    def cycle(self) -> dict[str, Any]:
        state = self.observe()
        due = self.store.claim_due_wakes(self.now().isoformat())
        state["due_wakes"] = due
        mission = self.choose_mission(state)
        mission_json = mission.materialize_priority()
        decision_plan = build_plan(state, mission)
        mission_json["decision_plan"] = decision_plan
        self.store.persist_mission(mission_json)
        self.store.journal("MISSION_CHOSEN", mission_json)
        self.store.journal("DECISION_PLAN", decision_plan)

        if self.executor is None:
            return {"status": "PLANNED", "mission": mission_json, "reason": "no external executor registered"}

        receipt = self.executor(mission)
        self.store.record_receipt(mission_json, receipt)
        if receipt.blocker or str(receipt.status).upper() in {"FAILED", "BLOCKED"}:
            blocker = receipt.blocker or f"RECEIPT_{str(receipt.status).upper()}"
            self.store.journal("BLOCKED", {"mission": mission_json, "blocker": blocker})
            self.store.record_learning({
                "category": "execution_failure",
                "expected": decision_plan["expected_result"],
                "observed": receipt.status,
                "evidence": receipt.evidence_ref or receipt.result,
                "cause": blocker,
                "change": decision_plan["fallback"],
                "regression": "verify the fallback result before retrying the original route",
                "lesson": "do not repeat this route without a state or route change",
            })
        else:
            self.store.journal("RECEIPT", {"mission": mission_json, "receipt": receipt.__dict__})
        return {"status": receipt.status, "mission": mission_json, "receipt": receipt.__dict__, "timestamp": self.now().isoformat()}

    @staticmethod
    def plan_conversation(context: dict[str, Any]) -> dict[str, Any]:
        return triage(context).to_dict()

    @staticmethod
    def price(data: dict[str, Any]) -> dict[str, Any]:
        return recommend_quote(data)
