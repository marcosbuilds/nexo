#!/usr/bin/env python3
"""Small state machine for durable action commitments.

The runtime can persist this object in the execution_commitments table. An
intent that is ready to execute remains alive until it becomes terminal or hits
a real boundary. Planning, asking permission, or ending a session do not clear
the commitment.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ActionCommitment:
    action_key: str
    status: str = "READY"
    attempts: int = 0
    confirmation_requests: int = 0
    no_progress_cycles: int = 0
    expected_result: str = ""
    evidence_ref: Optional[str] = None
    blocker_class: Optional[str] = None
    next_action: str = "EXECUTE_NOW"
    updated_at: str = ""

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def record_confirmation_request(self) -> None:
        self.confirmation_requests += 1
        self.no_progress_cycles += 1
        self.next_action = "EXECUTE_NOW"
        self.touch()

    def record_execution_started(self) -> None:
        self.status = "RUNNING"
        self.attempts += 1
        self.next_action = "WAIT_FOR_RECEIPT"
        self.touch()

    def record_result(self, evidence_ref: str | None, verified: bool) -> None:
        self.evidence_ref = evidence_ref
        self.status = "VERIFIED" if verified else "EXECUTED"
        self.next_action = "RECORD_AND_CONTINUE" if verified else "VERIFY_OUTCOME"
        self.no_progress_cycles = 0
        self.touch()

    def record_block(self, blocker_class: str) -> None:
        self.status = "BLOCKED"
        self.blocker_class = blocker_class
        self.next_action = "QUEUE_BLOCKER_AND_CONTINUE"
        self.touch()

    def to_dict(self) -> dict:
        if not self.updated_at:
            self.touch()
        return asdict(self)
