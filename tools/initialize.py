#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from db import database_path  # noqa: E402

schema=(ROOT/"data"/"schema.sql").read_text(encoding="utf-8")
db=database_path()
db.parent.mkdir(parents=True, exist_ok=True)

# Never delete, truncate or replace an existing runtime database. CREATE IF NOT EXISTS
# in the schema makes this initializer additive and safe during package replacement.
import sqlite3
with sqlite3.connect(db) as conn:
    conn.executescript(schema)
print(f"Initialized {db}")
