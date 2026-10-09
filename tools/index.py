#!/usr/bin/env python3
"""Build the local FTS5 knowledge index from validated JSON records."""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
DEFAULT_DB = ROOT / "runtime_data" / "knowledge.sqlite3"
TOKEN = re.compile(r"[\w][\w.-]*", re.UNICODE)


def database_path(value: str | None = None) -> Path:
    return Path(value or os.environ.get("WORKER_KNOWLEDGE_DB") or DEFAULT_DB).expanduser().resolve()


def _records() -> list[dict[str, Any]]:
    schema = json.loads((KNOWLEDGE / "schema.json").read_text(encoding="utf-8"))
    required = set(schema["required"])
    allowed = set(schema["properties"])
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(KNOWLEDGE.glob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON in {path}:{line_number}: {exc}") from exc
            missing = required - set(record)
            extra = set(record) - allowed
            if missing or extra:
                raise ValueError(f"invalid record {path}:{line_number}; missing={sorted(missing)} extra={sorted(extra)}")
            if record["id"] in seen:
                raise ValueError(f"duplicate knowledge id: {record['id']}")
            if record["kind"] not in {"rule", "lesson", "method"}:
                raise ValueError(f"invalid knowledge kind: {record['id']}")
            if not isinstance(record["priority"], int) or not 1 <= record["priority"] <= 100:
                raise ValueError(f"invalid knowledge priority: {record['id']}")
            if not isinstance(record["source_ids"], list) or not record["source_ids"]:
                raise ValueError(f"missing source ids: {record['id']}")
            seen.add(record["id"])
            result.append(record)
    if not result:
        raise ValueError("knowledge directory contains no JSONL records")
    source_data = json.loads((KNOWLEDGE / "sources.json").read_text(encoding="utf-8"))
    source_items = source_data.get("sources", [])
    if not isinstance(source_items, list) or not source_items:
        raise ValueError("sources.json must contain a non-empty sources array")
    for source in source_items:
        if not all(isinstance(source.get(key), str) and source[key] for key in ("id", "title", "url", "type")):
            raise ValueError("every source needs id, title, url, and type")
        if not source["url"].startswith(("https://", "http://")):
            raise ValueError(f"source URL is invalid: {source['id']}")
        if not isinstance(source.get("claims"), list) or not source["claims"]:
            raise ValueError(f"source has no claims: {source['id']}")
    source_ids = {item["id"] for item in source_items}
    missing_sources = sorted({sid for item in result for sid in item["source_ids"]} - source_ids)
    if missing_sources:
        raise ValueError("unknown source ids: " + ", ".join(missing_sources))
    return result


def _body(record: dict[str, Any]) -> str:
    fields = [record.get("id", ""), record.get("domain", ""), record.get("summary", "")]
    for key in ("when", "must", "must_not", "procedure", "failure", "correction", "error_class", "tags"):
        value = record.get(key)
        if isinstance(value, list):
            fields.extend(value)
        elif value:
            fields.append(str(value))
    return " ".join(str(part) for part in fields if part)


def build(output: str | None = None) -> dict[str, Any]:
    path = database_path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    records = _records()
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("DROP TABLE IF EXISTS records")
        db.execute(
            "CREATE VIRTUAL TABLE records USING fts5("
            "id UNINDEXED, kind UNINDEXED, domain UNINDEXED, priority UNINDEXED, body, payload UNINDEXED)"
        )
        for record in records:
            db.execute(
                "INSERT INTO records(id,kind,domain,priority,body,payload) VALUES(?,?,?,?,?,?)",
                (record["id"], record["kind"], record["domain"], record["priority"], _body(record), json.dumps(record, ensure_ascii=False)),
            )
        db.execute("INSERT INTO records(records) VALUES('optimize')")
        db.commit()
    return {"database": str(path), "records": len(records), "kinds": sorted({r["kind"] for r in records})}


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the local knowledge search index")
    ap.add_argument("--output")
    args = ap.parse_args()
    print(json.dumps(build(args.output), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
