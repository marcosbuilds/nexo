"""Prospecting: only approach people/businesses when observable relevance exists."""
from __future__ import annotations
from typing import Any


def score_lead(lead: dict[str, Any]) -> dict[str, Any]:
    signals = lead.get('signals') or {}
    relevance = min(1,max(0,float(signals.get('problem_relevance',0))))
    evidence = min(1,max(0,float(signals.get('evidence_strength',0))))
    fit = min(1,max(0,float(signals.get('capability_fit',0))))
    access = min(1,max(0,float(signals.get('contactability',0))))
    recurrence = min(1,max(0,float(signals.get('recurrence',0))))
    risk = min(1,max(0,float(signals.get('policy_risk',0))))
    contact_permission = bool(lead.get('contact_permission_verified', signals.get('contact_permission_verified', False)))
    score=max(0,100*(0.34*relevance+0.22*evidence+0.22*fit+0.10*access+0.12*recurrence-0.35*risk))
    return {
        'score':round(score,2),'should_contact':score>=55 and relevance>=0.45 and evidence>=0.30 and risk<0.35 and contact_permission,
        'why':[
            'observable_need' if relevance>=0.45 else 'weak_need_signal',
            'real_evidence' if evidence>=0.30 else 'weak_evidence',
            'capability_fit' if fit>=0.5 else 'weak_fit',
            'low_policy_risk' if risk<0.35 else 'policy_risk',
            'contact_permission_verified' if contact_permission else 'contact_permission_missing',
        ],
        'message_angle': lead.get('message_angle') or lead.get('observable_problem') or 'start with the concrete problem observed, not a generic service pitch',
        'stop_condition':'do_not_contact_without_permission_or_public_channel' if not contact_permission or not access else 'stop after refusal, opt-out or repeated no-signal followups',
    }
