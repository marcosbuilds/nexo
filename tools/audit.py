#!/usr/bin/env python3
"""Static audit for the autonomy layer.

Checks for hardcoded legacy business terms and hardcoded personal identifiers in active files.
This is a guardrail, not an identity detector.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIRS = [ROOT / "agents", ROOT / "adapters", ROOT / "core", ROOT / "config", ROOT / "memory", ROOT / "tools", ROOT / "workspace"]
LEGACY = ["5SIM", "SMS Atlas", "SMS_ATLAS", "saldo_5sim", "precos_cliente", "precos_interna", "precificar.py", "Kwai"]
PERSONAL_PATTERNS = [
    re.compile(r"(?i)\b(?:senha|password|token|secret|otp)\s*[=:]\s*['\"]"),
    re.compile(r"(?i)\b(?:telefone|phone|email)\s*[=:]\s*['\"][^'\"]+['\"]"),
]

errors = []
for base in ACTIVE_DIRS:
    if not base.exists():
        continue
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".py", ".json", ".md", ".txt", ".yaml", ".yml", ".sql"}:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.name in {"owner.json", "cache.json"}:
            # Local runtime data is intentionally outside the release surface.
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for term in LEGACY:
            if term.lower() in text.lower():
                errors.append(f"LEGACY reference: {path.relative_to(ROOT)} -> {term}")
        for p in PERSONAL_PATTERNS:
            if p.search(text):
                errors.append(f"POSSIBLE hardcoded personal secret/contact: {path.relative_to(ROOT)} -> {p.pattern}")

if errors:
    print("ACTIVE RUNTIME AUDIT: FAIL")
    print("\n".join(errors))
    raise SystemExit(1)
print("ACTIVE RUNTIME AUDIT: PASS")
