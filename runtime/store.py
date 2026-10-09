"""Small persistence layer used by the autonomous worker and safe for package replacement."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

class RuntimeStore:
    def __init__(self, connection: sqlite3.Connection):
        self.db = connection

    @classmethod
    def open(cls, path: str | Path | None = None) -> "RuntimeStore":
        raw = str(path) if path else None
        if raw:
            db = sqlite3.connect(Path(raw).expanduser())
        else:
            import sys
            sys.path.insert(0, str(ROOT / "tools"))
            from db import connect
            db = connect()
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        schema = (ROOT / "data" / "schema.sql").read_text(encoding="utf-8")
        db.executescript(schema)
        db.commit()
        return cls(db)

    def snapshot(self) -> dict[str, Any]:
        def count(table: str, where: str = "1=1") -> int:
            row = self.db.execute(f"SELECT COUNT(*) c FROM {table} WHERE {where}").fetchone()
            return int(row["c"])
        def rows(sql: str, params=()):
            return [dict(r) for r in self.db.execute(sql, params).fetchall()]
        from core.market import snapshot as market_snapshot
        market = market_snapshot(self.db)
        if market.get("phase") == "initial_scan":
            candidates = market.get("candidate_scan", [])
        else:
            candidates = [market.get("active_niche", {})] if market.get("active_niche") else []
        demand_signals = []
        for item in candidates:
            if not item or not item.get("id"):
                continue
            stats = item.get("stats", {})
            demand_signals.append({
                "id": item["id"],
                "source": "public_market_research",
                "segment": item.get("name", "commercial hypothesis"),
                "buyer_segment": item.get("buyer_segment"),
                "hypothesis": item.get("offer_angle"),
                "niche_id": item["id"],
                "potential_value": 100,
                "probability": 0.2,
                "recurrence": 0.3,
                "minutes": 30,
                "research_mode": "initial_comparison" if market.get("phase") == "initial_scan" else "focused_validation",
                "queries": item.get("search_queries", []),
                "signals_to_verify": item.get("signals_to_verify", []),
                "required_capabilities": item.get("required_capabilities", []),
                "capability_test": item.get("capability_test"),
                "research_cycles": stats.get("research_cycles", 0),
                "qualified_leads": stats.get("qualified_leads", 0),
                "success_condition": "Save public URLs and date; record research_cycle after each completed search batch; record qualified_lead only with evidence of buyer, need and permitted contact channel.",
                "recording_tool": market.get("recording_tool"),
            })
        demand_signals.sort(key=lambda item: (item.get("research_cycles", 0), item.get("qualified_leads", 0), item.get("niche_id", "")))
        return {
            "active_jobs": rows("SELECT id, agreed_value value, deadline, status, estimated_hours * 45 next_minutes FROM jobs WHERE status IN ('active','accepted') ORDER BY COALESCE(deadline,'9999') LIMIT 8"),
            "pending_outcomes": rows("SELECT id action_id, event_type label, 20 economic_value FROM outcome_checks WHERE status='pending' ORDER BY id LIMIT 8"),
            "conversation_queue": rows("SELECT cp.conversation_id, ct.name, cs.commercial_value economic_value, cs.recommended_next_action objective FROM conversation_plans cp JOIN conversations c ON c.id=cp.conversation_id LEFT JOIN contacts ct ON ct.id=c.contact_id LEFT JOIN conversation_states cs ON cs.conversation_id=cp.conversation_id WHERE c.status='open' ORDER BY COALESCE(cs.commercial_value,0) DESC LIMIT 10"),
            "qualified_opportunities": rows("SELECT id, title, budget, estimated_cost cost, execution_confidence close_probability, recurrence_probability recurrence, risk FROM opportunities WHERE status IN ('discovered','qualified') ORDER BY COALESCE(score,0) DESC LIMIT 10"),
            "demand_signals": demand_signals,
            "market_strategy": market,
            "partnership_signals": [],
            "mission_count": count("missions") if self._table_exists("missions") else 0,
        }

    def _table_exists(self, name: str) -> bool:
        row = self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
        return row is not None

    def persist_mission(self, mission: dict[str, Any]) -> int | None:
        if not self._table_exists("missions"):
            return None
        cur = self.db.execute(
            "INSERT INTO missions(title,objective,goal_id,economic_value,probability_of_success,strategic_value,recurrence_potential,expected_minutes,expected_cost,risk,uncertainty,context_switch_cost,human_dependency,deadline_at,success_condition,owner_dependency,current_state,next_action,priority,metadata_json,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                mission["title"], mission["objective"], mission.get("goal_id"), mission.get("economic_value",0), mission.get("probability_of_success",0.5), mission.get("strategic_value",0.5), mission.get("recurrence_potential",0), mission.get("expected_minutes",30), mission.get("expected_cost",0), mission.get("risk",0), mission.get("uncertainty",0), mission.get("context_switch_cost",0), mission.get("human_dependency",0), mission.get("deadline_at"), mission.get("success_condition"), mission.get("owner_dependency"), mission.get("current_state"), mission.get("next_action"), mission.get("priority",0), json.dumps(mission.get("metadata",{}), ensure_ascii=False), "chosen"
            )
        )
        self.db.commit()
        return cur.lastrowid

    def claim_due_wakes(self, now_iso: str, limit: int = 10) -> list[dict[str, Any]]:
        if not self._table_exists("wake_queue"):
            return []
        rows = self.db.execute("SELECT id,wake_type,due_at,priority,context_type,context_id,source_ref FROM wake_queue WHERE status='queued' AND due_at<=? ORDER BY priority ASC,due_at ASC LIMIT ?", (now_iso, limit)).fetchall()
        claimed=[]
        for row in rows:
            if self.db.execute("UPDATE wake_queue SET status='claimed', claimed_at=? WHERE id=? AND status='queued'", (now_iso,row["id"])).rowcount:
                claimed.append(dict(row))
        self.db.commit()
        return claimed

    def journal(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._table_exists("runtime_journal"):
            self.db.execute("INSERT INTO runtime_journal(event_type,payload_json,created_at) VALUES(?,?,?)", (event_type, json.dumps(payload, ensure_ascii=False), datetime.now(timezone.utc).isoformat()))
            self.db.commit()

    def record_receipt(self, mission: dict[str, Any], receipt: Any) -> None:
        if not self._table_exists("runtime_receipts"):
            return
        self.db.execute("INSERT INTO runtime_receipts(mission_fingerprint,action_type,status,result_json,evidence_ref,blocker,created_at) VALUES(?,?,?,?,?,?,?)", (mission.get("metadata",{}).get("fingerprint") or mission.get("title"), receipt.action, receipt.status, json.dumps(receipt.result, ensure_ascii=False), receipt.evidence_ref, receipt.blocker, datetime.now(timezone.utc).isoformat()))
        self.db.commit()

    def record_learning(self, lesson: dict[str, Any]) -> None:
        """Persist a compact failure/result lesson with its evidence chain."""
        required = ("expected", "observed", "evidence", "cause", "change", "regression", "lesson")
        missing = [key for key in required if key not in lesson or lesson[key] in (None, "")]
        if missing:
            raise ValueError(f"learning_record_missing:{','.join(missing)}")
        if not self._table_exists("learning_events"):
            return
        observation = json.dumps(
            {
                "expected": lesson["expected"],
                "observed": lesson["observed"],
                "evidence": lesson["evidence"],
                "cause": lesson["cause"],
                "change": lesson["change"],
                "regression": lesson["regression"],
                "lesson": lesson["lesson"],
            },
            ensure_ascii=False,
        )
        self.db.execute(
            "INSERT INTO learning_events(category,observation,evidence_count,confidence,effect) VALUES(?,?,?,?,?)",
            (
                lesson.get("category", "runtime"),
                observation,
                int(lesson.get("evidence_count", 1) or 1),
                lesson.get("confidence"),
                lesson.get("effect") or lesson["lesson"],
            ),
        )
        self.db.commit()
