#!/usr/bin/env python3
"""Deterministic humanization contract for pasted, file, and embedded text.

The engine is deliberately conservative: it detects drafting residue and
provides a structured rewrite brief. A language model may perform the rewrite,
but this module protects facts, technical spans, and the final send boundary.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config" / "humanizer.json"
CONTRACT = Path(__file__).with_name("contract.json")

ACKNOWLEDGEMENTS = [
    r"^(?:thanks|thank you|understood|got it|great|perfect|sure|absolutely|of course)(?:[,.!?]|\s|$)",
    r"^(?:obrigad[oa]|entendi|ótimo|perfeito|claro|com certeza)(?:[,.!?]|\s|$)",
]
CORPORATE = {
    "personalized solution", "strategic solution", "add value", "tailored experience",
    "i would like to present", "i am at your disposal", "in this regard",
    "incredible opportunity", "personalized service",
    "solução personalizada", "solução estratégica", "agregar valor",
    "experiência personalizada", "gostaria de apresentar", "estou à disposição",
    "nesse sentido", "oportunidade incrível", "atendimento personalizado",
}
CHATBOT_CLOSINGS = {
    "hope this helps", "hope that helps", "let me know if you need anything else",
    "is there anything else i can help with", "qualquer outra dúvida",
    "posso ajudar em mais alguma coisa", "espero ter ajudado",
}
PROTECTED_PATTERNS = [
    r"https?://\S+", r"www\.\S+", r"`[^`]+`", r"\b[A-Z][A-Z0-9_]{2,}\b",
    r"\b\d+(?:[.,/]\d+)*(?:%|\b)", r"\b\w[\w.+-]*@[\w.-]+\.[A-Za-z]{2,}\b",
]


def _config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    return config if config is not None else json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))


def _contract() -> dict[str, Any]:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def protected_spans(text: str) -> list[str]:
    spans: list[str] = []
    for pattern in PROTECTED_PATTERNS:
        spans.extend(match.group(0) for match in re.finditer(pattern, text))
    return list(dict.fromkeys(spans))


def _sentences(text: str) -> list[str]:
    return [item for item in re.split(r"(?<=[.!?])\s+", text.strip()) if item]


def analyze(text: str, recent_openings: list[str] | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a deterministic quality report without changing the text."""
    cfg = _config(config)
    recent_openings = recent_openings or []
    lower = text.lower().strip()
    issues: list[str] = []
    hints: list[str] = []
    if not lower:
        issues.append("empty_text")
        hints.append("do not send an empty message")
    if any(re.match(pattern, lower, re.I) for pattern in ACKNOWLEDGEMENTS):
        issues.append("stock_acknowledgment_opener")
        hints.append("remove an acknowledgement when it carries no information")
    corporate = set(cfg.get("corporate_phrases", [])) | CORPORATE
    if any(phrase.lower() in lower for phrase in corporate):
        issues.append("corporate_or_marketing_phrase")
        hints.append("replace institutional wording with a concrete detail")
    chatbot = set(cfg.get("chatbot_residue", [])) | CHATBOT_CLOSINGS
    if any(phrase.lower() in lower for phrase in chatbot):
        issues.append("chatbot_residue")
        hints.append("remove an automatic closing")
    sentences = _sentences(text)
    if text.count(":") > max(1, round(len(text) / 250)):
        issues.append("excessive_colons")
        hints.append("use natural punctuation outside URLs, code, and explicit labels")
    if len(sentences) > 8 and len(text) < 900:
        issues.append("overexplaining")
        hints.append("keep only what changes the next step")
    if len(text) > 1100:
        issues.append("chat_too_long")
        hints.append("rewrite into the smallest useful channel-sized message")
    if text.count("?") >= 4:
        issues.append("question_stacking")
        hints.append("ask one primary question at a time")
    if re.search(r"!!+|\?{3,}", text):
        issues.append("excessive_punctuation")
        hints.append("reduce emphasis punctuation")
    if recent_openings:
        first = re.sub(r"^[\"' ]+", "", lower.split(".")[0]).strip()[:80]
        if any(first == str(item).lower().strip() for item in recent_openings[-3:]):
            issues.append("repeated_opening")
            hints.append("do not reuse the same opening automatically")
    return {
        "passes": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "hints": list(dict.fromkeys(hints)),
        "metrics": {"chars": len(text), "sentences": len(sentences), "questions": text.count("?"), "protected_spans": len(protected_spans(text))},
    }


def rewrite_brief(text: str, *, mode: str = "pasted", channel: str = "general", voice: str | None = None, goal: str | None = None) -> dict[str, Any]:
    """Create the practical brief used by an LLM or a human rewriter."""
    if mode not in _contract()["modes"]:
        raise ValueError(f"unsupported_mode:{mode}")
    report = analyze(text)
    return {
        "mode": mode,
        "channel": channel,
        "goal": goal or "preserve the intended meaning while making the wording natural",
        "voice": voice or "preserve the author's observable voice",
        "input": text,
        "protected_spans": protected_spans(text),
        "issues": report["issues"],
        "rewrite_instructions": _contract()["rewrite_rules"],
        "preserve": _contract()["preserve"],
        "review": _contract()["final_gate"],
    }


def validate_rewrite(original: str, rewritten: str, *, required_terms: Iterable[str] = ()) -> dict[str, Any]:
    """Check that a rewrite did not lose protected data or required terms."""
    missing = [span for span in protected_spans(original) if span not in rewritten]
    missing_terms = [term for term in required_terms if term and term not in rewritten]
    report = analyze(rewritten)
    errors = []
    if missing:
        errors.append("protected_span_lost")
    if missing_terms:
        errors.append("required_term_lost")
    if report["issues"]:
        errors.append("style_gate_failed")
    return {"passes": not errors, "errors": errors, "missing_spans": missing, "missing_terms": missing_terms, "analysis": report}


def humanize_file(path: str | Path, *, mode: str = "file", encoding: str = "utf-8") -> dict[str, Any]:
    source = Path(path)
    text = source.read_text(encoding=encoding)
    return rewrite_brief(text, mode=mode)
