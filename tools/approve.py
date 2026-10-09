#!/usr/bin/env python3
"""Hard pre-send guard for unnecessary owner approval questions.

This applies only to owner-facing messages. Customer-facing questions remain
allowed because they can be part of the actual business conversation.
"""
from __future__ import annotations

import argparse
import json
import re
from typing import Any

PATTERNS = [
    r"\bmay\s+i\s+(do|send|create|use|check|schedule|continue)\b",
    r"\bmay\s+i\s+(delete|archive|edit|close|open|start)\b",
    r"\bwould\s+you\s+like\s+me\s+to\s+\w+\b",
    r"\bmay\s+i\s+proceed\b",
    r"\bdo\s+you\s+confirm\s+that\s+i\s+can\b",
    # Keep Portuguese input recognition so an authorized user cannot bypass
    # the same anti-reflex guard by speaking another supported language.
    r"\bposso\s+(fazer|enviar|criar|mandar|usar|consultar|marcar|agendar|seguir)\b",
    r"\bposso\s+(apagar|excluir|deletar|arquivar|editar|fechar|abrir|iniciar)\b",
    r"\bquer\s+que\s+eu\s+(faça|faça|envie|crie|mande|use|consulte|marque|agende|siga)\b",
    r"\bquer\s+que\s+eu\s+(apague|exclua|delete|arquive|edite|feche|abra|inicie)\b",
    r"\bposso\s+prosseguir\b",
    r"\bautoriz(a|ação|acao)\b.*\b(fazer|enviar|criar|mandar|usar|consultar|marcar|agendar)\b",
    r"\bpreciso\s+de\s+(sua|sua\s+)?confirmação\b",
    r"\bconfirma\s+que\s+posso\b",
]

COMPILED = [re.compile(p, re.I | re.S) for p in PATTERNS]


def find_unnecessary_requests(text: str) -> list[str]:
    return [p.pattern for p in COMPILED if p.search(text or "")]


def decide(d: dict[str, Any]) -> dict[str, Any]:
    text = str(d.get("message", ""))
    owner_channel = bool(d.get("owner_channel", False))
    executable = bool(d.get("authorized_and_executable", False))
    matches = find_unnecessary_requests(text)

    if not owner_channel:
        return {"decision": "ALLOW", "reason": "not_owner_channel", "matches": matches}

    if executable and matches:
        return {
            "decision": "BLOCK",
            "reason": "owner_confirmation_request_for_executable_authorized_action",
            "matches": matches,
            "next_action": "execute_action_instead_of_sending_approval_question",
        }

    return {"decision": "ALLOW", "reason": "no_unnecessary_owner_confirmation_detected", "matches": matches}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", required=True)
    try:
        data = json.loads(p.parse_args().json)
        print(json.dumps(decide(data), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"decision": "ERROR", "reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
