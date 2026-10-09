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
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do",
    "for", "from", "has", "in", "is", "it", "of", "on", "or", "the",
    "this", "to", "was", "with", "without", "did", "does", "no", "not",
}


def _match_query(query: str) -> str:
    tokens = _query_tokens(query)
    if not tokens:
        raise ValueError("query must contain at least one searchable token")
    return " OR ".join('"' + token.replace('"', '""') + '"' for token in tokens[:24])


def _query_tokens(query: str) -> list[str]:
    return list(dict.fromkeys(
        token.lower()
        for token in TOKEN.findall(query)
        if len(token) > 1 and token.lower() not in STOPWORDS
    ))


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN.findall(text)
        if len(token) > 1 and token.lower() not in STOPWORDS
    }


def _retrieval_score(record: dict[str, Any], query_tokens: set[str], rank: float) -> tuple[float, list[str]]:
    searchable = " ".join(
        str(record.get(key, "")) if not isinstance(record.get(key), list)
        else " ".join(str(item) for item in record.get(key, []))
        for key in ("id", "domain", "summary", "when", "must", "must_not", "procedure", "failure", "correction", "tags")
    )
    matched = sorted(query_tokens & _tokens(searchable))
    coverage = len(matched) / max(1, len(query_tokens))
    priority = max(0, min(100, int(record.get("priority", 0) or 0))) / 100
    # FTS supplies recall; this small deterministic vector overlap supplies
    # precision without shipping an embedding model or adding network calls.
    score = (coverage * 0.68) + (priority * 0.22) + (1 / (1 + max(0.0, rank)) * 0.10)
    return round(score, 6), matched


def _ensure(path: Path) -> None:
    if not path.exists():
        build(str(path))


def retrieve(query: str, *, limit: int = 5, kind: str | None = None, domain: str | None = None, output: str | None = None, context_chars: int = 4000) -> dict[str, Any]:
    path = database_path(output)
    _ensure(path)
    query_tokens = set(_query_tokens(query))
    if not query_tokens:
        raise ValueError("query must contain at least one searchable token")
    clauses = ["records MATCH ?"]
    values: list[Any] = [_match_query(query)]
    if kind:
        clauses.append("kind = ?")
        values.append(kind)
    if domain:
        clauses.append("domain = ?")
        values.append(domain)
    # Retrieve a wider candidate set, then rerank with structured token
    # overlap and priority.  This avoids letting a common token dominate the
    # final packet while keeping the index itself small and dependency-free.
    values.append(max(20, min(max(1, limit) * 8, 100)))
    sql = (
        "SELECT id,kind,domain,priority,payload,bm25(records,0,0,0,0,5.0,0) AS rank "
        "FROM records WHERE " + " AND ".join(clauses) + " "
        "ORDER BY rank ASC, CAST(priority AS INTEGER) DESC LIMIT ?"
    )
    with sqlite3.connect(path) as db:
        rows = db.execute(sql, values).fetchall()
    ranked: list[tuple[float, dict[str, Any], list[str]]] = []
    for row in rows:
        record = json.loads(row[4])
        score, matched = _retrieval_score(record, query_tokens, float(row[5] or 0))
        record["_retrieval"] = {"score": score, "matched_terms": matched}
        ranked.append((score, record, matched))
    ranked.sort(key=lambda item: (item[0], int(item[1].get("priority", 0) or 0)), reverse=True)
    strong = [item for item in ranked if len(item[2]) >= max(1, (len(query_tokens) + 2) // 3)]
    if strong:
        ranked = strong
    records: list[dict[str, Any]] = []
    context_lines: list[str] = []
    budget = max(500, int(context_chars))
    for _, record, _ in ranked[:max(1, min(limit, 20))]:
        lines = [f"[{record['id']}] {record['summary']}"]
        for key in ("must", "must_not", "procedure", "correction"):
            values_for_key = record.get(key)
            if values_for_key:
                label = key.replace("_", " ")
                rendered = "; ".join(values_for_key) if isinstance(values_for_key, list) else str(values_for_key)
                lines.append(f"{label}: {rendered}")
        lines.append("sources: " + ", ".join(record.get("source_ids", [])))
        addition = "\n".join(lines)
        if context_lines and sum(len(item) + 1 for item in context_lines) + len(addition) > budget:
            break
        records.append(record)
        context_lines.append(f"[{record['id']}] {record['summary']}")
        context_lines.extend(lines[1:])
    return {
        "query": query,
        "count": len(records),
        "candidate_count": len(ranked),
        "retrieval": "fts5_recall_plus_deterministic_token_vector_rerank",
        "context_chars": len("\n".join(context_lines)),
        "results": records,
        "context": "\n".join(context_lines),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Retrieve relevant operational knowledge")
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--kind", choices=["rule", "lesson", "method"])
    ap.add_argument("--domain")
    ap.add_argument("--context-chars", type=int, default=4000)
    ap.add_argument("--output")
    args = ap.parse_args()
    print(json.dumps(retrieve(args.query, limit=args.limit, kind=args.kind, domain=args.domain, output=args.output, context_chars=args.context_chars), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
