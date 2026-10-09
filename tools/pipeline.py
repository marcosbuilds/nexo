#!/usr/bin/env python3
"""CLI for real audio/video recovery before asking the sender to repeat."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from adapters.media import extract_audio, transcribe

def process(d):
    typ=(d.get('media_type') or '').lower(); path=d.get('path')
    if typ=='audio': return transcribe(path, model=d.get('model','base')).__dict__
    if typ=='video':
        extracted=extract_audio(path)
        if extracted.status!='SUCCESS': return extracted.__dict__
        out=transcribe(extracted.extracted_audio, model=d.get('model','base'))
        out.evidence={**(out.evidence or {}),'source_video':path}
        return out.__dict__
    return {'status':'FAILED','media_type':typ,'error_class':'CAPABILITY_UNAVAILABLE','evidence':{'reason':'unsupported_media_type_for_pipeline'}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True); print(json.dumps(process(json.loads(ap.parse_args().json)),ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
