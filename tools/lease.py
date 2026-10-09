#!/usr/bin/env python3
"""Single active worker lease so two processes cannot scramble browser state."""
from __future__ import annotations
import argparse,json,os,uuid
from datetime import datetime,timezone,timedelta
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from db import connect

def acquire(worker_id=None, ttl_seconds=90):
    worker_id=worker_id or str(uuid.uuid4()); now=datetime.now(timezone.utc).isoformat(); con=connect()
    try:
        row=con.execute('SELECT worker_id,heartbeat_at,status FROM runtime_leases ORDER BY id LIMIT 1').fetchone()
        if row and row['status']=='active':
            try:
                last=datetime.fromisoformat(row['heartbeat_at'])
                if datetime.now(timezone.utc)-last < timedelta(seconds=ttl_seconds) and row['worker_id']!=worker_id:
                    return {'acquired':False,'owner':row['worker_id'],'heartbeat_at':row['heartbeat_at']}
            except ValueError: pass
        con.execute('DELETE FROM runtime_leases'); con.execute('INSERT INTO runtime_leases(worker_id,acquired_at,heartbeat_at,status) VALUES(?,?,?,?)',(worker_id,now,now,'active')); con.commit()
        return {'acquired':True,'worker_id':worker_id,'heartbeat_at':now}
    finally: con.close()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--worker-id'); print(json.dumps(acquire(ap.parse_args().worker_id),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
