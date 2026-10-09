#!/usr/bin/env python3
"""Build and audit the runtime allowlist without leaving a tracked ZIP."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_NAME = "Nexo"
PUBLIC_ALIASES = {PUBLIC_NAME.lower(), "autonomia"}
HUMANIZER_ALLOWED = {"__init__.py", "engine.py", "LICENSE", "contract.json"}
RUNTIME_TOOL_EXCLUDES = {
    "audit.py", "legacy.py", "package.py", "install.py", "update.py",
}
RUNTIME_CONFIG = {
    "authorization.json", "autonomy.json", "calendar.json", "communication.json",
    "design.json", "humanizer.json", "identity.json", "market.json", "media.json",
    "payment.json", "platform.json", "pricing.json", "profile.json", "recovery.json",
    "routes.json", "runtime.json", "scoring.json", "search.json", "watch.json",
}
RUNTIME_DOCS = {"docs/core.md", "docs/context.md", "docs/foundations.md"}
FORBIDDEN_BUNDLE_PARTS = {
    "README.md", "LICENSE.md", "SKILL.md", "AGENTS.md", "CHANGELOG.md",
    "INSTALL.md", "UPDATE.md", "tests", "reports", "memory", "release",
    "archive", "reference", "legacy", ".git",
}
ABSOLUTE_PATH = __import__("re").compile(
    r"(?<![A-Za-z])(?:[A-Za-z]:[\\/]|\\\\|/(?:home|Users|mnt|private|var|tmp)/)",
    __import__("re").I,
)


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def runtime_files() -> list[Path]:
    files: dict[str, Path] = {}
    for directory in ("agents", "adapters", "core", "runtime"):
        for path in (ROOT / directory).rglob("*.py"):
            if "__pycache__" not in path.parts:
                files[path.relative_to(ROOT).as_posix()] = path
    for path in (ROOT / "tools").glob("*.py"):
        if path.name not in RUNTIME_TOOL_EXCLUDES:
            files[path.relative_to(ROOT).as_posix()] = path
    for name in RUNTIME_CONFIG:
        path = ROOT / "config" / name
        if path.exists():
            files[path.relative_to(ROOT).as_posix()] = path
    for directory in (ROOT / "knowledge", ROOT / "vendor" / "humanizer"):
        for path in directory.iterdir():
            if path.is_file() and (path.suffix.lower() in {".json", ".jsonl", ".py"} or path.name in {"LICENSE", "contract.json"}):
                files[path.relative_to(ROOT).as_posix()] = path
    for relative in ("data/schema.sql", *RUNTIME_DOCS):
        path = ROOT / relative
        if path.exists():
            files[relative] = path
    return [files[name] for name in sorted(files)]


def bundle_name(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def audit_runtime_surface() -> list[str]:
    errors: list[str] = []
    manifest = load_json("manifest.json")
    identity = load_json("config/identity.json")
    if not manifest.get("software_version"):
        errors.append("manifest software version is missing")
    if not manifest.get("worker_version"):
        errors.append("manifest worker version is missing")
    if manifest.get("version") != manifest.get("software_version"):
        errors.append("manifest version and software_version differ")
    if identity.get("version") != manifest.get("software_version"):
        errors.append("identity and software versions differ")
    required = [
        manifest.get(key) for key in
        ("identity", "active_source_of_truth", "active_runtime_context", "active_foundations", "active_execution_kernel", "schema", "knowledge_schema", "knowledge_sources")
    ]
    if any(not value or not (ROOT / value).exists() for value in required):
        errors.append("manifest has a missing required path")
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from index import _records
        _records()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        errors.append(f"knowledge validation failed: {exc}")
    humanizer = ROOT / "vendor" / "humanizer"
    actual = {path.name for path in humanizer.iterdir() if path.is_file()}
    if actual != HUMANIZER_ALLOWED:
        errors.append(f"humanizer runtime surface mismatch: {sorted(actual)}")
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".db", ".sqlite", ".sqlite3"} and "runtime_data" not in path.relative_to(ROOT).parts:
            errors.append(f"database artifact in public tree: {path.relative_to(ROOT).as_posix()}")
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
            normalized = name.replace("\\", "/")
            parts = set(Path(normalized).parts)
            if parts & FORBIDDEN_BUNDLE_PARTS:
                errors.append(f"non-runtime path in bundle: {name}")
            if Path(name).suffix.lower() in {".db", ".sqlite", ".sqlite3", ".zip"}:
                errors.append(f"binary state artifact in bundle: {name}")
            if name.endswith("/"):
                continue
            try:
                content = archive.read(name).decode("utf-8")
            except UnicodeDecodeError:
                continue
            lower = content.lower()
            if any(alias in lower for alias in PUBLIC_ALIASES):
                errors.append(f"public software identity leaked into bundle: {name}")
            if ABSOLUTE_PATH.search(content):
                errors.append(f"machine path leaked into bundle: {name}")
            if any(token in lower for token in ("install instructions", "installation guide", "developer instructions", "repository maintenance")):
                errors.append(f"development or installation language leaked into bundle: {name}")
    return sorted(set(errors))


def build_bundle(output: str | None = None) -> Path:
    manifest = load_json("manifest.json")
    worker_version = manifest["worker_version"]
    if output:
        destination = Path(output).expanduser().resolve()
    else:
        destination = Path(tempfile.gettempdir()) / f"worker-{worker_version}.zip"
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
            "software_version": manifest["software_version"],
            "worker_version": worker_version,
            "runtime_identity": "authorized_owner_or_company_profile",
            "public_project_identity_is_not_external_identity": True,
            "knowledge": {"records": "knowledge/*.jsonl", "schema": "knowledge/schema.json", "indexer": "tools/index.py", "retriever": "tools/retrieve.py"},
            "database_policy": "created locally at first run and never overwritten by update",
        }
        (staging / "bundle.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary_zip = Path(temp) / destination.name
        with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for source in sorted(staging.rglob("*")):
                if source.is_file():
                    name = source.relative_to(staging).as_posix()
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, source.read_bytes())
        shutil.copy2(temporary_zip, destination)
    errors = audit_bundle(destination)
    if errors:
        destination.unlink(missing_ok=True)
        raise RuntimeError("bundle audit failed:\n" + "\n".join(" - " + error for error in errors))
    return destination


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit the source tree and build a clean runtime ZIP in a temporary or explicit output path")
    ap.add_argument("--bundle", action="store_true")
    ap.add_argument("--output")
    args = ap.parse_args()
    errors = audit_runtime_surface()
    if errors:
        print("AUDIT FAILED")
        print("\n".join(" - " + error for error in errors))
        return 1
    if not args.bundle:
        print("AUDIT PASSED")
        return 0
    try:
        path = build_bundle(args.output)
    except RuntimeError as exc:
        print(str(exc))
        return 1
    print(json.dumps({"status": "PASS", "bundle": str(path), "sha256": checksum(path), "files": len(runtime_files()) + 1}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
