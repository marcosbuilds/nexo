"""Conversation behavior: plan first, wording second, silence is valid."""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from core.limits import whatsapp_limits
from core.message import package_message

STAGES = ["new", "discovering", "qualified", "solution_fit", "price", "negotiating", "accepted", "delivery", "aftercare", "relationship", "paused", "closed"]
ARTIFICIAL_ACK = re.compile(r"^(?:thanks? (?:for the )?(?:audio|text|message)|understood|got it|great|perfect|sure|absolutely|entendi|ótimo|perfeito|claro|com certeza)(?:[.!?,]|\s|$)", re.I)
CORPORATE_PHRASES = {"personalized solution", "strategic solution", "tailored experience", "i would like to present", "at your disposal", "incredible opportunity", "personalized service", "in this regard"}


@dataclass
class ConversationPlan:
    response_needed: bool
    reason: str
    relationship: str
    stage: str
    goal: str | None = None
    customer_problem: str | None = None
    known_facts: list[str] = field(default_factory=list)
    unknown_that_matters: list[str] = field(default_factory=list)
    desired_next_state: str | None = None
    action: str = "NO_RESPONSE"
    message_strategy: str | None = None
    followup_reason: str | None = None
    stop_condition: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def triage(context: dict[str, Any]) -> ConversationPlan:
    incoming = str(context.get("incoming_text") or "").strip()
    relationship = str(context.get("relationship") or "unknown")
    stage = str(context.get("stage") or "new")
    silence_days = float(context.get("silence_days", 0) or 0)
    explicit_question = bool(context.get("explicit_question"))
    customer_intent = str(context.get("customer_intent") or "").strip()
    active_commitment = str(context.get("active_commitment") or "").strip()
    already_answered = bool(context.get("already_answered_latest", False))
    should_be_quiet = bool(context.get("should_be_quiet", False))
    if should_be_quiet:
        return ConversationPlan(False, "quietness_policy", relationship, stage, stop_condition="continue_only_on_meaningful_event")
    if already_answered and not active_commitment and not explicit_question:
        return ConversationPlan(False, "latest_message_already_resolved", relationship, stage, stop_condition="wait_for_new_signal")
    if not incoming and not active_commitment:
        return ConversationPlan(False, "nothing_requires_a_new_message", relationship, stage, stop_condition="wait_for_event")
    if active_commitment:
        return ConversationPlan(True, "active_commitment_needs_progress", relationship, stage, goal="fulfill_or_update_the_current_commitment", customer_problem=customer_intent or None, desired_next_state="commitment_advanced", action="ADVANCE_COMMITMENT", message_strategy="address only what advances the commitment", stop_condition="stop after the smallest useful next step")
    if explicit_question or "?" in incoming:
        return ConversationPlan(True, "customer_question", relationship, stage, goal="answer_the_actual_question", customer_problem=customer_intent or incoming, desired_next_state="question_resolved", action="ANSWER_DIRECTLY", message_strategy="answer specifically without unrelated selling", stop_condition="stop when the question is resolved")
    if customer_intent:
        return ConversationPlan(True, "customer_need_detected", relationship, stage, goal="connect_capability_to_the_customers_goal", customer_problem=customer_intent, desired_next_state="need_clarified_or_helpful_route_selected", action="CONNECT_TO_NEED", message_strategy="start from the need, not the service catalogue", stop_condition="stop when no useful next advance exists")
    if silence_days >= 7:
        return ConversationPlan(False, "silence_not_a_problem", relationship, stage, stop_condition="do_not_reanimate_without_new_reason")
    return ConversationPlan(True, "meaningful_social_or_contextual_response", relationship, stage, goal="maintain_the_relationship_when_content_deserves_a_reply", desired_next_state="relationship_continues_naturally", action="RESPOND_NATURALLY", message_strategy="reply proportionally to the received tone", stop_condition="do not manufacture a topic")


def should_be_multibubble(text: str, *, channel: str = "whatsapp") -> bool:
    if channel != "whatsapp":
        return False
    limits = whatsapp_limits()
    sentences = len(re.split(r"(?<=[.!?])\s+", text.strip()))
    return len(text.strip()) > limits["max_chars"] or (len(text.strip()) > limits["max_chars"] // 2 and sentences >= 3)


def score_draft(text: str) -> dict[str, Any]:
    lower = text.lower().strip()
    problems: list[str] = []
    if not text.strip():
        problems.append("empty")
    if ARTIFICIAL_ACK.search(lower):
        problems.append("stock_acknowledgement")
    corporate = [phrase for phrase in CORPORATE_PHRASES if phrase in lower]
    if corporate:
        problems.append("corporate_residue")
    sentences = [item for item in re.split(r"(?<=[.!?])\s+", text.strip()) if item]
    if len(text) > 900:
        problems.append("too_long_for_chat")
    if len(sentences) > 8:
        problems.append("too_many_sentences")
    if text.count("?") >= 4:
        problems.append("question_stack")
    if re.search(r"\b(great|perfect|excellent|wonderful)\b", lower) and len(sentences) <= 2:
        problems.append("generic_praise")
    return {"passes": not problems, "problems": problems, "sentence_count": len(sentences), "chars": len(text)}


def naturalize_structure(text: str, max_bubbles: int | None = None, max_chars: int | None = None) -> list[str]:
    return package_message(text, max_bubbles=max_bubbles, max_chars=max_chars)["bubbles"]


def message_beats(context: dict[str, Any]) -> list[dict[str, Any]]:
    stage = str(context.get("stage") or "new")
    has_name = bool(context.get("customer_name"))
    intent = str(context.get("customer_intent") or "").strip()
    if stage == "new":
        beats = [{"purpose": "greeting", "rule": "greet proportionally to time and relationship"}]
        beats.append({"purpose": "relevance" if intent else "open_conversation", "rule": "show a concrete reason or ask one simple natural question"})
        if has_name:
            beats[0]["use_name"] = True
        return beats
    if stage in {"discovering", "qualified"}:
        return [{"purpose": "understand_need", "rule": "ask one question that reduces real uncertainty"}, {"purpose": "helpful_route", "rule": "connect capability to the customers problem"}]
    if stage in {"price", "negotiating"}:
        return [{"purpose": "resolve_current_objection_or_question", "rule": "answer the current point exactly"}, {"purpose": "small_next_step", "rule": "offer one low-friction next step"}]
    if stage in {"relationship", "aftercare"}:
        return [{"purpose": "relationship", "rule": "respond to what exists without manufacturing a commercial topic"}]
    return [{"purpose": "advance_current_state", "rule": "act only on the next useful state"}]
