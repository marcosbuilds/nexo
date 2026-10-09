"""Evidence-led niche focus for the autonomous commercial worker.

The focus begins as a bounded hypothesis, not a claim that a market has been
validated. Real leads, outreach, replies, sales and delivery feedback determine
whether the worker keeps or changes the niche.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "market.json"

VALID_EVENTS = {
    "qualified_lead",
    "outreach_sent",
    "reply_positive",
    "reply_negative",
    "sale",
    "delivery_positive",
    "delivery_negative",
    "lead_rejected",
    "research_cycle",
    "capability_tested",
}
METRIC_FIELDS = (
    "observed_need", "recurrence", "capability_fit", "contactability",
    "budget_plausibility", "differentiation", "risk",
)


def load_policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Apply additive tables safely to already-deployed runtime databases."""
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS market_niche_observations (
      id INTEGER PRIMARY KEY,
      niche_id TEXT NOT NULL,
      event_type TEXT NOT NULL,
      external_ref TEXT,
      evidence_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_market_niche_events
      ON market_niche_observations(niche_id, event_type, created_at);
    CREATE UNIQUE INDEX IF NOT EXISTS uq_market_niche_external_event
      ON market_niche_observations(niche_id, event_type, external_ref)
      WHERE external_ref IS NOT NULL AND external_ref <> '';
    CREATE TABLE IF NOT EXISTS market_strategy_state (
      id INTEGER PRIMARY KEY CHECK (id = 1),
      active_niche_id TEXT NOT NULL,
      selected_at TEXT NOT NULL,
      phase TEXT NOT NULL DEFAULT 'initial_scan',
      reason TEXT NOT NULL DEFAULT '',
      last_review_at TEXT,
      candidate_scan_json TEXT NOT NULL DEFAULT '[]'
    );
    """)
    # Upgrade older runtime databases without replacing user/business data.
    state_columns = {r[1] for r in conn.execute("PRAGMA table_info(market_strategy_state)").fetchall()}
    if "candidate_scan_json" not in state_columns:
        conn.execute("ALTER TABLE market_strategy_state ADD COLUMN candidate_scan_json TEXT NOT NULL DEFAULT '[]'")
    policy = load_policy()
    candidates = _initial_candidate_ids(policy)
    niches = _niches_by_id(policy)
    legacy_map = {
        "barber_beauty": "creative_assets_barber_beauty",
        "home_services": "creative_assets_home_services",
        "food_local": "creative_assets_food_local",
        "auto_detailing": "creative_assets_auto_detailing",
    }
    # Migrate old niche-only evidence into the matching offer × buyer hypothesis.
    # Evidence is preserved; duplicate unique external references are safely ignored.
    for old_id, new_id in legacy_map.items():
        if new_id not in niches:
            continue
        old_rows = conn.execute(
            "SELECT id,event_type,external_ref,evidence_json,created_at FROM market_niche_observations WHERE niche_id=?",
            (old_id,),
        ).fetchall()
        for event in old_rows:
            conn.execute(
                "INSERT OR IGNORE INTO market_niche_observations(niche_id,event_type,external_ref,evidence_json,created_at) VALUES(?,?,?,?,?)",
                (new_id, event["event_type"], event["external_ref"], event["evidence_json"], event["created_at"]),
            )
        if old_rows:
            conn.execute("DELETE FROM market_niche_observations WHERE niche_id=?", (old_id,))

    now = datetime.now(timezone.utc).isoformat()
    row = conn.execute("SELECT * FROM market_strategy_state WHERE id=1").fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO market_strategy_state(id, active_niche_id, selected_at, phase, reason, candidate_scan_json) VALUES(1,?,?,?,?,?)",
            (candidates[0], now, "initial_scan",
             "Temporary offer × buyer hypotheses; compare four candidates with real capability and market evidence before choosing a focus.",
             json.dumps(candidates)),
        )
    else:
        current = dict(row)
        event_count = conn.execute("SELECT COUNT(*) FROM market_niche_observations").fetchone()[0]
        original_active = current.get("active_niche_id")
        mapped_active = legacy_map.get(original_active, original_active)
        stored_candidates = []
        try:
            stored_candidates = json.loads(current.get("candidate_scan_json") or "[]")
        except (TypeError, json.JSONDecodeError):
            stored_candidates = []
        stored_candidates = [legacy_map.get(str(x), str(x)) for x in stored_candidates]
        stored_candidates = [x for x in stored_candidates if x in niches]

        # A previous hard-coded/default focus with no observations is not a real decision.
        has_old_default = "Default test hypothesis" in str(current.get("reason", ""))
        has_unverified_legacy_focus = original_active in legacy_map and not event_count
        if not event_count and (has_old_default or has_unverified_legacy_focus or mapped_active not in niches):
            mapped_active = candidates[0]
            stored_candidates = candidates
            conn.execute(
                "UPDATE market_strategy_state SET active_niche_id=?, selected_at=?, phase='initial_scan', reason=?, candidate_scan_json=? WHERE id=1",
                (mapped_active, now,
                 "No observed market history supports the old focus; restart with a comparative offer × buyer scan and capability tests.",
                 json.dumps(candidates)),
            )
        else:
            # Preserve genuine history and an evidence-backed current focus. An unfinished
            # initial scan adopts the diversified current candidate set rather than locking
            # into the old single-service experiment.
            if current.get("phase") == "initial_scan":
                stored_candidates = candidates
            if not stored_candidates:
                stored_candidates = candidates
            conn.execute(
                "UPDATE market_strategy_state SET active_niche_id=?, candidate_scan_json=? WHERE id=1",
                (mapped_active if mapped_active in niches else candidates[0], json.dumps(stored_candidates)),
            )
    conn.commit()


def _clamp(value: Any, default: float = 0.5) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(0.0, min(1.0, number))


def _niches_by_id(policy: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    policy = policy or load_policy()
    return {n["id"]: n for n in policy.get("commercial_hypotheses", policy["niches"])}


def _initial_candidate_ids(policy: dict[str, Any] | None = None) -> list[str]:
    """Rank hypotheses for research order; prior scores are not market validation."""
    policy = policy or load_policy()
    niches = _niches_by_id(policy)
    selection = policy.get("selection", {})
    explicit = [str(x) for x in selection.get("initial_scan_candidate_ids", []) if str(x) in niches]
    count = max(1, int(selection.get("initial_scan_candidates", 3)))
    if explicit:
        return explicit[:count]
    baseline = [_event_metrics(niche, []) for niche in niches.values()]
    ranked = sorted(baseline, key=lambda item: item["score"], reverse=True)
    return [item["niche_id"] for item in ranked[:count]]


def _event_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT niche_id, event_type, external_ref, evidence_json, created_at "
        "FROM market_niche_observations ORDER BY created_at"
    ).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        try:
            item["evidence"] = json.loads(item.pop("evidence_json") or "{}")
        except json.JSONDecodeError:
            item["evidence"] = {}
            item.pop("evidence_json", None)
        out.append(item)
    return out


def _event_metrics(niche: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    prior = niche.get("prior", {})
    relevant = [e for e in events if e["niche_id"] == niche["id"]]
    qualified = [e for e in relevant if e["event_type"] == "qualified_lead"]
    capability_tests = [e for e in relevant if e["event_type"] == "capability_tested"]
    research_cycles = sum(e["event_type"] == "research_cycle" for e in relevant)
    outreach = sum(e["event_type"] == "outreach_sent" for e in relevant)
    positive = sum(e["event_type"] == "reply_positive" for e in relevant)
    negative = sum(e["event_type"] == "reply_negative" for e in relevant)
    sales = sum(e["event_type"] == "sale" for e in relevant)
    delivered_positive = sum(e["event_type"] == "delivery_positive" for e in relevant)
    delivered_negative = sum(e["event_type"] == "delivery_negative" for e in relevant)
    rejected = sum(e["event_type"] == "lead_rejected" for e in relevant)

    # Blend small samples with conservative priors so one lucky reply does not
    # immediately dominate the selection.
    lead_alpha = len(qualified) / (len(qualified) + 4.0) if qualified else 0.0
    metrics: dict[str, float] = {}
    for field in METRIC_FIELDS:
        evidence_events = capability_tests if field == "capability_fit" and capability_tests else qualified
        observed = [_clamp(e.get("evidence", {}).get(field), _clamp(prior.get(field), 0.5)) for e in evidence_events
                    if field in e.get("evidence", {})]
        empirical = sum(observed) / len(observed) if observed else _clamp(prior.get(field), 0.5)
        alpha = (len(observed) / (len(observed) + 1.0)) if field == "capability_fit" and observed else lead_alpha
        metrics[field] = round((1.0 - alpha) * _clamp(prior.get(field), 0.5) + alpha * empirical, 4)

    reply_prior = _clamp(prior.get("reply_rate"), 0.18)
    sale_prior = _clamp(prior.get("sale_rate"), 0.07)
    reply_rate = (positive + negative + reply_prior * 3.0) / (outreach + 3.0)
    sale_rate = (sales + sale_prior * 6.0) / (outreach + 6.0)
    weights = load_policy()["scoring_weights"]
    weighted = (
        weights["observed_need"] * metrics["observed_need"]
        + weights["recurrence"] * metrics["recurrence"]
        + weights["capability_fit"] * metrics["capability_fit"]
        + weights["contactability"] * metrics["contactability"]
        + weights["budget_plausibility"] * metrics["budget_plausibility"]
        + weights["reply_rate"] * reply_rate
        + weights["sale_rate"] * sale_rate
        + weights["differentiation"] * metrics["differentiation"]
        - weights["risk_penalty"] * metrics["risk"]
    )
    return {
        "niche_id": niche["id"],
        "name": niche["name"],
        "score": round(max(0.0, min(100.0, weighted * 100.0)), 2),
        "metrics": metrics,
        "qualified_leads": len(qualified),
        "research_cycles": research_cycles,
        "capability_tests": len(capability_tests),
        "outreach_sent": outreach,
        "positive_replies": positive,
        "negative_replies": negative,
        "reply_rate": round((positive + negative) / outreach, 4) if outreach else None,
        "positive_reply_rate": round(positive / outreach, 4) if outreach else None,
        "sales": sales,
        "sale_rate": round(sales / outreach, 4) if outreach else None,
        "delivery_feedback": {"positive": delivered_positive, "negative": delivered_negative},
        "rejected_leads": rejected,
        "last_event_at": relevant[-1]["created_at"] if relevant else None,
        "score_basis": "market_and_capability_evidence" if (qualified or outreach or capability_tests) else "prior_only_hypothesis",
        "has_observed_market_evidence": bool(qualified or outreach or sales),
        "has_capability_evidence": bool(capability_tests or sales or delivered_positive),
    }


def _days_since(iso_value: str | None) -> int:
    if not iso_value:
        return 0
    try:
        dt = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0, (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).days)
    except ValueError:
        return 0


def _niche_detail(niche: dict[str, Any], stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": niche["id"],
        "name": niche["name"],
        "offer_angle": niche["offer_angle"],
        "customer_problem": niche["customer_problem"],
        "signals_to_verify": niche["signals_to_verify"],
        "search_queries": niche["search_queries"],
        "buyer_segment": niche.get("buyer_segment"),
        "required_capabilities": niche.get("required_capabilities", []),
        "capability_test": niche.get("capability_test"),
        "visual_direction": niche.get("visual_direction"),
        "stats": stats,
    }


def _maybe_switch(conn: sqlite3.Connection, policy: dict[str, Any], niches: dict[str, dict[str, Any]],
                  stats: dict[str, dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
    rules = policy["focus_rules"]
    if state.get("phase") == "initial_scan":
        return state
    initial_candidates = _initial_candidate_ids(policy)
    current_id = state["active_niche_id"] if state.get("active_niche_id") in niches else initial_candidates[0]
    current = stats[current_id]
    enough_sample = (
        current["qualified_leads"] >= rules["minimum_qualified_leads_before_review"]
        and current["outreach_sent"] >= rules["minimum_personalized_outreach_before_review"]
        and _days_since(state.get("selected_at")) >= rules["minimum_days_before_switch"]
    )
    if not enough_sample:
        return state

    # Only consider an alternative after it has both verified leads and actual
    # outreach data. Prior assumptions alone cannot replace the active niche.
    alternatives = []
    for niche_id, item in stats.items():
        if niche_id == current_id:
            continue
        has_capability_proof = item.get("capability_tests", 0) > 0 or item.get("sales", 0) > 0 or item.get("delivery_feedback", {}).get("positive", 0) > 0
        if (item["qualified_leads"] >= rules["minimum_alternative_qualified_leads_before_switch"]
                and item["outreach_sent"] >= rules["minimum_alternative_outreach_before_switch"]
                and has_capability_proof):
            alternatives.append(item)
    if not alternatives:
        state["phase"] = "review_ready_no_comparable_alternative"
        return state

    best = max(alternatives, key=lambda x: x["score"])
    margin = best["score"] - current["score"]
    if margin >= rules["switch_score_margin_points"]:
        now = datetime.now(timezone.utc).isoformat()
        reason = (f"Focus changed after comparable evidence: {best['name']} leads by {margin:.1f} score points; "
                  f"current niche reply rate={current['reply_rate']}, alternative reply rate={best['reply_rate']}. "
                  "The decision uses qualified leads and personalized outreach, not priors alone.")
        candidate_scan_json = state.get("candidate_scan_json", "[]")
        conn.execute(
            "UPDATE market_strategy_state SET active_niche_id=?, selected_at=?, phase='validation', reason=?, last_review_at=? WHERE id=1",
            (best["niche_id"], now, reason, now),
        )
        conn.commit()
        state = {"id": 1, "active_niche_id": best["niche_id"], "selected_at": now,
                 "phase": "validation", "reason": reason, "last_review_at": now,
                 "candidate_scan_json": candidate_scan_json}
    else:
        now = datetime.now(timezone.utc).isoformat()
        state["phase"] = "focused_test_continue"
        state["last_review_at"] = now
        state["reason"] = "Minimum sample reached; no evidence-backed alternative met the switch threshold. Continue primary test and refine offer."
        conn.execute("UPDATE market_strategy_state SET phase=?, reason=?, last_review_at=? WHERE id=1",
                     (state["phase"], state["reason"], now))
        conn.commit()
    return state


def _maybe_finish_initial_scan(conn: sqlite3.Connection, policy: dict[str, Any],
                               stats: dict[str, dict[str, Any]], state: dict[str, Any],
                               candidate_ids: list[str]) -> dict[str, Any]:
    if state.get("phase") != "initial_scan" or not candidate_ids:
        return state
    minimum = max(1, int(policy.get("selection", {}).get("minimum_qualified_leads_per_candidate", 3)))
    minimum_tests = max(1, int(policy.get("selection", {}).get("minimum_capability_tests_per_candidate", 1)))
    if not all(
        stats.get(niche_id, {}).get("qualified_leads", 0) >= minimum
        and stats.get(niche_id, {}).get("capability_tests", 0) >= minimum_tests
        for niche_id in candidate_ids
    ):
        return state
    best = max((stats[niche_id] for niche_id in candidate_ids), key=lambda item: item["score"])
    now = datetime.now(timezone.utc).isoformat()
    reason = (f"Comparative scan complete: each of {len(candidate_ids)} offer-buyer hypotheses has at least {minimum} "
              f"qualified observed leads and a recorded capability test. {best['name']} is the leading hypothesis; personalized outreach and sales "
              "results are still required before calling the market validated.")
    conn.execute(
        "UPDATE market_strategy_state SET active_niche_id=?, selected_at=?, phase='validation', reason=?, last_review_at=? WHERE id=1",
        (best["niche_id"], now, reason, now),
    )
    conn.commit()
    state = dict(state)
    state.update({"active_niche_id": best["niche_id"], "selected_at": now,
                  "phase": "validation", "reason": reason, "last_review_at": now})
    return state


def snapshot(conn: sqlite3.Connection) -> dict[str, Any]:
    ensure_schema(conn)
    policy = load_policy()
    niches = _niches_by_id(policy)
    events = _event_rows(conn)
    stat_map = {niche_id: _event_metrics(niche, events) for niche_id, niche in niches.items()}
    state_row = conn.execute("SELECT * FROM market_strategy_state WHERE id=1").fetchone()
    state = dict(state_row) if state_row else {}
    try:
        candidate_ids = [x for x in json.loads(state.get("candidate_scan_json") or "[]") if x in niches]
    except (TypeError, json.JSONDecodeError):
        candidate_ids = []
    if not candidate_ids:
        candidate_ids = _initial_candidate_ids(policy)
    state = _maybe_finish_initial_scan(conn, policy, stat_map, state, candidate_ids)
    state = _maybe_switch(conn, policy, niches, stat_map, state)
    active_candidates = [niches[nid] for nid in candidate_ids if nid in niches]
    scan_minimum = max(1, int(policy.get("selection", {}).get("minimum_qualified_leads_per_candidate", 3)))
    scan_details = []
    if state.get("phase") == "initial_scan":
        active_candidates.sort(key=lambda niche: (stat_map[niche["id"]].get("research_cycles", 0), stat_map[niche["id"]]["qualified_leads"], niche["id"]))
    for niche in active_candidates:
        detail = _niche_detail(niche, stat_map[niche["id"]])
        lead_ready = detail["stats"]["qualified_leads"] >= scan_minimum
        test_ready = detail["stats"].get("capability_tests", 0) >= max(1, int(policy.get("selection", {}).get("minimum_capability_tests_per_candidate", 1)))
        detail["scan_status"] = "sample_ready" if (lead_ready and test_ready) else ("needs_capability_test" if lead_ready and not test_ready else "needs_more_observations")
        detail["qualified_leads_needed"] = max(0, scan_minimum - detail["stats"]["qualified_leads"])
        detail["capability_test_needed"] = not test_ready
        scan_details.append(detail)
    active_id = state.get("active_niche_id") if state.get("active_niche_id") in niches else candidate_ids[0]
    active_niche = _niche_detail(niches[active_id], stat_map[active_id])
    focus_rules = policy["focus_rules"]
    enough = (stat_map[active_id]["qualified_leads"] >= focus_rules["minimum_qualified_leads_before_review"]
              and stat_map[active_id]["outreach_sent"] >= focus_rules["minimum_personalized_outreach_before_review"])
    offer = policy["offer"]
    return {
        "strategy": policy["strategy"],
        "decision_space": "offer_x_buyer_segment",
        "phase": state.get("phase", "initial_scan"),
        "active_niche": active_niche,
        "active_since": state.get("selected_at"),
        "focus_reason": state.get("reason") or "Initial comparative scan; no niche has been validated.",
        "offer_hypothesis": None if state.get("phase", "initial_scan") == "initial_scan" else offer,
        "offer_selection_guidance": offer,
        "experiment": {
            "minimum_capability_tests_per_candidate": policy.get("selection", {}).get("minimum_capability_tests_per_candidate", 1),
            "minimum_qualified_leads": focus_rules["minimum_qualified_leads_before_review"],
            "minimum_personalized_outreach": focus_rules["minimum_personalized_outreach_before_review"],
            "current_sample_complete": enough,
            "effort_allocation": {
                "primary_niche": focus_rules["primary_effort_share"],
                "adjacent_research": focus_rules["adjacent_research_share"],
                "capability_and_offer_improvement": focus_rules["capability_and_offer_improvement_share"],
            },
        },
        "candidate_scan": scan_details,
        "candidate_scan_complete": all(x["scan_status"] == "sample_ready" for x in scan_details),
        "candidate_scores": sorted(stat_map.values(), key=lambda item: item["score"], reverse=True),
        "recording_tool": "python tools/market.py --record-json '{...}'",
        "must_not_claim_validated_before_evidence": True,
        "score_interpretation": "Prior-only scores decide research order, never proof of market demand.",
        "research_recording_contract": "Record research_cycle with source_urls and a factual summary; qualified_lead also requires source URLs, observed need, contactability and an observed permitted channel.",
    }

def record_event(conn: sqlite3.Connection, item: dict[str, Any]) -> dict[str, Any]:
    ensure_schema(conn)
    policy = load_policy()
    niches = _niches_by_id(policy)
    niche_id = str(item.get("niche_id") or "")
    event_type = str(item.get("event_type") or "")
    if niche_id not in niches:
        raise ValueError(f"unknown_niche_id: {niche_id}")
    if event_type not in VALID_EVENTS:
        raise ValueError(f"invalid_event_type: {event_type}")
    evidence = item.get("evidence") or {}
    if not isinstance(evidence, dict):
        raise ValueError("evidence_must_be_object")
    # Keep records short and factual; do not store unnecessary personal data.
    allowed_evidence = set(METRIC_FIELDS) | {
        "reason", "public_evidence_url", "source_urls", "service_observed", "offer_observed",
        "contact_channel_observed", "outcome", "amount_brl", "delivery_hours",
        "source_count", "qualified_count", "contradicting_signal",
    }
    filtered = {k: v for k, v in evidence.items() if k in allowed_evidence}
    source_urls = filtered.get("source_urls") or []
    if isinstance(source_urls, str):
        source_urls = [source_urls]
    if not isinstance(source_urls, list):
        source_urls = []
    if filtered.get("public_evidence_url"):
        source_urls = [filtered["public_evidence_url"], *source_urls]
    normalized_urls = []
    for url in source_urls:
        candidate = str(url).strip()[:600]
        if candidate.startswith(("https://", "http://")) and candidate not in normalized_urls:
            normalized_urls.append(candidate)
        if len(normalized_urls) >= 8:
            break
    if normalized_urls:
        filtered["source_urls"] = normalized_urls
        filtered["public_evidence_url"] = normalized_urls[0]
    else:
        filtered.pop("source_urls", None)
        filtered.pop("public_evidence_url", None)
    if "reason" in filtered:
        filtered["reason"] = str(filtered["reason"]).strip()[:1200]
    for field in ("service_observed", "offer_observed", "contact_channel_observed", "outcome", "contradicting_signal"):
        if field in filtered:
            filtered[field] = str(filtered[field]).strip()[:600]
    for field in METRIC_FIELDS:
        if field in filtered:
            filtered[field] = _clamp(filtered[field])
    if event_type == "research_cycle":
        if not normalized_urls or not filtered.get("reason"):
            raise ValueError("research_cycle_requires_source_urls_and_factual_summary")
    elif event_type == "qualified_lead":
        required = ("source_urls", "reason", "observed_need", "contactability", "contact_channel_observed")
        missing = [field for field in required if not filtered.get(field)]
        if missing:
            raise ValueError("qualified_lead_missing_evidence:" + ",".join(missing))
    elif event_type == "capability_tested":
        if "capability_fit" not in filtered or not filtered.get("reason"):
            raise ValueError("capability_tested_requires_fit_score_and_test_result")
    external_ref = str(item.get("external_ref") or "").strip()[:600] or None
    try:
        cur = conn.execute(
            "INSERT INTO market_niche_observations(niche_id,event_type,external_ref,evidence_json,created_at) VALUES(?,?,?,?,?)",
            (niche_id, event_type, external_ref, json.dumps(filtered, ensure_ascii=False),
             datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        inserted = True
        event_id = cur.lastrowid
    except sqlite3.IntegrityError:
        inserted = False
        row = conn.execute(
            "SELECT id FROM market_niche_observations WHERE niche_id=? AND event_type=? AND external_ref=?",
            (niche_id, event_type, external_ref),
        ).fetchone()
        event_id = row["id"] if row else None
    result = snapshot(conn)
    result["record"] = {"inserted": inserted, "event_id": event_id, "niche_id": niche_id, "event_type": event_type}
    return result


def default_market_plan() -> dict[str, Any]:
    """Build an initial comparative scan; do not hard-code a profession as winner."""
    policy = load_policy()
    niches = _niches_by_id(policy)
    ids = _initial_candidate_ids(policy)
    stats = {nid: _event_metrics(niches[nid], []) for nid in niches}
    scan = []
    for niche_id in ids:
        item = _niche_detail(niches[niche_id], stats[niche_id])
        item["scan_status"] = "needs_more_observations"
        item["qualified_leads_needed"] = policy["selection"]["minimum_qualified_leads_per_candidate"]
        scan.append(item)
    active = scan[0]
    return {
        "strategy": policy["strategy"],
        "decision_space": "offer_x_buyer_segment",
        "phase": "initial_scan",
        "active_niche": active,
        "candidate_scan": scan,
        "candidate_scan_complete": False,
        "offer_hypothesis": None,
        "offer_selection_guidance": policy["offer"],
        "research_recording_contract": "Record research_cycle with source_urls and a factual summary; qualified_lead also requires source URLs, observed need, contactability and an observed permitted channel.",
        "experiment": {
            "minimum_capability_tests_per_candidate": policy.get("selection", {}).get("minimum_capability_tests_per_candidate", 1),
            "minimum_qualified_leads": policy["focus_rules"]["minimum_qualified_leads_before_review"],
            "minimum_personalized_outreach": policy["focus_rules"]["minimum_personalized_outreach_before_review"],
            "current_sample_complete": False,
            "effort_allocation": {"primary_niche": policy["focus_rules"]["primary_effort_share"], "adjacent_research": policy["focus_rules"]["adjacent_research_share"], "capability_and_offer_improvement": policy["focus_rules"]["capability_and_offer_improvement_share"]},
        },
        "candidate_scores": sorted(stats.values(), key=lambda item: item["score"], reverse=True),
        "focus_reason": "Provisional research order only; compare all selected offer × buyer hypotheses with public evidence before selecting a primary sales focus.",
        "must_not_claim_validated_before_evidence": True,
        "score_interpretation": "Prior-only scores decide research order, never proof of market demand.",
    }
