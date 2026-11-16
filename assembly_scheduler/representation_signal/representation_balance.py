from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class DomainSignal:
    code: str
    score: float
    severity: str
    evidence: dict[str, Any]

def number(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        value = float(payload.get(key, default))
    except (TypeError, ValueError):
        return default
    return default if value != value or value in (float('inf'), float('-inf')) else value

def ratio(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    value = number(payload, key, default)
    if value > 1.0:
        value /= 100.0
    return max(0.0, min(1.0, value))

def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))

def representation_balance(payload: Mapping[str, Any]) -> DomainSignal:
    weight = ratio(payload, 'representation_weight')
    eligibility = ratio(payload, 'nominee_eligibility')
    capacity = max(0.0, number(payload, 'delegate_capacity'))
    conflicts = max(0.0, number(payload, 'schedule_conflicts'))
    timezone = ratio(payload, 'timezone_penalty')
    debt = max(0.0, number(payload, 'participation_debt'))
    priority = ratio(payload, 'agenda_priority')
    feasible = clamp((capacity-conflicts) / max(1.0, capacity))
    debt_credit = min(.25, debt / 100.0)
    score = clamp(weight*.28 + eligibility*.22 + feasible*.24 + priority*.12 + (1-timezone)*.14 + debt_credit)
    severity = 'critical' if capacity <= conflicts or eligibility < .2 else 'warning' if timezone > .65 or score < .5 else 'info'
    return DomainSignal('representation_balance', score, severity, {'feasible_share': feasible, 'debt_credit': debt_credit, 'timezone_penalty': timezone, 'capacity': capacity})

def peer_distribution(records: Iterable[Any], group_field: str = 'region_group') -> dict[str, Any]:
    groups = {}
    for record in records:
        payload=getattr(record,'payload',record); groups.setdefault(str(payload.get(group_field,'unknown')),[]).append(representation_balance(payload).score)
    means={k:sum(v)/len(v) for k,v in groups.items()}; gap=max(means.values())-min(means.values()) if means else 0.0
    return {'groups':means,'count':sum(len(v) for v in groups.values()),'representation_gap':gap}

def augment_context(record: Any, repository: Any) -> dict[str, Any]:
    signal=representation_balance(record.payload); peers=peer_distribution(repository.list_records())
    return {'domain_signal':signal.score,'domain_severity':signal.severity,'representation_gap':peers['representation_gap'],'peer_count':peers['count']}
