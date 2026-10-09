#!/usr/bin/env python3
"""Retrieve a compact, provenance-preserving knowledge packet."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from index import build, database_path  # noqa: E402

TOKEN = re.compile(r"[\w][\w.-]*", re.UNICODE)


def _match_query(query: str) -> str:
    tokens = [token.lower() for token in TOKEN.findall(query) if len(token) > 1]
    if not tokens:
        raise ValueError("query must contain at least one searchable token")
    return " OR ".join('"' + token.replace('"', '""') + '"' for token in tokens[:24])


def _ensure(path: Path) -> None:
    if not path.exists():
        build(str(path))


def retrieve(query: str, *, limit: int = 5, kind: str | None = None, domain: str | None = None, output: str | None = None) -> dict[str, Any]:
    path = database_path(output)
    _ensure(path)
    clauses = ["records MATCH ?"]
    values: list[Any] = [_match_query(query)]
    if kind:
        clauses.append("kind = ?")
        values.append(kind)
    if domain:
        clauses.append("domain = ?")
        values.append(domain)
    values.append(max(1, min(limit, 20)))
    sql = (
        "SELECT id,kind,domain,priority,payload,bm25(records,0,0,0,0,5.0,0) AS rank "
        "FROM records WHERE " + " AND ".join(clauses) + " "
        "ORDER BY rank ASC, CAST(priority AS INTEGER) DESC LIMIT ?"
    )
    with sqlite3.connect(path) as db:
        rows = db.execute(sql, values).fetchall()
    records = [json.loads(row[4]) for row in rows]
    context_lines: list[str] = []
    for record in records:
        context_lines.append(f"[{record['id']}] {record['summary']}")
        for key in ("must", "must_not", "procedure", "correction"):
            values_for_key = record.get(key)
            if values_for_key:
                label = key.replace("_", " ")
                rendered = "; ".join(values_for_key) if isinstance(values_for_key, list) else str(values_for_key)
                context_lines.append(f"{label}: {rendered}")
        context_lines.append("sources: " + ", ".join(record.get("source_ids", [])))
    return {"query": query, "count": len(records), "results": records, "context": "\n".join(context_lines)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Retrieve relevant operational knowledge")
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--kind", choices=["rule", "lesson", "method"])
    ap.add_argument("--domain")
    ap.add_argument("--output")
    args = ap.parse_args()
    print(json.dumps(retrieve(args.query, limit=args.limit, kind=args.kind, domain=args.domain, output=args.output), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
