"""Autonomous commercial pricing from evidence and observed economics."""
from __future__ import annotations
from statistics import median
from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def recommend_quote(data: dict[str, Any]) -> dict[str, Any]:
    hours = max(0.0, _num(data.get("hours")))
    direct_costs = max(0.0, _num(data.get("direct_costs")))
    complexity = min(1.0, max(0.0, _num(data.get("complexity"), 0.35)))
    revision_risk = min(1.0, max(0.0, _num(data.get("revision_risk"), 0.25)))
    urgency = min(1.0, max(0.0, _num(data.get("urgency"), 0.0))) if data.get("real_deadline") else 0.0
    target_profit_per_hour = _num(data.get("target_profit_per_hour"))
    observed_prices = [_num(x) for x in data.get("observed_prices", []) if _num(x) > 0]
    historical_prices = [_num(x) for x in data.get("historical_prices", []) if _num(x) > 0]
    comparable_values = observed_prices + historical_prices
    value_estimate = max(0.0, _num(data.get("customer_value_estimate")))
    closing_sensitivity = min(1.0, max(0.0, _num(data.get("closing_sensitivity"), 0.5)))

    if target_profit_per_hour <= 0:
        if data.get("owner_minimum_profit_per_hour"):
            target_profit_per_hour = max(0.0, _num(data.get("owner_minimum_profit_per_hour")))
        elif comparable_values and hours > 0:
            target_profit_per_hour = max(1.0, median(comparable_values) / hours * 0.60)
        else:
            target_profit_per_hour = max(50.0, direct_costs / max(hours, 1.0) * 2.0)

    base = max(direct_costs, hours * target_profit_per_hour)
    risk_multiplier = 1.0 + complexity * 0.25 + revision_risk * 0.20 + urgency * 0.12
    market_anchor = median(comparable_values) if comparable_values else 0.0
    value_anchor = value_estimate * (0.10 + closing_sensitivity * 0.15) if value_estimate else 0.0
    recommendation = max(base * risk_multiplier, market_anchor * 0.85 if market_anchor else 0.0, value_anchor)
    recommendation = round(recommendation, 2)
    floor = round(max(direct_costs, base * 0.80), 2)
    ceiling = round(max(recommendation * 1.25, market_anchor * 1.15 if market_anchor else 0), 2)
    if ceiling and ceiling < recommendation:
        ceiling = recommendation

    uncertainty = 0.1
    if not comparable_values:
        uncertainty += 0.25
    if hours <= 0:
        uncertainty += 0.25
    if not value_estimate:
        uncertainty += 0.10

    return {
        "recommended_price_brl": recommendation,
        "negotiation_floor_brl": floor,
        "preferred_range_brl": [round(recommendation * 0.95, 2), ceiling or round(recommendation * 1.15, 2)],
        "confidence": round(max(0.0, 1.0 - min(0.9, uncertainty)), 3),
        "market_anchor_brl": round(market_anchor, 2),
        "basis": {
            "hours": hours,
            "direct_costs": direct_costs,
            "target_profit_per_hour": round(target_profit_per_hour, 2),
            "complexity": complexity,
            "revision_risk": revision_risk,
            "urgency": urgency,
            "customer_value_estimate": value_estimate,
        },
        "decision_rule": "derive a commercially viable value from available evidence; if evidence is weak, prefer a range or gather one high-value missing fact",
    }
