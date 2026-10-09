import json
import sqlite3
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from index import build  # noqa: E402
from retrieve import retrieve  # noqa: E402
from package import build_bundle  # noqa: E402
from vendor.humanizer import rewrite_brief, validate_rewrite  # noqa: E402


def test_knowledge_records_are_structured_and_source_backed():
    schema = json.loads((ROOT / "knowledge/schema.json").read_text(encoding="utf-8"))
    sources = json.loads((ROOT / "knowledge/sources.json").read_text(encoding="utf-8"))
    source_ids = {item["id"] for item in sources["sources"]}
    assert schema["$schema"].endswith("2020-12/schema")
    for path in (ROOT / "knowledge").glob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            assert {"id", "kind", "domain", "priority", "summary", "when", "source_ids"} <= set(record)
            assert set(record["source_ids"]) <= source_ids


def test_fts5_retrieval_returns_relevant_lesson_and_compact_context(tmp_path):
    db = tmp_path / "knowledge.sqlite3"
    result = build(str(db))
    assert result["records"] >= 30
    found = retrieve("customer did not reply repeated followup", limit=5, output=str(db))
    ids = {item["id"] for item in found["results"]}
    assert "lesson.followup.no_signal" in ids
    assert "sources:" in found["context"]
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT count(*) FROM records").fetchone()[0] == result["records"]


def test_humanizer_surface_contains_runtime_only_files():
    allowed = {"__init__.py", "engine.py", "LICENSE", "contract.json"}
    files = {path.name for path in (ROOT / "vendor/humanizer").iterdir() if path.is_file()}
    assert files == allowed
    assert not any(path.name in {"README.md", "SKILL.md", "CHANGELOG.md", "AGENTS.md"} for path in (ROOT / "vendor/humanizer").rglob("*"))


def test_runtime_bundle_is_external_release_material_only(tmp_path):
    bundle = build_bundle(str(tmp_path / "worker-test.zip"))
    with zipfile.ZipFile(bundle) as archive:
        names = set(archive.namelist())
        assert "docs/core.md" in names
        assert "knowledge/rules.jsonl" in names
        assert not any(name.startswith(prefix) for prefix in ("tests/", "reports/", "memory/", "release/", "docs/reference/") for name in names)
        content = b"\n".join(archive.read(name) for name in names if not name.endswith(".pyc"))
        assert b"Nexo" not in content
        assert b"Autonomia" not in content
        assert b"D:\\Project" not in content


def test_humanizer_preserves_protected_spans_and_supports_practical_modes():
    brief = rewrite_brief("Send https://example.org/report by 2026-10-09.", mode="pasted", channel="chat")
    assert brief["mode"] == "pasted"
    assert "https://example.org/report" in brief["protected_spans"]
    checked = validate_rewrite(brief["input"], "Send https://example.org/report by 2026-10-09.")
    assert checked["passes"] is True
