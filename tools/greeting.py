#!/usr/bin/env python3
"""Return a natural greeting for the configured operating timezone."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from zoneinfo import ZoneInfo


def greeting_for(dt: datetime) -> str:
    h = dt.hour
    if 5 <= h < 12:
        return "Bom dia"
    if 12 <= h < 18:
        return "Boa tarde"
    return "Boa noite"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--timezone", default="America/Santarem")
    p.add_argument("--when", default=None, help="ISO datetime; defaults to now")
    args = p.parse_args()
    zone = ZoneInfo(args.timezone)
    dt = datetime.fromisoformat(args.when) if args.when else datetime.now(zone)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=zone)
    dt = dt.astimezone(zone)
    print(json.dumps({"timezone": args.timezone, "local_time": dt.isoformat(), "greeting": greeting_for(dt)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
