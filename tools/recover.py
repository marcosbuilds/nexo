#!/usr/bin/env python3
"""Classify and choose a recovery path without blind retries."""
from __future__ import annotations
import argparse, hashlib, json

RETRYABLE = {'TRANSIENT_NETWORK','RATE_LIMIT','STALE_STATE','VALIDATION_FAILED','UNKNOWN'}

def fingerprint(provider, operation, payload):
    raw = json.dumps({'provider':provider,'operation':operation,'payload':payload}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def classify(error_code='', message='', kind=''):
    text = f'{kind} {error_code} {message}'.lower()
    if '429' in text or 'rate limit' in text: return 'RATE_LIMIT'
    if any(x in text for x in ('timeout','timed out','connection','network','temporarily unavailable','502','503','504')): return 'TRANSIENT_NETWORK'
    if any(x in text for x in ('401','expired','session expired','unauthorized')): return 'AUTH_EXPIRED'
    if any(x in text for x in ('403','forbidden','permission denied')): return 'PERMISSION_DENIED'
    if any(x in text for x in ('captcha','otp','manual verification')): return 'PLATFORM_MANUAL_INTERVENTION'
    if any(x in text for x in ('view once','visualização única')): return 'VIEW_ONCE_INACCESSIBLE'
    if any(x in text for x in ('audio','transcrib') and 'fail' in text): return 'MEDIA_INACCESSIBLE'
    if any(x in text for x in ('duplicate','already sent','already exists')): return 'DUPLICATE_RISK'
    if any(x in text for x in ('stale','outdated','element not found','state changed')): return 'STALE_STATE'
    if any(x in text for x in ('invalid','validation')): return 'VALIDATION_FAILED'
    return 'UNKNOWN'

def recover(error_class, attempt, provider_retry_after=None, state_changed=False):
    # A retry is a new experiment, not a reflex. The caller must show what
    # changed; otherwise the worker would keep pushing the same failed route.
    if error_class in RETRYABLE and not state_changed:
        return {
            'action': 'INSPECT_AND_CHANGE_STATE',
            'retry': False,
            'reason': 'no_state_change_since_last_attempt',
        }
    if error_class == 'RATE_LIMIT':
        return {'action':'WAIT_AND_RETRY','retry':attempt < 2,'delay_seconds': provider_retry_after or min(300, 2 ** attempt * 5)}
    if error_class in {'TRANSIENT_NETWORK','STALE_STATE','VALIDATION_FAILED'}:
        return {'action':'RETRY_WITH_STATE_CHANGE','retry':attempt < 2,'delay_seconds':min(60, 2 ** attempt)}
    if error_class == 'AUTH_EXPIRED':
        return {'action':'REVALIDATE_SESSION','retry':False,'human_if_revalidation_fails':True}
    if error_class == 'PERMISSION_DENIED':
        return {'action':'TRY_AUTHORIZED_FALLBACK','retry':False,'human_if_all_routes_fail':True}
    if error_class in {'VIEW_ONCE_INACCESSIBLE','MEDIA_INACCESSIBLE'}:
        return {'action':'REQUEST_SUPPORTED_INPUT','retry':False}
    if error_class == 'DUPLICATE_RISK':
        return {'action':'IDEMPOTENCY_CHECK','retry':False}
    if error_class == 'PLATFORM_MANUAL_INTERVENTION':
        return {'action':'QUEUE_HUMAN_BLOCKER','retry':False}
    return {'action':'ISOLATE_ERROR_AND_CONTINUE_INDEPENDENT_WORK','retry':False}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--json',required=True); d=json.loads(ap.parse_args().json)
    ec=classify(d.get('error_code',''),d.get('message',''),d.get('kind',''))
    out={'error_class':ec,'recovery':recover(ec,int(d.get('attempt',0)),d.get('provider_retry_after'),bool(d.get('state_changed')))}
    if d.get('provider') and d.get('operation'): out['idempotency_key']=fingerprint(d['provider'],d['operation'],d.get('payload',{}))
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
