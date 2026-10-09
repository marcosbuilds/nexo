#!/usr/bin/env python3
"""Canonical runtime database location.

The replaceable code package never owns the operational database. All tools use
this helper so updates cannot silently fall back to a shipped database.
"""
from __future__ import annotations

import os
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "runtime_data" / "nexo.sqlite3"


def database_path() -> Path:
    raw = os.environ.get("NEXO_DB") or os.environ.get("AUTONOMIA_DB")
    path = Path(raw).expanduser() if raw else DEFAULT_DB
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def connect() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
