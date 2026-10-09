#!/usr/bin/env python3
"""Universal operation preflight.

Connected access is operational permission for routine work. Human escalation
exists only for a real boundary, not as a polite reflex before every click.
"""
from __future__ import annotations
import argparse,json,hashlib

ROUTINE_CAPABILITIES={
 'send_message':'send_messages_on_authorized_channels','follow_up':'schedule_followups',
 'calendar_read':'consult_authorized_calendar','calendar_event_create':'create_calendar_events_when_calendar_write_permission_exists',
 'internal_reminder_create':'create_internal_reminder','payment_link_create':'create_payment_links_on_verified_provider',
 'pix_send':'send_verified_pix_destination_when_customer_requests_payment','payment_check':'check_payment_receipts',
 'retry_transient':'retry_transient_failures','fallback_route':'switch_to_registered_fallbacks','capability_probe':'run_low_risk_probes',
 'social_publish':'publish_on_authorized_social_accounts','prospecting_message':'conduct_low_risk_prospecting_on_authorized_channels',
 'content_create':'create_and_distribute_authorized_content','web_research':'research_public_business_demand',
 'browser_read':'read_authorized_web_pages','account_login':'login_existing_authorized_account',
 'account_create':'create_account_when_data_and_platform_allow','extract_media':'download_and_process_media',
 'send_payment_link':'send_customer_specific_payment_link',
 'start_dm':'start_or_continue_dm','open_dm':'start_or_continue_dm',
 'continue_dm':'start_or_continue_dm','send_dm':'send_messages_on_authorized_channels',
 'delete_conversation':'delete_conversation','conversation_delete':'delete_conversation',
 'archive_conversation':'archive_conversation','conversation_archive':'archive_conversation',
 'edit_conversation':'edit_conversation','conversation_update':'edit_conversation',
 'close_conversation':'close_conversation'
}
HUMAN_BOUNDARIES={
 'identity_verification','legal_documents_or_binding_legal_acceptance','irreversible_high_risk_action',
 'financial_transfer_out','security_incident','material_missing_fact_not_discoverable','platform_manual_intervention_required'
}
HIGH_RISK={'high','critical'}
MANUAL_SIGNALS={'captcha','otp','identity','security'}

def key(d):
    raw=json.dumps({'action':d.get('action'),'scope':d.get('scope'),'payload':d.get('payload',{})},sort_keys=True,ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()

def preflight(d):
    action=d.get('action',''); cap=d.get('capability') or ROUTINE_CAPABILITIES.get(action,action); risk=d.get('risk_level','low'); mandate=d.get('mandate') or {}
    if d.get('explicit_revocation'):
        return {'decision':'BLOCK','reason':'explicit_revocation','capability':cap}
    if not d.get('platform_allowed',True):
        return {'decision':'BLOCK','reason':'platform_or_policy_denied','capability':cap}
    if d.get('manual_blocker') in MANUAL_SIGNALS or d.get('requires_manual_platform_step'):
        return {'decision':'HUMAN_REQUIRED','reason':d.get('manual_blocker') or 'platform_manual_intervention_required','capability':cap}
    if cap in HUMAN_BOUNDARIES or d.get('requires_human_by_policy'):
        return {'decision':'HUMAN_REQUIRED','reason':cap,'capability':cap}
    if d.get('financial_action') and risk in HIGH_RISK:
        return {'decision':'HUMAN_REQUIRED','reason':'high_risk_financial_action','capability':cap}
    if d.get('spend_amount') is not None and float(d.get('spend_amount') or 0) > float(d.get('auto_spend_limit',5)):
        return {'decision':'HUMAN_REQUIRED','reason':'spend_above_limit','capability':cap}
    if action in {'payment_link_create','pix_send','send_payment_link'} and not d.get('verified_resource') and not d.get('account_permission'):
        return {'decision':'HUMAN_REQUIRED','reason':'payment_resource_not_verified','capability':cap}
    if action=='calendar_event_create' and not d.get('account_permission'):
        return {'decision':'HUMAN_REQUIRED','reason':'calendar_write_permission_missing','capability':cap}
    if action=='account_create' and not d.get('owner_identity_available',False):
        return {'decision':'MATERIAL_INPUT_REQUIRED','reason':'owner_identity_required_for_account_creation','capability':cap}
    if d.get('customer_requested') and action in {'payment_link_create','pix_send','send_payment_link'} and not d.get('sale_context_known',True):
        return {'decision':'MATERIAL_INPUT_REQUIRED','reason':'sale_amount_or_context_missing','capability':cap}
    covered=bool(mandate.get(cap,True))
    connected=bool(d.get('account_permission') or d.get('connected_account') or d.get('verified_resource'))
    resource_ok=connected or action in {'web_research','browser_read','capability_probe','extract_media','retry_transient','fallback_route'}
    if covered and resource_ok:
        return {'decision':'ALLOW_EXECUTE','reason':'routine_action_already_authorized','capability':cap,
                'authorization_basis':'owner_mandate + connected_account_or_verified_resource',
                'idempotency_key':key(d),'next_action':'EXECUTE_NOW','decision_legacy':'ALLOW_EXECUTE','forbid_owner_confirmation':True}
    return {'decision':'HUMAN_REQUIRED','reason':'no_verified_resource_or_authorized_account','capability':cap}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True); print(json.dumps(preflight(json.loads(ap.parse_args().json)),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
