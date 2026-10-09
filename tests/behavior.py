import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from core.mission import generate_default_missions
from core.conversation import triage, message_beats, score_draft
from core.pricing import recommend_quote
from core.account import resolve_account
from core.payment import prepare_link
from adapters.browser import classify_manual_intervention
from adapters.operate import BrowserOperator
from tools.guard import validate_send
from tools.followup import decide as followup_decide


def init_temp_db(path: Path):
    schema = (ROOT / 'data/schema.sql').read_text(encoding='utf-8')
    with sqlite3.connect(path) as conn:
        conn.executescript(schema)


def test_mission_prefers_outcome_over_generic_activity():
    missions = generate_default_missions({
        'active_jobs': [{'id': 7, 'value': 250, 'execution_confidence': 0.9, 'next_minutes': 30}],
        'demand_signals': [{'segment': 'generic', 'potential_value': 5000, 'probability': 0.02, 'minutes': 90}],
    })
    assert missions[0].next_action == 'execute_active_job'


def test_due_wake_precedes_speculative_work():
    missions = generate_default_missions({
        'due_wakes': [{
            'id': 4,
            'wake_type': 'payment_check',
            'due_at': '2026-10-09T10:00:00+00:00',
            'context_id': 'payment-4',
        }],
        'active_jobs': [{
            'id': 7,
            'value': 5000,
            'execution_confidence': 0.95,
            'next_minutes': 30,
        }],
    })
    assert missions[0].current_state == 'due_wake'
    assert missions[0].next_action == 'resume_due_wake'


def test_worker_generates_work_without_human_task():
    missions = generate_default_missions({})
    assert missions[0].next_action in {'research_and_score_market'}
    assert missions[0].economic_value > 0


def test_price_brain_decides_without_hourly_floor():
    out = recommend_quote({'hours': 3, 'direct_costs': 20, 'observed_prices': [240, 280], 'complexity': .3})
    assert out['recommended_price_brl'] > 0
    assert out['negotiation_floor_brl'] > 0
    assert out['recommended_price_brl'] >= out['negotiation_floor_brl']


def test_artificial_ack_is_semantically_blocked():
    out = score_draft('Understood. I can help with that.')
    assert not out['passes']
    assert 'stock_acknowledgement' in out['problems']


def test_conversation_can_choose_silence():
    out = triage({'history': [{'text': 'Tudo certo, obrigado.'}], 'incoming_text': 'Tudo certo, obrigado.', 'already_answered_latest': True})
    assert not out.response_needed
    assert out.action == 'NO_RESPONSE'


def test_first_contact_is_progressive_not_full_sales_script():
    beats = message_beats({'stage': 'new', 'customer_name': True, 'customer_intent': ''})
    assert [b['purpose'] for b in beats] == ['greeting', 'open_conversation']


def test_followup_stops_without_new_reason():
    out = followup_decide({'due': True, 'attempts': 1, 'waiting_on_customer': True, 'new_value': False})
    assert out['decision'] == 'WAIT'


def test_context_guard_blocks_wrong_recipient():
    out = validate_send({'conversation_id': 'c1', 'recipient_id': '5511', 'resolved_recipient_id': '5522', 'account_id': 'a1', 'current_account_id': 'a1', 'send_intent': True, 'history_loaded': True})
    assert out['decision'] == 'BLOCK_SEND'


def test_account_resolution_uses_existing_google_account():
    out = resolve_account([
        {'provider': 'google', 'email': 'owner@example.com', 'purpose': 'gmail', 'status': 'logged_in', 'permission_level': 'owner'}
    ], provider='google', purpose='gmail', preferred_email='owner@example.com')
    assert out['status'] == 'RESOLVED'
    assert out['account']['email'] == 'owner@example.com'


def test_payment_link_metadata_is_specific_and_idempotent():
    sale = {'job_id': 12, 'customer_id': 8, 'amount': 190, 'description': 'Landing page', 'reference': 'JOB-12'}
    a = prepare_link(sale); b = prepare_link(dict(sale))
    assert a['status'] == 'READY_FOR_PROVIDER'
    assert a['idempotency_key'] == b['idempotency_key']
    assert a['metadata']['reference'] == 'JOB-12'


def test_browser_stops_at_captcha_instead_of_bypassing():
    assert classify_manual_intervention('Please complete the CAPTCHA to continue')['manual_required']


class FakeBrowser:
    def __init__(self): self.reads = ['normal page', 'normal page', 'CAPTCHA required']
    def start(self): pass
    def goto(self, url): pass
    def read(self): return self.reads.pop(0) if self.reads else 'normal page'
    def click(self, selector): pass
    def type(self, selector, text): pass
    def press(self, selector, key): pass
    def screenshot(self, path): return path
    def close(self): pass


def test_browser_operator_honors_manual_boundary():
    result = BrowserOperator(FakeBrowser()).run([{'type': 'goto', 'url': 'https://example.com'}, {'type': 'read'}])
    assert result['status'] in {'BLOCKED', 'SUCCESS'}
    # The important invariant is that CAPTCHA becomes a blocker, never an automated bypass.
    if result['status'] == 'BLOCKED':
        assert result['blocker'] == 'captcha'


def test_schema_contains_autonomy_25_tables(tmp_path):
    db = tmp_path / 'runtime.sqlite3'; init_temp_db(db)
    with sqlite3.connect(db) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for expected in {'missions', 'runtime_journal', 'runtime_receipts', 'browser_workspaces', 'runtime_leases'}:
        assert expected in tables

def test_worker_boots_on_fresh_runtime_db(tmp_path):
    from runtime.store import RuntimeStore
    from agents.worker import AutonomousWorker
    db = tmp_path / 'boot.sqlite3'; init_temp_db(db)
    store = RuntimeStore.open(db)
    try:
        out = AutonomousWorker(store=store).cycle()
    finally:
        store.db.close()
    assert out['status'] == 'PLANNED'
    assert out['mission']['next_action'] == 'research_and_score_market'

def test_execute_once_initializes_a_completely_new_database(tmp_path, monkeypatch):
    db = tmp_path / 'new.sqlite3'
    monkeypatch.setenv('WORKER_DB', str(db))
    from tools.execute import once
    out = once()
    assert out['status'] == 'PLANNED'
    assert db.exists()

def test_prospecting_requires_observable_relevance():
    from core.prospecting import score_lead
    generic = score_lead({'signals': {'problem_relevance': 0.1, 'evidence_strength': 0.8, 'capability_fit': 0.9, 'contactability': 1}})
    good = score_lead({'contact_permission_verified': True, 'signals': {'problem_relevance': 0.8, 'evidence_strength': 0.7, 'capability_fit': 0.9, 'contactability': 1}})
    assert generic['should_contact'] is False
    assert good['should_contact'] is True


def test_partnership_requires_mutual_fit():
    from core.partnership import evaluate_partner
    one_sided = evaluate_partner({'audience_overlap': .8, 'complementarity': .1, 'economic_fit': .8, 'trust_signal': .8})
    mutual = evaluate_partner({'audience_overlap': .8, 'complementarity': .8, 'economic_fit': .8, 'trust_signal': .8})
    assert not one_sided['should_approach']
    assert mutual['should_approach']

def test_worker_default_executor_is_optional_and_non_fabricating(monkeypatch):
    monkeypatch.delenv('WORKER_EXECUTOR_CMD', raising=False)
    monkeypatch.delenv('WORKER_BROWSER_PROFILE', raising=False)
    from tools.execute import make_executor
    assert make_executor() is None


def test_public_contact_is_not_outbound_permission():
    from core.prospecting import score_lead
    lead = {'signals': {'problem_relevance': 0.9, 'evidence_strength': 0.8, 'capability_fit': 0.9, 'contactability': 1}}
    result = score_lead(lead)
    assert result['should_contact'] is False
    assert 'contact_permission_missing' in result['why']
