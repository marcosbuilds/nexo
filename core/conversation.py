"""Conversation behavior: plan first, wording second, silence is a valid move."""
from __future__ import annotations
from dataclasses import dataclass, field
import re
from typing import Any
from core.message import package_message
from core.limits import whatsapp_limits

STAGES = [
    "new", "discovering", "qualified", "solution_fit", "price", "negotiating",
    "accepted", "delivery", "aftercare", "relationship", "paused", "closed"
]

ARTIFICIAL_ACK = re.compile(r"^(obrigad[oa] (?:pelo|pela).{0,80}(?:áudio|audio|mensagem)|entendi[.!]?$|ótimo[.!]?$|perfeito[.!]?$|claro[.!]?$)", re.I)
CORPORATE_PHRASES = {
    "solução personalizada", "solução estratégica", "experiência personalizada",
    "gostaria de apresentar", "estou à disposição", "fico à disposição",
    "oportunidade incrível", "atendimento personalizado", "nesse sentido",
}

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


def _last_meaningful_text(history: list[dict[str, Any]]) -> str:
    for msg in reversed(history):
        text = str(msg.get("text") or "").strip()
        if text:
            return text
    return ""


def triage(context: dict[str, Any]) -> ConversationPlan:
    history = context.get("history") or []
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
        return ConversationPlan(
            True, "active_commitment_needs_progress", relationship, stage,
            goal="cumprir ou atualizar o compromisso atual",
            customer_problem=customer_intent or None,
            desired_next_state="commitment_advanced",
            action="ADVANCE_COMMITMENT",
            message_strategy="responder somente o que destrava o compromisso",
            stop_condition="stop after the smallest useful next step",
        )

    if explicit_question or "?" in incoming:
        return ConversationPlan(
            True, "customer_question", relationship, stage,
            goal="responder à pergunta real",
            customer_problem=customer_intent or incoming,
            desired_next_state="question_resolved",
            action="ANSWER_DIRECTLY",
            message_strategy="resposta curta e específica; não adicionar venda sem relação",
            stop_condition="não continuar se a pergunta já estiver resolvida",
        )

    if customer_intent:
        return ConversationPlan(
            True, "customer_need_detected", relationship, stage,
            goal="entender e conectar o que a funcionária pode fazer ao objetivo do cliente",
            customer_problem=customer_intent,
            desired_next_state="need_clarified_or_helpful_route_selected",
            action="CONNECT_TO_NEED",
            message_strategy="partir da necessidade do cliente, não do catálogo da funcionária",
            stop_condition="parar a conversa comercial quando não houver próximo avanço útil",
        )

    if silence_days >= 7:
        return ConversationPlan(False, "silence_not_a_problem", relationship, stage, stop_condition="do_not_reanimate_without_new_reason")

    return ConversationPlan(
        True, "meaningful_social_or_contextual_response", relationship, stage,
        goal="manter a relação quando houver conteúdo que mereça resposta",
        desired_next_state="relationship_continues_naturally",
        action="RESPOND_NATURALLY",
        message_strategy="uma resposta humana e proporcional ao tom recebido",
        stop_condition="não criar assunto artificialmente",
    )


def should_be_multibubble(text: str, *, channel: str = "whatsapp") -> bool:
    if channel != "whatsapp":
        return False
    limits = whatsapp_limits()
    sentence_count = len(re.split(r"(?<=[.!?])\s+", text.strip()))
    return len(text.strip()) > limits["max_chars"] or (len(text.strip()) > limits["max_chars"] // 2 and sentence_count >= 3)


def score_draft(text: str) -> dict[str, Any]:
    lower = text.lower().strip()
    problems: list[str] = []
    if not text.strip():
        problems.append("empty")
    if ARTIFICIAL_ACK.search(lower) or re.match(r'^(entendi|ótimo|perfeito|claro|com certeza)[.!]?\s', lower, re.I):
        problems.append("stock_acknowledgement")
    corporate = [p for p in CORPORATE_PHRASES if p in lower]
    if corporate:
        problems.append("corporate_residue")
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
    if len(text) > 900:
        problems.append("too_long_for_chat")
    if len(sentences) > 8:
        problems.append("too_many_sentences")
    if text.count("?") >= 4:
        problems.append("question_stack")
    if re.search(r"\b(ótimo|perfeito|excelente|maravilhoso)\b", lower) and len(sentences) <= 2:
        problems.append("generic_praise")
    return {"passes": not problems, "problems": problems, "sentence_count": len(sentences), "chars": len(text)}


def naturalize_structure(text: str, max_bubbles: int | None = None, max_chars: int | None = None) -> list[str]:
    """Split by meaning without silently creating an oversized final bubble."""
    return package_message(text, max_bubbles=max_bubbles, max_chars=max_chars)["bubbles"]


def message_beats(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a few conversational beats, not a fixed sales script."""
    stage = str(context.get("stage") or "new")
    relationship = str(context.get("relationship") or "unknown")
    has_name = bool(context.get("customer_name"))
    intent = str(context.get("customer_intent") or "").strip()
    if stage == "new":
        beats = [{"purpose": "greeting", "rule": "cumprimentar de forma proporcional ao horário e à relação"}]
        if intent:
            beats.append({"purpose": "relevance", "rule": "mostrar que existe uma razão concreta para o contato"})
        else:
            beats.append({"purpose": "open_conversation", "rule": "deixar uma pergunta simples ou comentário natural, sem despejar oferta"})
        if has_name:
            beats[0]["use_name"] = True
        return beats
    if stage in {"discovering", "qualified"}:
        return [{"purpose": "understand_need", "rule": "uma pergunta que realmente reduza incerteza"}, {"purpose": "helpful_route", "rule": "conectar a capacidade ao problema do cliente"}]
    if stage in {"price", "negotiating"}:
        return [{"purpose": "resolve_current_objection_or_question", "rule": "responder exatamente ao ponto atual"}, {"purpose": "small_next_step", "rule": "um próximo passo de baixo atrito"}]
    if stage in {"relationship", "aftercare"}:
        return [{"purpose": "relationship", "rule": "responder ao que existe na conversa sem fabricar assunto comercial"}]
    return [{"purpose": "advance_current_state", "rule": "agir somente sobre o próximo estado útil"}]
