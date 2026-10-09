#!/usr/bin/env python3
"""Evidence-based priority score for contacts, companies and opportunities."""
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'config'/'scoring.json').read_text(encoding='utf-8'))

def clamp(x): return max(0.0,min(1.0,float(x)))

def score(data):
    factors=data.get('factors') or {}
    evidence=int(data.get('evidence_count',0))
    weighted=0.0; used={}
    for k,w in CFG['dimensions'].items():
        v=clamp(factors.get(k,0.0)); used[k]=v
        weighted += v*w
    penalty=0.0
    for k,w in CFG['penalties'].items():
        if k=='policy_risk': v=clamp(factors.get(k,0.0))
        else: v=clamp(factors.get(k,0.0))
        penalty += v*w
    raw=max(0.0,min(1.0,weighted-penalty))
    s=round(raw*100,2)
    conf=min(1.0,(evidence/CFG['guardrails']['minimum_evidence_for_high_priority']))
    conf*=min(1.0,sum(1 for k in CFG['dimensions'] if k in factors)/len(CFG['dimensions']))
    band=next((b for b,r in CFG['priority_bands'].items() if r[0]<=s<=r[1]),'LOW')
    reasons=[]
    for k,v in sorted(used.items(), key=lambda kv: kv[1]*CFG['dimensions'][kv[0]], reverse=True)[:3]:
        reasons.append({'factor':k,'value':round(v,3),'effect':'positive'})
    return {'entity_type':data.get('entity_type','contact'),'entity_id':data.get('entity_id'),'score':s,'confidence':round(conf,3),'priority':band,'reasons':reasons,'recommended_action':CFG['recommended_actions'][band]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True)
    print(json.dumps(score(json.loads(ap.parse_args().json)),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
