"""Conservative policy for deciding whether a WhatsApp sticker adds social value."""
from __future__ import annotations
from typing import Any

POSITIVE_INTENTS = {"playful_banter", "celebration", "congratulations", "casual_thanks", "friendly_acknowledgement"}
SENSITIVE_OR_COMMERCIAL_INTENTS = {
    "first_contact", "cold_outreach", "complaint", "conflict", "apology", "grief",
    "health", "urgent", "payment", "price_negotiation", "refund", "rejection",
    "legal", "security", "customer_support_problem",
}
FAMILIAR_RELATIONSHIPS = {"friend", "family", "close_contact", "established_customer"}


def decide_sticker(context: dict[str, Any] | None) -> dict[str, Any]:
    c = context or {}
    if str(c.get("channel") or "whatsapp").lower() != "whatsapp":
        return {"decision": "TEXT_ONLY", "reason": "sticker_policy_is_whatsapp_specific"}
    intent = str(c.get("intent") or "").strip().lower()
    relationship = str(c.get("relationship") or "unknown").strip().lower()
    if intent in SENSITIVE_OR_COMMERCIAL_INTENTS:
        return {"decision": "TEXT_ONLY", "reason": "context_is_sensitive_or_commercial"}
    if intent not in POSITIVE_INTENTS:
        return {"decision": "TEXT_ONLY", "reason": "no_clear_social_intent_for_sticker"}
    if relationship not in FAMILIAR_RELATIONSHIPS:
        return {"decision": "TEXT_ONLY", "reason": "relationship_not_familiar_enough"}
    if relationship == "established_customer" and not bool(c.get("customer_used_sticker_or_playful_tone")):
        return {"decision": "TEXT_ONLY", "reason": "do_not_inject_uninvited_playfulness_into_customer_chat"}
    if float(c.get("context_confidence", 0) or 0) < 0.8:
        return {"decision": "TEXT_ONLY", "reason": "context_confidence_below_threshold"}
    if not bool(c.get("matching_sticker_available")):
        return {"decision": "TEXT_ONLY", "reason": "no_relevant_existing_sticker"}
    if bool(c.get("sticker_sent_recently")):
        return {"decision": "TEXT_ONLY", "reason": "avoid_sticker_repetition"}
    if not bool(c.get("sticker_send_capability_verified")):
        return {"decision": "TEXT_ONLY", "reason": "outbound_sticker_capability_not_verified"}
    tags = c.get("sticker_tags") or []
    if not isinstance(tags, list) or not tags:
        return {"decision": "TEXT_ONLY", "reason": "sticker_intent_match_not_verified"}
    return {
        "decision": "STICKER_MAY_FIT",
        "reason": "familiar_low-risk_context_and_matching_existing_sticker",
        "required_conditions": ["sticker_tags_match_intent", "do_not_replace_necessary_text", "send_at_most_one"],
    }
