#!/usr/bin/env python3
"""Release audit: package gates and active sources remain coherent."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors=[]
    banned={'.sqlite','.sqlite3','.db'}
    for path in ROOT.rglob('*'):
        if not path.is_file():
            continue
        rel=path.relative_to(ROOT).as_posix()
        if any(part == '__pycache__' for part in path.parts):
            continue
        if rel.startswith(('runtime_data/', 'archive/', 'docs/legacy/')):
            # These are explicitly local or historical surfaces. The external
            # release tool separately checks that ignored paths are not staged.
            continue
        if path.suffix.lower() in banned:
            errors.append(f'database artifact shipped: {rel}')
    manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    policy=json.loads((ROOT/'config/runtime.json').read_text(encoding='utf-8'))
    auth=json.loads((ROOT/'config/authorization.json').read_text(encoding='utf-8'))
    comm=json.loads((ROOT/'config/communication.json').read_text(encoding='utf-8'))
    market=json.loads((ROOT/'config/market.json').read_text(encoding='utf-8'))
    design=json.loads((ROOT/'config/design.json').read_text(encoding='utf-8'))
    candidate_ids=set(market.get('selection', {}).get('initial_scan_candidate_ids', []))
    identity=json.loads((ROOT/'config/identity.json').read_text(encoding='utf-8'))
    required_paths = [
        manifest.get('identity'),
        manifest.get('active_source_of_truth'),
        manifest.get('active_runtime_context'),
        manifest.get('active_foundations'),
        manifest.get('active_execution_kernel'),
        manifest.get('schema'),
    ]
    paths_ok = all(path and (ROOT / path).exists() for path in required_paths)
    checks={
        'manifest_version':manifest.get('version')=='0.1.0',
        'identity_version':identity.get('version')==manifest.get('version'),
        'runtime_revision':policy.get('behavioral_revision')=='0.1.0',
        'context_entrypoint':Path(ROOT/manifest['active_execution_kernel']).exists(),
        'nexo_source':manifest.get('active_source_of_truth')=='docs/core.md',
        'required_paths':paths_ok,
        'mission_layer':Path(ROOT/'core/mission.py').exists(),
        'worker_runtime':Path(ROOT/'tools/execute.py').exists(),
        'regression_suite':Path(ROOT/'tests/behavior.py').exists(),
        'empty_queue_demand_generation':policy.get('empty_queue_behavior',{}).get('never_end_just_because_queue_is_empty') is True,
        'connected_access_permission':auth.get('operational_interpretation',{}).get('connected_access_is_permission') is True,
        'humanizer_behavioral_governor_and_final_gate':comm.get('humanizer',{}).get('role')=='upstream_behavioral_governor_and_final_gate',
        'communication_gate':Path(ROOT/'tools/communicate.py').exists(),
        'work_seeking':Path(ROOT/'tools/search.py').exists(),
        'canonical_db_helper':Path(ROOT/'tools/db.py').exists(),
        'principles_document':Path(ROOT/'docs/foundations.md').exists(),
        'market_hypothesis_policy':len(market.get('commercial_hypotheses', [])) >= 4 and len(candidate_ids) >= 3,
        'design_policy':len(design.get('canva', {}).get('magic_media', {}).get('prompt_fields_required', [])) >= 8,
        'no_legacy_source_in_active_manifest':not any('legacy' in str(value).lower() for value in manifest.get('active_documents', [])),
    }
    errors += [f'failed policy check: {name}' for name,ok in checks.items() if not ok]
    if errors:
        print('AUDIT FAILED')
        for e in errors: print(' -',e)
        return 1
    print('AUDIT PASSED')
    print(json.dumps({'checks':checks,'database_shipping':'forbidden'},ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
