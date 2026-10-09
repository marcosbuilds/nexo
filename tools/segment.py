#!/usr/bin/env python3
"""Package text into semantic WhatsApp bubbles and report if it must be rewritten."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.message import package_message


def sentence_split(text: str) -> list[str]:
    import re
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]


def word_wrap(text: str, max_chars: int) -> list[str]:
    from core.message import _word_wrap
    return _word_wrap(text, max_chars)


def split_message(text: str, max_bubbles: int | None = None, max_chars: int | None = None) -> list[str]:
    return package_message(text, max_bubbles=max_bubbles, max_chars=max_chars)["bubbles"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--max-bubbles", type=int, default=None)
    parser.add_argument("--max-chars", type=int, default=None)
    args = parser.parse_args()
    if (args.max_bubbles is not None and args.max_bubbles < 1) or (args.max_chars is not None and args.max_chars < 50):
        raise SystemExit("invalid message packaging limits")
    result = package_message(args.text, max_bubbles=args.max_bubbles, max_chars=args.max_chars)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["fits_limits"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
