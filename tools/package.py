#!/usr/bin/env python3
"""Audit the public tree and build a clean runtime bundle."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_NAME = "Nexo"
RUNTIME_TOOL_EXCLUDES = {"audit.py", "legacy.py", "package.py", "install.py", "update.py"}
HUMANIZER_ALLOWED = {"__init__.py", "engine.py", "LICENSE"}
FORBIDDEN_BUNDLE_NAMES = {"README", "SKILL", "AGENTS", "CHANGELOG", "INSTALL", "UPDATE"}
RUNTIME_CONFIG = {
    "authorization.json", "calendar.json", "communication.json", "design.json",
    "humanizer.json", "identity.json", "media.json", "market.json", "payment.json",
    "platform.json", "pricing.json", "profile.json", "recovery.json", "routes.json",
    "scoring.json", "search.json", "runtime.json", "watch.json",
}


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def runtime_files() -> list[Path]:
    files: list[Path] = []
    for directory in ("agents", "adapters", "core", "runtime"):
        files.extend(sorted((ROOT / directory).rglob("*.py")))
    for path in sorted((ROOT / "tools").glob("*.py")):
        if path.name not in RUNTIME_TOOL_EXCLUDES:
            files.append(path)
    files.extend(ROOT / "config" / name for name in sorted(RUNTIME_CONFIG))
    for directory in ("knowledge", "vendor/humanizer"):
        files.extend(sorted((ROOT / directory).glob("*.json")))
        files.extend(sorted((ROOT / directory).glob("*.jsonl")))
        files.extend(sorted((ROOT / directory).glob("*.sql")))
        files.extend(sorted((ROOT / directory).glob("*.py")))
    files.extend([ROOT / "vendor" / "humanizer" / "LICENSE", ROOT / "data" / "schema.sql"])
    files.extend([ROOT / "docs" / "core.md", ROOT / "docs" / "context.md", ROOT / "docs" / "foundations.md"])
    unique: dict[str, Path] = {}
    for path in files:
        if path.exists() and path.is_file():
            unique[path.relative_to(ROOT).as_posix()] = path
    return [unique[name] for name in sorted(unique)]


def bundle_name(path: Path) -> str:
    if path == ROOT / "data" / "schema.sql":
        return "data/schema.sql"
    return path.relative_to(ROOT).as_posix()


def audit_runtime_surface() -> list[str]:
    errors: list[str] = []
    manifest = load_json("manifest.json")
    identity = load_json("config/identity.json")
    if manifest.get("version") != "0.2.0":
        errors.append("manifest version must be 0.2.0")
    if identity.get("version") != manifest.get("version"):
        errors.append("identity and manifest versions differ")
    required = [manifest.get(key) for key in ("identity", "active_source_of_truth", "active_runtime_context", "active_foundations", "active_execution_kernel", "schema")]
    if any(not value or not (ROOT / value).exists() for value in required):
        errors.append("manifest has a missing required path")
    if not Path(ROOT / "knowledge/schema.json").exists() or not Path(ROOT / "tools/index.py").exists() or not Path(ROOT / "tools/retrieve.py").exists():
        errors.append("structured knowledge and retrieval entrypoints are incomplete")
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from index import _records
        _records()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        errors.append(f"knowledge validation failed: {exc}")
    if set(path.name for path in (ROOT / "vendor/humanizer").iterdir() if path.is_file()) != HUMANIZER_ALLOWED:
        errors.append("humanizer vendor must contain runtime files and license only")
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".db", ".sqlite", ".sqlite3"}:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if not rel.startswith("runtime_data/"):
            errors.append(f"database artifact in public tree: {rel}")
    return errors


def audit_bundle(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"bundle missing: {path}"]
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            errors.append("bundle contains duplicate paths")
        for name in names:
            upper = name.upper()
            basename = Path(name).name.upper()
            if any(token in basename for token in FORBIDDEN_BUNDLE_NAMES):
                errors.append(f"instructional/install file in bundle: {name}")
            if name.startswith(("tests/", "reports/", "memory/", "release/", "docs/reference/")):
                errors.append(f"non-runtime path in bundle: {name}")
            if Path(name).suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
                errors.append(f"database artifact in bundle: {name}")
            if name.endswith("/"):
                continue
            try:
                text = archive.read(name).decode("utf-8")
            except UnicodeDecodeError:
                continue
            lower = text.lower()
            if PUBLIC_NAME.lower() in lower or "autonomia" in lower:
                errors.append(f"public software identity leaked into bundle: {name}")
            if "installation" in lower or "install instructions" in lower:
                errors.append(f"installation language leaked into bundle: {name}")
    return sorted(set(errors))


def build_bundle(output: str | None = None) -> Path:
    manifest = load_json("manifest.json")
    version = manifest["version"]
    destination = Path(output).expanduser().resolve() if output else ROOT / "release" / f"worker-{version}.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = runtime_files()
    with tempfile.TemporaryDirectory(prefix="runtime-bundle-") as temp:
        staging = Path(temp) / "runtime"
        for source in files:
            target = staging / bundle_name(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        payload = {
            "format": "runtime_bundle",
            "version": version,
            "runtime_identity": "owner_or_company_profile",
            "public_software_name_is_not_external_identity": True,
            "knowledge": {"records": "knowledge/*.jsonl", "schema": "knowledge/schema.json", "indexer": "tools/index.py", "retriever": "tools/retrieve.py"},
            "database_policy": "created_locally_at_first_run_and_never_overwritten_by_update",
        }
        (staging / "bundle.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary_zip = Path(temp) / destination.name
        with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for source in sorted(staging.rglob("*")):
                if source.is_file():
                    archive.write(source, source.relative_to(staging).as_posix())
        shutil.copy2(temporary_zip, destination)
    errors = audit_bundle(destination)
    if errors:
        raise RuntimeError("bundle audit failed:\n" + "\n".join(" - " + error for error in errors))
    return destination


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit the release surface and optionally build the runtime zip")
    ap.add_argument("--bundle", action="store_true", help="build the clean runtime zip")
    ap.add_argument("--output")
    args = ap.parse_args()
    errors = audit_runtime_surface()
    if errors:
        print("AUDIT FAILED")
        print("\n".join(" - " + error for error in errors))
        return 1
    if args.bundle:
        try:
            path = build_bundle(args.output)
        except RuntimeError as exc:
            print(str(exc))
            return 1
        print(json.dumps({"status": "PASS", "bundle": str(path), "files": len(runtime_files()) + 1}, ensure_ascii=False, indent=2))
    else:
        print("AUDIT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
