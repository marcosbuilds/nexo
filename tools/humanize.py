#!/usr/bin/env python3
"""Command-line access to the runtime Humanizer contract."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from vendor.humanizer import analyze, humanize_file, rewrite_brief, validate_rewrite  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze text or produce a fact-preserving humanization brief")
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--file")
    ap.add_argument("--mode", choices=["pasted", "file", "embedded"], default="pasted")
    ap.add_argument("--channel", default="general")
    ap.add_argument("--voice")
    ap.add_argument("--goal")
    ap.add_argument("--rewritten")
    args = ap.parse_args()
    if args.file:
        result = humanize_file(args.file, mode="file")
        original = result["input"]
    else:
        original = args.text or ""
        result = rewrite_brief(original, mode=args.mode, channel=args.channel, voice=args.voice, goal=args.goal)
    if args.rewritten is not None:
        result["validation"] = validate_rewrite(original, args.rewritten)
    else:
        result["analysis"] = analyze(original)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
