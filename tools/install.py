#!/usr/bin/env python3
"""Install a runtime zip without replacing local profile or runtime data."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path


def safe_extract(bundle: Path, target: Path) -> None:
    target = target.resolve()
    with zipfile.ZipFile(bundle) as archive:
        for member in archive.infolist():
            destination = (target / member.filename).resolve()
            if destination != target and target not in destination.parents:
                raise ValueError(f"unsafe archive path: {member.filename}")
        archive.extractall(target)


def ensure_profile(target: Path, owner_name: str | None = None, company_name: str | None = None) -> Path:
    profile = target / "memory" / "owner.json"
    profile.parent.mkdir(parents=True, exist_ok=True)
    if profile.exists():
        data = json.loads(profile.read_text(encoding="utf-8"))
    else:
        template = json.loads((target / "config" / "profile.json").read_text(encoding="utf-8"))
        data = template
    identity = data.setdefault("identity", {})
    if owner_name:
        identity["full_name"] = owner_name
        identity["preferred_name"] = owner_name
    if company_name:
        identity["company_name"] = company_name
    if company_name or owner_name:
        identity["public_name"] = company_name or owner_name
    profile.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return profile


def rebuild_index(target: Path) -> None:
    indexer = target / "tools" / "index.py"
    if not indexer.exists():
        raise FileNotFoundError(indexer)
    output = target / "runtime_data" / "knowledge.sqlite3"
    subprocess.run([sys.executable, str(indexer), "--output", str(output)], cwd=target, check=True)


def install(bundle: str, target: str, *, owner_name: str | None = None, company_name: str | None = None) -> dict[str, str]:
    bundle_path = Path(bundle).expanduser().resolve()
    target_path = Path(target).expanduser().resolve()
    if not bundle_path.is_file():
        raise FileNotFoundError(bundle_path)
    target_path.mkdir(parents=True, exist_ok=True)
    safe_extract(bundle_path, target_path)
    profile = ensure_profile(target_path, owner_name, company_name)
    rebuild_index(target_path)
    return {"target": str(target_path), "profile": str(profile), "knowledge_index": str(target_path / "runtime_data" / "knowledge.sqlite3")}


def main() -> int:
    ap = argparse.ArgumentParser(description="Install a clean runtime bundle")
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--owner-name")
    ap.add_argument("--company-name")
    args = ap.parse_args()
    print(json.dumps(install(args.bundle, args.target, owner_name=args.owner_name, company_name=args.company_name), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
