"""WhatsApp message packaging with explicit limits and no silent wall-of-text fallback."""
from __future__ import annotations
import re
from typing import Any
from core.limits import whatsapp_limits

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in _SENTENCE_SPLIT.split(text.strip()) if part.strip()]


def _word_wrap(text: str, max_chars: int) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def package_message(text: str, *, max_bubbles: int | None = None, max_chars: int | None = None) -> dict[str, Any]:
    """Prepare semantic bubbles. If limits cannot be met, require regeneration.

    The function intentionally returns an invalid package rather than merging
    excess content into one enormous final bubble. The send gate must regenerate
    the draft before any side effect when ``fits_limits`` is false.
    """
    limits = whatsapp_limits()
    max_bubbles = limits["max_bubbles"] if max_bubbles is None else int(max_bubbles)
    max_chars = limits["max_chars"] if max_chars is None else int(max_chars)
    if max_bubbles < 1 or max_chars < 50:
        raise ValueError("invalid_message_packaging_limits")
    normalized = (text or "").replace("\r\n", "\n").strip()
    if not normalized:
        return {"bubbles": [], "count": 0, "fits_limits": False, "reason": "empty_message", "forced_word_splits": 0}

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", normalized) if p.strip()]
    units: list[str] = []
    forced_word_splits = 0
    for paragraph in paragraphs:
        sentences = _sentences(paragraph)
        # Short paragraphs can remain one bubble. Long or multi-sentence blocks
        # are separated by thought, never by a random character cut.
        if len(paragraph) <= max_chars and len(sentences) <= 2:
            units.append(paragraph)
            continue
        for sentence in sentences or [paragraph]:
            if len(sentence) <= max_chars:
                units.append(sentence)
            else:
                # Word wrapping is only a recovery artifact. It is not considered
                # a sendable natural draft, because sentence fragments feel bad.
                wrapped = _word_wrap(sentence, max_chars)
                units.extend(wrapped)
                forced_word_splits += 1

    # Combine only adjacent semantic units when they remain inside the soft cap.
    bubbles: list[str] = []
    for unit in units:
        if bubbles and len(bubbles[-1]) + 1 + len(unit) <= max_chars:
            bubbles[-1] = f"{bubbles[-1]} {unit}".strip()
        else:
            bubbles.append(unit)

    bubbles = [bubble.strip() for bubble in bubbles if bubble.strip()]
    overflow = len(bubbles) > max_bubbles
    overlong = any(len(bubble) > max_chars for bubble in bubbles)
    forced = forced_word_splits > 0
    fits = bool(bubbles) and not overflow and not overlong and not forced
    reasons = []
    if overflow:
        reasons.append("too_many_semantic_bubbles")
    if overlong:
        reasons.append("bubble_exceeds_soft_character_limit")
    if forced:
        reasons.append("sentence_required_word_wrapping")
    return {
        "bubbles": bubbles,
        "count": len(bubbles),
        "max_chars": max((len(b) for b in bubbles), default=0),
        "fits_limits": fits,
        "reason": ",".join(reasons) if reasons else "ok",
        "forced_word_splits": forced_word_splits,
        "limits": {"max_bubbles": max_bubbles, "max_chars_per_bubble": max_chars},
    }
