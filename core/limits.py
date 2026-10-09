"""Shared channel limits read from the active communication policy."""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def whatsapp_limits() -> dict[str, int]:
    policy_path = ROOT / "config" / "communication.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    limits = policy["message_packaging"]["channel_defaults"]["whatsapp"]
    bubbles = int(limits["max_bubbles_without_special_reason"])
    chars = int(limits["max_chars_hard_limit"])
    if bubbles < 1 or chars < 50:
        raise ValueError("invalid_whatsapp_limits_in_communication_policy")
    return {"max_bubbles": bubbles, "max_chars": chars}
