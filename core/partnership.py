"""Partnership evaluation: mutually beneficial routes, not one-sided outreach."""
from __future__ import annotations
from typing import Any


def evaluate_partner(data: dict[str, Any]) -> dict[str, Any]:
    overlap=min(1,max(0,float(data.get('audience_overlap',0))))
    complement=min(1,max(0,float(data.get('complementarity',0))))
    economics=min(1,max(0,float(data.get('economic_fit',0))))
    credibility=min(1,max(0,float(data.get('trust_signal',0))))
    friction=min(1,max(0,float(data.get('friction',0))))
    value=100*(0.30*overlap+0.30*complement+0.22*economics+0.18*credibility-0.25*friction)
    kinds=data.get('possible_formats') or ['referral','cross_sell','joint_offer']
    chosen=kinds[0]
    return {
        'score':round(max(0,value),2),
        'should_approach':value>=50 and overlap>=0.35 and complement>=0.45,
        'recommended_format':chosen,
        'mutual_value':data.get('mutual_value') or 'exchange demand or capability where both sides gain',
        'opening_angle':data.get('opening_angle') or 'show the shared audience/problem and suggest one small test before proposing a broad partnership',
        'stop_condition':'no evidence of complementarity or explicit decline',
    }
