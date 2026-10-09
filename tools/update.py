#!/usr/bin/env python3
"""Update replaceable runtime files while preserving local state."""
from __future__ import annotations

import argparse
import json
from install import install


def main() -> int:
    ap = argparse.ArgumentParser(description="Update runtime code and rebuild the local knowledge index")
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--target", required=True)
    args = ap.parse_args()
    print(json.dumps(install(args.bundle, args.target), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
