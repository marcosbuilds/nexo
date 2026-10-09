#!/usr/bin/env python3
"""Durable local agenda + wake queue, with atomic event/reminder creation."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'tools'))
from db import connect

def create_reminder(d):
    c=connect()
    try:
        existing=c.execute("SELECT id,due_at,status,next_fire_at FROM reminders WHERE title=? AND due_at=? AND status IN ('scheduled','fired')",(d['title'],d['due_at'])).fetchone()
        if existing and not d.get('force_duplicate',False):
            return {'reminder_id':existing['id'],'status':'already_scheduled','next_wake_at':existing['next_fire_at'] or existing['due_at']}
        cur=c.execute("INSERT INTO reminders(event_id,context_type,context_id,title,message,due_at,delivery,status,priority,repeat_rule,next_fire_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (d.get('event_id'),d.get('context_type'),d.get('context_id'),d['title'],d.get('message'),d['due_at'],d.get('delivery','runtime_wake'),'scheduled',int(d.get('priority',3)),d.get('repeat_rule'),d.get('next_fire_at',d['due_at'])))
        rid=cur.lastrowid
        c.execute("INSERT INTO wake_queue(wake_type,due_at,priority,context_type,context_id,source_ref,status) VALUES(?,?,?,?,?,?,?)",
            ('REMINDER',d.get('next_fire_at',d['due_at']),int(d.get('priority',3)),d.get('context_type'),d.get('context_id'),f'reminder:{rid}','queued'))
        c.commit(); return {'reminder_id':rid,'status':'scheduled','next_wake_at':d.get('next_fire_at',d['due_at'])}
    finally: c.close()

def create_event(d):
    c=connect()
    try:
        cur=c.execute("INSERT INTO calendar_events(calendar_id,external_event_id,title,description,start_at,end_at,timezone,status,source,context_type,context_id,recurrence_rule,sync_state) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
          (d.get('calendar_id'),d.get('external_event_id'),d['title'],d.get('description'),d['start_at'],d.get('end_at'),d.get('timezone'),'scheduled',d.get('source','local'),d.get('context_type'),d.get('context_id'),d.get('recurrence_rule'),d.get('sync_state','local_only')))
        eid=cur.lastrowid
        if d.get('reminder_due_at'):
            existing=c.execute("SELECT id FROM reminders WHERE title=? AND due_at=? AND status IN ('scheduled','fired')",(d.get('reminder_title',d['title']),d['reminder_due_at'])).fetchone()
            if not existing:
                rid=c.execute("INSERT INTO reminders(event_id,context_type,context_id,title,message,due_at,delivery,status,priority,next_fire_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(eid,d.get('context_type'),d.get('context_id'),d.get('reminder_title',d['title']),d.get('message'),d['reminder_due_at'],'runtime_wake','scheduled',int(d.get('priority',3)),d['reminder_due_at'])).lastrowid
                c.execute("INSERT INTO wake_queue(wake_type,due_at,priority,context_type,context_id,source_ref,status) VALUES(?,?,?,?,?,?,?)",('REMINDER',d['reminder_due_at'],int(d.get('priority',3)),d.get('context_type'),d.get('context_id'),f'reminder:{rid}','queued'))
        c.commit(); return {'event_id':eid,'status':'scheduled'}
    finally: c.close()

def list_agenda(d):
    c=connect()
    try:
        rows=c.execute("SELECT id,title,description,start_at,end_at,timezone,status,source,context_type,context_id FROM calendar_events WHERE status='scheduled' AND start_at>=? AND (? IS NULL OR start_at<?) ORDER BY start_at LIMIT ?",(d['from_at'],d.get('to_at'),d.get('to_at'),int(d.get('limit',50)))).fetchall()
        return {'events':[dict(r) for r in rows]}
    finally:c.close()

def due(d):
    c=connect()
    try:
        rows=c.execute("SELECT id,wake_type,due_at,priority,context_type,context_id,source_ref FROM wake_queue WHERE status='queued' AND due_at<=? ORDER BY priority ASC,due_at ASC LIMIT ?",(d['now'],int(d.get('limit',20)))).fetchall(); return {'due':[dict(r) for r in rows]}
    finally:c.close()

def complete_wake(wake_id:int):
    c=connect()
    try:
        c.execute("UPDATE wake_queue SET status='completed',completed_at=CURRENT_TIMESTAMP WHERE id=? AND status='claimed'",(wake_id,)); c.commit(); return {'wake_id':wake_id,'status':'completed'}
    finally:c.close()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('action',choices=['create-reminder','create-event','agenda','due','complete']); ap.add_argument('--json',default='{}'); a=ap.parse_args(); d=json.loads(a.json)
    fn={'create-reminder':create_reminder,'create-event':create_event,'agenda':list_agenda,'due':due,'complete':lambda x:complete_wake(int(x['wake_id']))}[a.action]; print(json.dumps(fn(d),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
