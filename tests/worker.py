import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from authorization import decide as authorization
from context import build as build_context
from recover import recover
from operate import preflight
from approve import decide as owner_confirmation

from core.decision import build_plan
from core.mission import Mission
from agents.worker import ActionReceipt, AutonomousWorker
from runtime.store import RuntimeStore


def test_connected_account_covers_routine_conversation_operations():
    for action in (
        "start_dm",
        "send_message",
        "edit_conversation",
        "archive_conversation",
        "delete_conversation",
    ):
        result = preflight({"action": action, "account_permission": True})
        assert result["decision"] == "ALLOW_EXECUTE", (action, result)
        assert result["forbid_owner_confirmation"] is True


def test_authorization_gate_does_not_reopen_connected_scope_for_dm_or_delete():
    for capability in ("start_or_continue_dm", "delete_conversation"):
        result = authorization({"capability": capability, "account_permission": True})
        assert result["decision"] == "ALLOW", (capability, result)


def test_owner_confirmation_guard_catches_conversation_permission_reflex():
    result = owner_confirmation(
        {
            "owner_channel": True,
            "authorized_and_executable": True,
            "message": "May I delete this conversation and start a DM?",
        }
    )
    assert result["decision"] == "BLOCK"


def test_retry_requires_new_state_and_stops_after_two_attempts():
    unchanged = recover("TRANSIENT_NETWORK", 0, state_changed=False)
    assert unchanged["retry"] is False
    assert unchanged["action"] == "INSPECT_AND_CHANGE_STATE"

    changed = recover("TRANSIENT_NETWORK", 0, state_changed=True)
    assert changed["retry"] is True

    exhausted = recover("TRANSIENT_NETWORK", 2, state_changed=True)
    assert exhausted["retry"] is False


def test_decision_plan_contains_action_cost_evidence_and_recovery():
    mission = Mission(
        title="Verificar retorno",
        objective="Confirm the result of a sent action.",
        current_state="pending_consequence",
        next_action="verify_external_outcome",
        success_condition="return confirmed with evidence",
        expected_minutes=7,
        risk=0.1,
    )
    plan = build_plan({"account_permission": True, "conversation_id": "c-1"}, mission)
    assert plan["action"] == "verify_external_outcome"
    assert plan["expected_result"] == "return confirmed with evidence"
    assert plan["cost"]["expected_minutes"] == 7
    assert plan["fallback"]
    assert plan["stop_condition"] == "verified_result_or_persisted_material_blocker"


def test_learning_record_requires_evidence_chain_and_persists():
    connection = sqlite3.connect(":memory:")
    connection.executescript((ROOT / "data/schema.sql").read_text(encoding="utf-8"))
    store = RuntimeStore(connection)
    store.record_learning(
        {
            "category": "test",
            "expected": "a receipt",
            "observed": "blocked",
            "evidence": "tool-log-1",
            "cause": "stale state",
            "change": "refresh before retry",
            "regression": "repeat with refreshed state",
            "lesson": "do not repeat a stale route",
        }
    )
    row = connection.execute(
        "SELECT category, observation FROM learning_events ORDER BY id DESC LIMIT 1"
    ).fetchone()
    observation = json.loads(row[1])
    assert row[0] == "test"
    assert observation["lesson"] == "do not repeat a stale route"


def test_context_packet_is_canonical_and_does_not_load_legacy_rulebooks(tmp_path):
    # build() writes the normal cache, but this assertion only inspects the
    # returned packet and protects the source-selection contract.
    packet = build_context(force=True)
    assert packet["version"] == "0.3.1"
    assert packet["source_of_truth"] == "docs/core.md"
    assert packet["foundation_reference"] == "docs/foundations.md"
    assert "decision_contract" in packet
    assert "docs/foundations.md" not in packet["sources"]
    assert "docs/legacy/Nucleo_Operacional.md" not in packet["sources"]


def test_worker_records_failed_receipt_even_without_explicit_blocker(tmp_path):
    connection = sqlite3.connect(":memory:")
    connection.executescript((ROOT / "data/schema.sql").read_text(encoding="utf-8"))
    store = RuntimeStore(connection)

    def failed_executor(mission):
        return ActionReceipt(
            mission.next_action or "unknown",
            "FAILED",
            {"message": "provider rejected the unchanged request"},
        )

    result = AutonomousWorker(store=store, executor=failed_executor).cycle()
    assert result["status"] == "FAILED"
    row = connection.execute(
        "SELECT category FROM learning_events ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert row[0] == "execution_failure"
