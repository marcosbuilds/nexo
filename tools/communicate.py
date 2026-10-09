#!/usr/bin/env python3
"""Final send gate with upstream behavioral planning and semantic naturalness QA."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from core.conversation import triage, score_draft
from core.message import package_message
from core.sticker import decide_sticker
from humanize import analyze

_COMMUNICATION_POLICY = json.loads((ROOT / "config" / "communication.json").read_text(encoding="utf-8"))
_WA_LIMITS = _COMMUNICATION_POLICY["message_packaging"]["channel_defaults"]["whatsapp"]

def decide(d:dict)->dict:
    has_context=any(k in d for k in ('incoming_text','history','relationship','customer_intent','stage','active_commitment'))
    plan=triage(d) if has_context else None
    response_needed=plan.response_needed if plan else bool(d.get('response_needed'))
    if not response_needed:
        return {'decision':'NO_SEND','reason':(plan.reason if plan else d.get('triage_reason')) or 'response_is_not_needed','plan':plan.to_dict() if plan else None,'next_action':'wait_for_meaningful_event'}
    draft=str(d.get('draft') or '').strip()
    if not draft:
        return {'decision':'REPLAN','reason':'response_needed_but_no_draft_exists','plan':plan.to_dict() if plan else None,'next_action':'draft_from_conversation_plan'}
    semantic=score_draft(draft); lexical=analyze(draft,d.get('recent_openings') or [])
    if not semantic['passes'] or not lexical['passes']:
        return {'decision':'REGENERATE','reason':'behavioral_or_naturalness_guard_failed','issues':sorted(set(semantic['problems']+lexical['issues'])),'hints':lexical['hints']+['regenerate from conversation purpose, not by synonym replacement'],'plan':plan.to_dict() if plan else None,'next_action':'regenerate_from_plan_then_recheck'}
    channel=str(d.get('channel') or 'whatsapp').lower()
    if channel == 'whatsapp':
        max_bubbles = min(
            int(_WA_LIMITS.get("max_bubbles_without_special_reason", 3)),
            max(1, int(d.get("max_bubbles", _WA_LIMITS.get("max_bubbles_without_special_reason", 3)))),
        )
        max_chars = min(
            int(_WA_LIMITS.get("max_chars_hard_limit", 260)),
            max(120, int(d.get("max_chars_per_bubble", _WA_LIMITS.get("max_chars_per_bubble", 260)))),
        )
        package = package_message(draft, max_bubbles=max_bubbles, max_chars=max_chars)
        if not package['fits_limits']:
            return {
                'decision':'REGENERATE',
                'reason':'whatsapp_packaging_limits_exceeded',
                'issues':[x for x in package['reason'].split(',') if x] or ['invalid_message_package'],
                'package_preview':package,
                'hints':['rewrite the draft to fit 1-3 coherent bubbles','keep each bubble under the single configured character limit','do not cram excess content into the final bubble','preserve only information needed for the current conversational goal'],
                'plan':plan.to_dict() if plan else None,
                'next_action':'rewrite_shorter_from_conversation_plan_then_recheck',
            }
        bubbles=package['bubbles']
    else:
        bubbles=[draft]
        package={'fits_limits':True,'count':1,'max_chars':len(draft),'reason':'non_whatsapp_channel'}
    sticker_context=d.get('sticker_context')
    sticker_guidance=decide_sticker(sticker_context) if isinstance(sticker_context,dict) else {'decision':'TEXT_ONLY','reason':'no_sticker_context_provided'}
    return {'decision':'SEND','channel':channel,'bubbles':bubbles,'count':len(bubbles),'package':package,'sticker_guidance':sticker_guidance,'goal':(plan.goal if plan else d.get('conversation_goal')),'next_customer_state':(plan.desired_next_state if plan else d.get('desired_next_customer_state')),'plan':plan.to_dict() if plan else None,'humanizer':'passed'}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True); print(json.dumps(decide(json.loads(ap.parse_args().json)),ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
