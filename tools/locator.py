#!/usr/bin/env python3
"""Build deterministic direct locators without fuzzy identity matching."""
from __future__ import annotations

import argparse
import json
import re


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if not digits:
        raise ValueError("phone contains no digits")
    return digits


def locate(kind: str, value: str) -> dict:
    if kind == "phone":
        digits = normalize_phone(value)
        return {
            "kind": kind,
            "normalized": digits,
            "direct_routes": {
                "whatsapp": f"https://wa.me/{digits}"
            },
            "match_policy": "exact_identifier_only",
        }
    if kind == "url":
        return {"kind": kind, "normalized": value.strip(), "match_policy": "exact_identifier_only"}
    if kind == "email":
        return {"kind": kind, "normalized": value.strip().lower(), "match_policy": "exact_identifier_only"}
    if kind == "id":
        return {"kind": kind, "normalized": value.strip(), "match_policy": "exact_identifier_only"}
    raise ValueError(f"unsupported kind: {kind}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["phone", "url", "email", "id"])
    parser.add_argument("value")
    args = parser.parse_args()
    try:
        print(json.dumps(locate(args.kind, args.value), ensure_ascii=False, indent=2))
        return 0
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
