#!/usr/bin/env python3
"""Deterministic authorization gate.

A covered action does not need a fresh owner confirmation. Authorization is
scoped, evidence-backed and subordinate to security/legal/risk boundaries.
"""
from __future__ import annotations
import argparse, json

DEFAULT_MANDATE = {
    'normal_communication': True,
    'send_messages_on_authorized_channels': True,
    'create_payment_links_on_verified_provider': True,
    'send_verified_pix_destination_when_customer_requests_payment': True,
    'consult_authorized_calendar': True,
    'create_internal_reminder': True,
    'create_calendar_events_when_calendar_write_permission_exists': True,
    'schedule_followups': True,
    'check_payment_receipts': True,
    'run_low_risk_probes': True,
    'retry_transient_failures': True,
    'switch_to_registered_fallbacks': True,
    'continue_independent_work_while_blocked': True,
    'start_or_continue_dm': True,
    'delete_conversation': True,
    'archive_conversation': True,
    'edit_conversation': True,
    'close_conversation': True,
    'read_authorized_web_pages': True,
    'login_existing_authorized_account': True,
    'create_account_when_data_and_platform_allow': True,
    'download_and_process_media': True,
}

HIGH_RISK = {'high','critical'}
APPROVAL_ONLY = {
    'identity_verification','legal_documents_or_binding_legal_acceptance',
    'irreversible_high_risk_action','financial_spend_above_configured_limit',
    'financial_transfer_out','credential_creation_or_password_change_when_platform_requires_owner',
    'security_incident','material_missing_fact_not_discoverable','platform_manual_intervention_required'
}

def decide(d: dict) -> dict:
    capability = d.get('capability','')
    risk = d.get('risk_level','low')
    mandate = dict(DEFAULT_MANDATE); mandate.update(d.get('mandate') or {})
    explicit_block = bool(d.get('explicit_revocation'))
    platform_allowed = d.get('platform_allowed', True)
    verified_resource = bool(d.get('verified_resource'))
    account_permission = bool(d.get('account_permission') or d.get('connected_account'))
    customer_requested = bool(d.get('customer_requested'))
    financial = bool(d.get('financial_action'))

    if explicit_block:
        return {'decision':'BLOCK','reason':'explicit_revocation'}
    if not platform_allowed:
        return {'decision':'BLOCK','reason':'platform_or_policy_denied'}
    if capability in APPROVAL_ONLY or bool(d.get('requires_human_by_policy')):
        return {'decision':'HUMAN_REQUIRED','reason':capability or 'policy_boundary'}
    if financial and risk in HIGH_RISK:
        return {'decision':'HUMAN_REQUIRED','reason':'high_risk_financial_action'}

    covered = bool(mandate.get(capability, False))
    if verified_resource and capability in {
        'send_verified_pix_destination_when_customer_requests_payment',
        'create_payment_links_on_verified_provider', 'check_payment_receipts'
    }:
        return {'decision':'ALLOW','reason':'verified_resource_plus_mandate',
                'authorization_basis':'owner_mandate + verified_resource'}
    if account_permission and capability in {
        'consult_authorized_calendar','create_calendar_events_when_calendar_write_permission_exists'
    }:
        return {'decision':'ALLOW','reason':'connected_account_permission_plus_mandate',
                'authorization_basis':'owner_mandate + account_permission'}
    if covered or account_permission or verified_resource:
        basis = 'owner_mandate'
        if account_permission:
            basis += ' + connected_account_permission'
        if verified_resource:
            basis += ' + verified_resource'
        return {'decision':'ALLOW','reason':'routine_action_is_within_existing_operational_scope',
                'authorization_basis':basis}
    if customer_requested and capability in {'send_messages_on_authorized_channels','schedule_followups'} and (mandate.get(capability,False) or account_permission):
        return {'decision':'ALLOW','reason':'customer_request_within_mandate',
                'authorization_basis':'owner_mandate + customer_request'}
    return {'decision':'HUMAN_REQUIRED','reason':'capability_not_in_mandate'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True)
    print(json.dumps(decide(json.loads(ap.parse_args().json)),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
