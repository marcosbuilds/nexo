#!/usr/bin/env python3
"""Deterministic media-access gate shared by every communication channel."""
from __future__ import annotations
import argparse, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'config'/'media.json'

def load(): return json.loads(POLICY.read_text(encoding='utf-8'))

def decide(data: dict)->dict:
    t=(data.get('media_type') or '').lower()
    view_once=bool(data.get('view_once',False))
    status=(data.get('status') or '').lower()
    p=load()['fallbacks']
    if view_once and not bool(data.get('view_once_accessible',False)):
        return {'decision':'REQUEST_RESHARE_NORMAL','reason':'view_once_unavailable','message':p['view_once_unavailable']['message']}
    if t=='audio' and not bool(data.get('transcribed',False)):
        reason='audio_transcription_failed' if status in {'decode_failed','transcription_failed','timeout','error'} else 'audio_unavailable'
        return {'decision':'REQUEST_TEXT','reason':reason,'message':p[reason]['message']}
    if t=='image' and not bool(data.get('previewed',False)):
        return {'decision':'REQUEST_REUPLOAD_OR_DESCRIBE','reason':'image_preview_failed','message':p['image_preview_failed']['message']}
    if t=='video' and not bool(data.get('previewed',False)):
        return {'decision':'REQUEST_REUPLOAD_OR_DESCRIBE','reason':'video_preview_failed','message':p['video_preview_failed']['message']}
    if t=='document' and not bool(data.get('parsed',False)):
        return {'decision':'REQUEST_REUPLOAD_OR_TEXT','reason':'document_parse_failed','message':p['document_parse_failed']['message']}
    return {'decision':'CONTINUE_MEDIA_ANALYSIS','reason':'media_capability_succeeded'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True)
    d=decide(json.loads(ap.parse_args().json)); print(json.dumps(d,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
