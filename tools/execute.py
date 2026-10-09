#!/usr/bin/env python3
"""Runtime entrypoint with a durable worker loop."""
from __future__ import annotations
import argparse, json, os, signal, time
from datetime import datetime, timezone
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from agents.worker import AutonomousWorker, ActionReceipt
from runtime.store import RuntimeStore

_STOP=False

def _stop(*_):
    global _STOP; _STOP=True


def make_executor():
    command=os.environ.get('WORKER_EXECUTOR_CMD')
    if command:
        import subprocess
        def execute_command(mission):
            proc=subprocess.run(command,shell=True,input=json.dumps(mission,ensure_ascii=False),text=True,capture_output=True,timeout=600)
            if proc.returncode:
                return ActionReceipt(mission.get('next_action') or 'unknown','BLOCKED',{'stderr':proc.stderr[-2000:]},blocker='EXECUTOR_ERROR')
            try: data=json.loads(proc.stdout)
            except json.JSONDecodeError: return ActionReceipt(mission.get('next_action') or 'unknown','FAILED',{'stdout':proc.stdout[-2000:]},blocker='INVALID_EXECUTOR_RECEIPT')
            return ActionReceipt(data.get('action',mission.get('next_action') or 'unknown'),data.get('status','UNKNOWN'),data.get('result') or {},data.get('evidence_ref'),data.get('blocker'))
        return execute_command

    profile=os.environ.get('WORKER_BROWSER_PROFILE')
    if profile:
        def execute_browser(mission):
            try:
                from adapters.browser import PlaywrightBrowser
                from adapters.operate import BrowserOperator
                from adapters.research import BrowserResearcher
                browser=PlaywrightBrowser(profile,headless=os.environ.get('WORKER_BROWSER_HEADLESS','0')=='1')
                browser.start()
                try:
                    meta=mission.get('metadata') or {}
                    if mission.get('next_action')=='research_and_score_market':
                        researcher=BrowserResearcher(browser)
                        results=[]
                        for query in (meta.get('queries') or [])[:3]:
                            r=researcher.search(query); results.append(r.__dict__)
                            if r.status=='BLOCKED':
                                return ActionReceipt('research_and_score_market','BLOCKED',{'results':results},blocker=r.blocker)
                        return ActionReceipt('research_and_score_market','SUCCESS',{'results':results},evidence_ref='browser_research')
                    steps=meta.get('browser_steps')
                    if steps:
                        result=BrowserOperator(browser).run(steps)
                        return ActionReceipt(mission.get('next_action') or 'browser_task',result.get('status','UNKNOWN'),result,evidence_ref='browser_operator',blocker=result.get('blocker'))
                    return ActionReceipt(mission.get('next_action') or 'browser_task','BLOCKED',{},blocker='NO_EXECUTABLE_BROWSER_ROUTE')
                finally:
                    browser.close()
            except Exception as exc:
                return ActionReceipt(mission.get('next_action') or 'browser_task','BLOCKED',{'error':str(exc)},blocker='BROWSER_RUNTIME_UNAVAILABLE')
        return execute_browser
    return None


def once()->dict:
    store=RuntimeStore.open()
    try: return AutonomousWorker(store=store,executor=make_executor()).cycle()
    finally: store.db.close()


def _next_wake_seconds(default_interval:int=30)->float:
    store=RuntimeStore.open()
    try:
        if not store._table_exists('wake_queue'): return float(default_interval)
        row=store.db.execute("SELECT due_at FROM wake_queue WHERE status='queued' ORDER BY due_at ASC LIMIT 1").fetchone()
    finally: store.db.close()
    if not row: return float(default_interval)
    try:
        due=datetime.fromisoformat(row['due_at'].replace('Z','+00:00'))
        return max(1.0,min(float(default_interval),(due-datetime.now(timezone.utc)).total_seconds()))
    except ValueError: return float(default_interval)


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--once',action='store_true'); ap.add_argument('--daemon',action='store_true'); ap.add_argument('--interval',type=int,default=30)
    args=ap.parse_args(); signal.signal(signal.SIGINT,_stop); signal.signal(signal.SIGTERM,_stop)
    if args.daemon:
        while not _STOP:
            print(json.dumps(once(),ensure_ascii=False),flush=True)
            sleep_for=_next_wake_seconds(max(1,args.interval))
            end=time.monotonic()+sleep_for
            while not _STOP and time.monotonic()<end: time.sleep(min(1.0,end-time.monotonic()))
        return 0
    print(json.dumps(once(),ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
