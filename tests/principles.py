import json
import sqlite3
import sys
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))

from core.design import build_design_brief
from core.market import default_market_plan, record_event, snapshot as market_snapshot
from core.message import package_message
from runtime.store import RuntimeStore
from communicate import decide as communication_gate
from converse import decide as conversation_gate


def test_market_starts_with_diverse_offer_buyer_hypotheses():
    plan = default_market_plan()
    candidates = plan['candidate_scan']
    assert plan['phase'] == 'initial_scan'
    assert plan['offer_hypothesis'] is None
    assert len(candidates) == 4
    ids = {candidate['id'] for candidate in candidates}
    assert ids == {
        'creative_assets_home_services',
        'landing_page_local_business',
        'python_workflow_automation',
        'verified_market_research',
    }
    assert len({tuple(candidate['required_capabilities']) for candidate in candidates}) == 4
    assert all(candidate['stats']['score_basis'] == 'prior_only_hypothesis' for candidate in candidates)


def test_runtime_store_no_longer_injects_static_generic_market_demand(tmp_path):
    db_path = tmp_path / 'runtime.sqlite3'
    schema = (ROOT / 'data/schema.sql').read_text(encoding='utf-8')
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema)
    store = RuntimeStore.open(db_path)
    try:
        state = store.snapshot()
    finally:
        store.db.close()
    assert state['market_strategy']['phase'] == 'initial_scan'
    assert len(state['demand_signals']) == 4
    assert all(item['niche_id'] != 'broad_market_demand' for item in state['demand_signals'])
    assert all(item['required_capabilities'] for item in state['demand_signals'])


def test_art_direction_matches_air_conditioning_category_not_barber_default():
    brief = build_design_brief({
        'business': {'name': 'Clima Teste', 'category': 'Empresa de ar-condicionado', 'profile_url': 'https://example.com'},
        'main_subject': 'technician inspecting a split unit',
        'offer': 'limpeza de ar-condicionado',
        'headline': 'Ar mais limpo',
        'cta': 'Request a quote',
    })
    assert brief['niche_id'] == 'home_services'
    assert 'barbeiro' not in brief['magic_media_element_prompt'].lower()
    assert 'ar-condicionado' in brief['magic_media_element_prompt'].lower()


def test_unknown_business_category_gets_context_specific_style_and_url_is_not_brand_observation():
    brief = build_design_brief({
        'business': {'name': 'Test Veterinary Clinic', 'category': 'Veterinary clinic', 'profile_url': 'https://example.com'},
        'offer': 'veterinary consultation', 'headline': 'Book a consultation', 'cta': 'Contact the clinic',
    })
    assert brief['niche_id'] == 'context_specific'
    assert brief['brand_observation_status'] == 'not_observed_url_is_reference_only'
    assert brief['publish_ready'] is False
    assert any('observed visual identity' in item for item in brief['facts_to_verify_before_publish'])


def test_transparent_cutout_prompt_does_not_conflict_with_text_negative_space():
    brief = build_design_brief({
        'business': {'category': 'Empresa de ar-condicionado'},
        'transparent_background': True,
        'no_text_in_generated_asset': True,
        'main_subject': 'aparelho split inverter branco completo',
    })
    prompt = brief['magic_media_element_prompt'].lower()
    assert 'genuinely transparent' in prompt
    assert 'no need to reserve text space inside the object' in prompt


def test_whatsapp_limits_and_compatibility_gate_are_consistent():
    policy = json.loads((ROOT / 'config/communication.json').read_text(encoding='utf-8'))
    limit = policy['message_packaging']['channel_defaults']['whatsapp']['max_chars_hard_limit']
    assert limit == 260
    draft = 'The first part explains the result we can deliver. The second part defines the scope and what is included. The third part asks only for the next step to continue.'
    direct = communication_gate({'response_needed': True, 'draft': draft, 'channel': 'whatsapp'})
    compat = conversation_gate({'response_needed': True, 'draft': draft, 'channel': 'whatsapp'})
    assert direct['decision'] == compat['decision'] == 'SEND'
    assert direct['bubbles'] == compat['bubbles']
    assert len(direct['bubbles']) <= 3
    assert all(len(message) <= limit for message in direct['bubbles'])
    packaged = package_message('A' * 280, max_chars=limit)
    assert packaged['fits_limits'] is False


def test_market_learning_records_research_and_capability_evidence():
    conn = sqlite3.connect(':memory:')
    try:
        conn.row_factory = sqlite3.Row
        record_event(conn, {
            'niche_id': 'python_workflow_automation', 'event_type': 'research_cycle',
            'external_ref': 'test:python:query-1',
            'evidence': {'reason': 'Research completed; sources reviewed.', 'source_urls': ['https://example.org/source-a', 'https://example.org/source-b'], 'source_count': 2, 'qualified_count': 1},
        })
        result = record_event(conn, {
            'niche_id': 'python_workflow_automation', 'event_type': 'capability_tested',
            'external_ref': 'test:python:capability-1',
            'evidence': {'capability_fit': 0.9, 'reason': 'A amostra passou nos testes definidos.'},
        })
        metrics = next(x for x in result['candidate_scores'] if x['niche_id'] == 'python_workflow_automation')
        assert metrics['research_cycles'] == 1
        assert metrics['capability_tests'] == 1
        assert metrics['has_capability_evidence'] is True
        assert metrics['has_observed_market_evidence'] is False
        assert metrics['metrics']['capability_fit'] > 0.5
    finally:
        conn.close()


def test_initial_scan_winner_requires_both_buyer_and_capability_evidence():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    try:
        before = market_snapshot(conn)
        target = before['candidate_scan'][0]['id']
        # Three qualified buyers without a capability test must not finish the scan.
        for index in range(3):
            record_event(conn, {
                'niche_id': target, 'event_type': 'qualified_lead',
                'external_ref': f'test:lead:{index}',
            'evidence': {'observed_need': 0.8, 'contactability': 0.8, 'contact_channel_observed': 'public commercial form', 'source_urls': [f'https://example.org/business/{index}'], 'reason': 'public evidence verified'},
            })
        midway = market_snapshot(conn)
        assert midway['phase'] == 'initial_scan'
        record_event(conn, {
            'niche_id': target, 'event_type': 'capability_tested', 'external_ref': 'test:capability:one',
            'evidence': {'capability_fit': 0.8, 'reason': 'sample passed'},
        })
        after_one = market_snapshot(conn)
        assert after_one['phase'] == 'initial_scan'  # remaining candidates still need comparable evidence
    finally:
        conn.close()


def test_whatsapp_limits_have_one_policy_source():
    from core.limits import whatsapp_limits
    policy = json.loads((ROOT / 'config/communication.json').read_text(encoding='utf-8'))
    configured = policy['message_packaging']['channel_defaults']['whatsapp']
    assert whatsapp_limits() == {
        'max_bubbles': configured['max_bubbles_without_special_reason'],
        'max_chars': configured['max_chars_hard_limit'],
    }
    default_package = package_message('Primeira ideia. Segunda ideia com um pouco mais de contexto.')
    assert default_package['limits'] == {
        'max_bubbles': configured['max_bubbles_without_special_reason'],
        'max_chars_per_bubble': configured['max_chars_hard_limit'],
    }


def test_legacy_market_focus_and_evidence_migrate_without_loss():
    from core.market import snapshot as market_snapshot
    conn = sqlite3.connect(':memory:')
    try:
        conn.execute('''CREATE TABLE market_niche_observations (
            id INTEGER PRIMARY KEY, niche_id TEXT NOT NULL, event_type TEXT NOT NULL,
            external_ref TEXT, evidence_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )''')
        # Simulate the previous deployed state before candidate_scan_json existed.
        conn.execute('''CREATE TABLE market_strategy_state (
            id INTEGER PRIMARY KEY CHECK (id=1), active_niche_id TEXT NOT NULL,
            selected_at TEXT NOT NULL, phase TEXT NOT NULL DEFAULT 'initial_scan',
            reason TEXT NOT NULL DEFAULT '', last_review_at TEXT
        )''')
        conn.execute(
            'INSERT INTO market_niche_observations(niche_id,event_type,external_ref,evidence_json,created_at) VALUES(?,?,?,?,?)',
            ('barber_beauty', 'qualified_lead', 'old:public-profile-1',
             json.dumps({'observed_need': 0.7, 'reason': 'old verified evidence'}), '2026-10-01T12:00:00+00:00'),
        )
        conn.execute(
            'INSERT INTO market_strategy_state(id,active_niche_id,selected_at,phase,reason,last_review_at) VALUES(1,?,?,?,?,?)',
            ('barber_beauty', '2026-10-01T12:00:00+00:00', 'validation', 'Previous focus with evidence', None),
        )
        conn.commit()
        state = market_snapshot(conn)
        rows = conn.execute('SELECT niche_id,event_type,external_ref,evidence_json FROM market_niche_observations').fetchall()
        assert state['active_niche']['id'] == 'creative_assets_barber_beauty'
        assert len(rows) == 1
        assert rows[0][0] == 'creative_assets_barber_beauty'
        assert rows[0][1] == 'qualified_lead'
        assert rows[0][2] == 'old:public-profile-1'
        assert json.loads(rows[0][3])['reason'] == 'old verified evidence'
        assert conn.execute("SELECT COUNT(*) FROM market_niche_observations WHERE niche_id='barber_beauty'").fetchone()[0] == 0
    finally:
        conn.close()


def test_sticker_is_blocked_without_verified_sender_and_commercial_context():
    from core.sticker import decide_sticker
    base = {
        'channel': 'whatsapp', 'intent': 'celebration', 'relationship': 'friend',
        'context_confidence': 0.95, 'matching_sticker_available': True,
        'sticker_sent_recently': False, 'sticker_tags': ['celebration'],
    }
    assert decide_sticker({**base, 'sticker_send_capability_verified': False})['decision'] == 'TEXT_ONLY'
    assert decide_sticker({**base, 'sticker_send_capability_verified': True, 'intent': 'payment'})['decision'] == 'TEXT_ONLY'
    assert decide_sticker({**base, 'sticker_send_capability_verified': True})['decision'] == 'STICKER_MAY_FIT'


def test_whatsapp_numeric_limits_are_not_duplicated_in_legacy_policies():
    runtime = json.loads((ROOT / 'config/runtime.json').read_text(encoding='utf-8'))
    autonomy = json.loads((ROOT / 'config/autonomy.json').read_text(encoding='utf-8'))
    assert 'max_whatsapp_bubbles_default' not in runtime
    assert 'max_whatsapp_bubbles_without_special_reason' not in runtime
    assert autonomy['communication_policy']['whatsapp']['policy'] == 'config/communication.json'


def test_market_evidence_writer_rejects_unreferenced_claims():
    conn = sqlite3.connect(':memory:')
    try:
        with pytest.raises(ValueError, match='research_cycle_requires_source_urls'):
            record_event(conn, {
                'niche_id': 'python_workflow_automation', 'event_type': 'research_cycle',
                'external_ref': 'test:research-without-source',
                'evidence': {'reason': 'I searched and found demand', 'source_count': 4},
            })
        with pytest.raises(ValueError, match='qualified_lead_missing_evidence'):
            record_event(conn, {
                'niche_id': 'python_workflow_automation', 'event_type': 'qualified_lead',
                'external_ref': 'test:lead-without-source',
                'evidence': {'reason': 'seems like a lead'},
            })
    finally:
        conn.close()


def test_foundations_are_referenced_without_loading_the_full_research_file():
    principles = (ROOT / 'docs/foundations.md').read_text(encoding='utf-8')
    context = json.loads((ROOT / 'memory/cache.json').read_text(encoding='utf-8'))
    assert 'Jobs to Be Done' in principles
    assert 'Retrieval-augmented generation' in principles
    assert 'source IDs' in principles
    assert context.get('foundation_reference') == 'docs/foundations.md'
    assert 'docs/foundations.md' not in context.get('sources', {})
    assert 'on-demand source' in principles
