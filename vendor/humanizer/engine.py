#!/usr/bin/env python3
"""Runtime-only wording checks."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config" / "humanizer.json"

SEMANTIC_RESIDUE = [
    r"^obrigad[oa] (?:pelo|pela) (?:áudio|audio|texto|mensagem)", r"^entendi(?:\b|[.!])",
    r"^ótimo(?:\b|[.!])", r"^perfeito(?:\b|[.!])", r"^claro(?:\b|[.!])",
    r"^com certeza(?:\b|[.!])", r"^fico à disposição(?:\b|[.!])",
]
CORPORATE = {"solução personalizada", "solução estratégica", "experiência personalizada", "gostaria de apresentar", "estou à disposição", "fico à disposição", "nesse sentido", "oportunidade incrível", "atendimento personalizado"}


def _config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    return config if config is not None else json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))


def analyze(text: str, recent_openings: list[str] | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = _config(config)
    recent_openings = recent_openings or []
    lower = text.lower().strip()
    issues: list[str] = []
    hints: list[str] = []
    if any(re.match(pattern, lower, re.I) for pattern in SEMANTIC_RESIDUE):
        issues.append("stock_acknowledgment_opener"); hints.append("remove automatic acknowledgement when it carries no content")
    corporate = set(cfg.get("corporate_phrases", [])) | CORPORATE
    if any(phrase in lower for phrase in corporate):
        issues.append("corporate_or_marketing_phrase"); hints.append("replace institutional wording with a concrete case detail")
    if any(phrase in lower for phrase in cfg.get("chatbot_residue", [])):
        issues.append("chatbot_residue"); hints.append("remove automatic assistant closing")
    if text.count(":") > max(1, round(len(text) / 250)):
        issues.append("excessive_colons"); hints.append("use natural punctuation in ordinary conversation")
    sentences = [item for item in re.split(r"(?<=[.!?])\s+", text.strip()) if item]
    if len(sentences) > 8 and len(text) < 900:
        issues.append("overexplaining"); hints.append("keep only what changes the next step")
    if len(text) > 1100:
        issues.append("chat_too_long"); hints.append("split the reasoning before sending")
    if text.count("?") >= 4:
        issues.append("question_stacking"); hints.append("ask one primary question at a time")
    if re.search(r"!!+|\?{3,}", text):
        issues.append("excessive_punctuation"); hints.append("reduce emphasis punctuation")
    if recent_openings:
        first = re.sub(r"^[\"' ]+", "", lower.split(".")[0]).strip()[:60]
        if any(first == str(item).lower() for item in recent_openings[-3:]):
            issues.append("repeated_opening"); hints.append("do not reuse the same opening automatically")
    if sum(bool(re.search(pattern, lower, re.I)) for pattern in SEMANTIC_RESIDUE) >= 2:
        issues.append("stacked_acknowledgements"); hints.append("remove confirmations that do not move the conversation")
    return {"passes": not issues, "issue_count": len(issues), "issues": issues, "hints": hints, "metrics": {"chars": len(text), "sentences": len(sentences), "questions": text.count("?")}}
