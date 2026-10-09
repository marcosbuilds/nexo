#!/usr/bin/env python3
"""Small deterministic helper for consequence tracing.

It does not browse or act on external systems. It turns an event into
candidate destination categories so the orchestrator can decide what to inspect.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "config" / "routes.json"

def load() -> dict:
    return json.loads(TEMPLATES.read_text(encoding="utf-8"))

def route(event_class: str) -> dict:
    data = load()
    for item in data.get("event_classes", []):
        if item.get("class") == event_class:
            return item
    return {"class": event_class, "signals": [], "destination_types": [], "default_probe": None}

def main() -> int:
    event_class = sys.argv[1] if len(sys.argv) > 1 else "async_external_action"
    print(json.dumps(route(event_class), ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
