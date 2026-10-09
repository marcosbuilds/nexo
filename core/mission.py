"""Mission layer: the worker owns outcomes, not a pile of disconnected tasks."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass
class Mission:
    title: str
    objective: str
    goal_id: int | None = None
    economic_value: float = 0.0
    probability_of_success: float = 0.5
    strategic_value: float = 0.5
    recurrence_potential: float = 0.0
    expected_minutes: float = 30.0
    expected_cost: float = 0.0
    risk: float = 0.0
    uncertainty: float = 0.0
    context_switch_cost: float = 0.0
    human_dependency: float = 0.0
    deadline_at: str | None = None
    success_condition: str | None = None
    owner_dependency: str | None = None
    current_state: str = "candidate"
    next_action: str | None = None
    priority: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def expected_profit(self) -> float:
        return max(0.0, self.economic_value - self.expected_cost)

    def utility(self) -> float:
        base = (
            self.expected_profit
            * clamp(self.probability_of_success)
            * (0.75 + clamp(self.strategic_value) * 0.75)
            * (1.0 + clamp(self.recurrence_potential) * 0.60)
        )
        denominator = max(1.0, self.expected_minutes)
        penalty = (
            self.risk * 0.30
            + self.uncertainty * 0.25
            + self.context_switch_cost * 0.20
            + self.human_dependency * 0.80
        )
        urgency_bonus = 0.0
        if self.deadline_at:
            try:
                dt = datetime.fromisoformat(self.deadline_at.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                remaining_h = (dt - now).total_seconds() / 3600
                if remaining_h <= 0:
                    urgency_bonus = 2.0
                elif remaining_h <= 24:
                    urgency_bonus = 1.0
                elif remaining_h <= 72:
                    urgency_bonus = 0.35
            except ValueError:
                pass
        return max(0.0, (base / denominator) + urgency_bonus - penalty)

    def materialize_priority(self) -> dict[str, Any]:
        self.priority = round(self.utility(), 6)
        return asdict(self) | {"expected_profit": round(self.expected_profit, 2), "utility": self.priority}


def rank(missions: list[Mission]) -> list[Mission]:
    for mission in missions:
        mission.materialize_priority()
    return sorted(missions, key=lambda item: item.priority, reverse=True)


def generate_default_missions(state: dict[str, Any]) -> list[Mission]:
    """Create candidate work from world state without requiring a human task."""
    missions: list[Mission] = []
    active_jobs = state.get("active_jobs") or []
    pending = state.get("pending_outcomes") or []
    conversations = state.get("conversation_queue") or []
    opportunities = state.get("qualified_opportunities") or []
    demand = state.get("demand_signals") or []
    partnerships = state.get("partnership_signals") or []

    for job in active_jobs[:8]:
        missions.append(Mission(
            title=f"Entregar/avançar trabalho #{job.get('id', '?')}",
            objective="Produzir o próximo resultado verificável do trabalho aceito.",
            economic_value=float(job.get("value", 0) or 0),
            probability_of_success=clamp(float(job.get("execution_confidence", 0.8))),
            strategic_value=0.8,
            expected_minutes=float(job.get("next_minutes", 45) or 45),
            deadline_at=job.get("deadline"),
            success_condition="resultado do escopo atual verificado",
            next_action="execute_active_job",
            current_state="active_job",
            metadata={"job_id": job.get("id")},
        ))

    for item in pending[:8]:
        missions.append(Mission(
            title=f"Verificar consequência: {item.get('label', 'ação externa')}",
            objective="Confirmar o efeito real de uma ação já executada antes de assumir sucesso.",
            economic_value=float(item.get("economic_value", 20) or 20),
            probability_of_success=0.9,
            strategic_value=0.7,
            expected_minutes=float(item.get("minutes", 10) or 10),
            risk=0.05,
            next_action="verify_external_outcome",
            current_state="pending_consequence",
            metadata={"action_id": item.get("action_id")},
        ))

    for item in conversations[:10]:
        missions.append(Mission(
            title=f"Avançar conversa: {item.get('name', 'contato')}",
            objective=item.get("objective") or "Levar a conversa ao menor próximo estado útil, inclusive decidir não responder.",
            economic_value=float(item.get("economic_value", 0) or 0),
            probability_of_success=clamp(float(item.get("reply_probability", 0.5))),
            strategic_value=clamp(float(item.get("strategic_value", 0.5))),
            recurrence_potential=clamp(float(item.get("recurrence", 0.2))),
            expected_minutes=float(item.get("minutes", 8) or 8),
            risk=clamp(float(item.get("risk", 0.05))),
            next_action="triage_and_plan_conversation",
            current_state="conversation",
            metadata={"conversation_id": item.get("conversation_id")},
        ))

    for item in opportunities[:10]:
        missions.append(Mission(
            title=f"Avaliar oportunidade: {item.get('title', 'oportunidade')}",
            objective="Aplicar a menor rota válida para converter a oportunidade em trabalho real.",
            economic_value=float(item.get("value", item.get("budget", 0)) or 0),
            probability_of_success=clamp(float(item.get("close_probability", 0.25))),
            strategic_value=clamp(float(item.get("strategic_value", 0.5))),
            recurrence_potential=clamp(float(item.get("recurrence", 0.1))),
            expected_minutes=float(item.get("minutes", 25) or 25),
            expected_cost=float(item.get("cost", 0) or 0),
            risk=clamp(float(item.get("risk", 0.15))),
            next_action="choose_opportunity_route",
            current_state="qualified_opportunity",
            metadata={"opportunity_id": item.get("id")},
        ))

    for item in demand[:8]:
        missions.append(Mission(
            title=f"Encontrar demanda: {item.get('segment', 'mercado')}",
            objective="Pesquisar demanda legítima e criar oportunidades acionáveis, não apenas produzir atividade.",
            economic_value=float(item.get("potential_value", 100) or 100),
            probability_of_success=clamp(float(item.get("probability", 0.15))),
            strategic_value=0.6,
            recurrence_potential=clamp(float(item.get("recurrence", 0.25))),
            expected_minutes=float(item.get("minutes", 30) or 30),
            risk=0.1,
            uncertainty=0.3,
            next_action="research_and_score_market",
            current_state="demand_generation",
            metadata={
                "source": item.get("source"),
                "hypothesis": item.get("hypothesis"),
                "niche_id": item.get("niche_id"),
                "research_mode": item.get("research_mode", "general_demand_discovery"),
                "queries": item.get("queries") or ["demanda real por serviços contratáveis", "empresas com necessidade observável", "opções de serviço com evidência de orçamento"],
                "signals_to_verify": item.get("signals_to_verify") or [],
                "success_condition": item.get("success_condition") or "Retornar evidência pública concreta, URLs e dúvidas que ainda precisam ser verificadas.",
                "avoid_generic_market_claims": True,
                "market_decision_space": "offer_x_buyer_segment",
                "required_capabilities": item.get("required_capabilities") or [],
                "capability_test": item.get("capability_test"),
                "research_cycles_observed": int(item.get("research_cycles", 0) or 0),
                "qualified_leads_observed": int(item.get("qualified_leads", 0) or 0),
                "recording_tool": item.get("recording_tool") or "python tools/market.py --record-json '{...}'",
                "research_recording_contract": "After each completed candidate/source batch record event_type=research_cycle with a stable external_ref, public URLs and concise factual evidence. Record event_type=qualified_lead only when the business, need, public evidence and allowed contact channel are verified. Never record a search result alone as a qualified lead.",
                "capability_test_contract": "Before selling or promising the offer, run the defined low-cost sample test. Record event_type=capability_tested with a capability_fit score from 0 to 1 and evidence of the test output. Do not mark delivery capability as verified based on a prompt or assumption alone.",
            },
        ))

    for item in partnerships[:6]:
        missions.append(Mission(
            title=f"Construir parceria: {item.get('name', 'parceiro')}",
            objective="Testar uma parceria mutuamente útil que possa gerar demanda recorrente.",
            economic_value=float(item.get("potential_value", 250) or 250),
            probability_of_success=clamp(float(item.get("probability", 0.12))),
            strategic_value=0.9,
            recurrence_potential=0.8,
            expected_minutes=float(item.get("minutes", 25) or 25),
            risk=0.1,
            uncertainty=0.35,
            next_action="research_partner_and_propose",
            current_state="partnership",
            metadata={"partner_ref": item.get("ref")},
        ))

    if not missions:
        missions.append(Mission(
            title="Gerar nova frente de trabalho",
            objective="Pesquisar a web e encontrar uma demanda compatível com as capacidades disponíveis.",
            economic_value=100,
            probability_of_success=0.12,
            strategic_value=0.7,
            recurrence_potential=0.3,
            expected_minutes=35,
            risk=0.12,
            uncertainty=0.5,
            next_action="research_and_score_market",
            current_state="idle_to_demand",
        ))
    return rank(missions)
