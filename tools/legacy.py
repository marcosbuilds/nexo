#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIRS = [ROOT/"core", ROOT/"agents", ROOT/"adapters", ROOT/"tools", ROOT/"config"]
PATTERNS = [
    "5" + "SIM",
    "SMS " + "Atlas",
    "saldo_" + "5" + "sim",
    "custo_" + "efetivo_brl_por_usd",
    "precos_" + "cliente",
    "precos_" + "interna",
]
SELF = Path(__file__).resolve()
hits=[]
for base in ACTIVE_DIRS:
    if not base.exists(): continue
    for p in base.rglob("*"):
        if p.name in {"legacy.py", "audit.py"} or not p.is_file() or p.suffix.lower() not in {".md",".txt",".json",".py",".sql",".yaml",".yml",".toml",".js",".ts"}:
            continue
        try: t=p.read_text(encoding="utf-8", errors="ignore")
        except Exception: continue
        for pat in PATTERNS:
            if pat.lower() in t.lower(): hits.append((p.relative_to(ROOT),pat))
if hits:
    print("LEGACY REFERENCES FOUND IN ACTIVE RUNTIME")
    for p,pat in hits: print(f"- {p}: {pat}")
    sys.exit(1)
print("OK: no legacy references in active runtime/config/tools.")
