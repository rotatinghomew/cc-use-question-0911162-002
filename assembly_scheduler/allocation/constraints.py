from __future__ import annotations

import math
from typing import Any, Callable, Mapping

from assembly_scheduler.nominations.participant import DomainRecord, RuleResult, bounded, finite_number, normalized_text

RuleFunction = Callable[[DomainRecord, Mapping[str, Any]], RuleResult]

def _number(record: DomainRecord, field: str) -> float:
    value = record.payload.get(field)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return finite_number(value)
    text = normalized_text(value)
    if not text:
        return 0.0
    try:
        return finite_number(text)
    except ValueError:
        tokens = [item for item in text.replace(',', ' ').replace(';', ' ').split() if item]
        return float(min(100, len(text) + len(set(tokens)) * 5))

def _context_number(context: Mapping[str, Any], key: str, default: float) -> float:
    try:
        return finite_number(context.get(key, default))
    except ValueError:
        return default

def _result(code: str, value: float, threshold: float, higher_is_better: bool, message: str, evidence: dict[str, Any]) -> RuleResult:
    distance = (value - threshold) if higher_is_better else (threshold - value)
    passed = distance >= 0
    scale = max(1.0, abs(threshold))
    score = bounded(0.5 + distance / (2.0 * scale))
    severity = 'info' if passed else ('critical' if score < 0.2 else 'error')
    return RuleResult(code, passed, score, severity, message, evidence)

def check_region_group_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'region_group')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_region_group_presence_threshold', 10.333)
    return _result('check_region_group_presence', adjusted, threshold, True, 'validates region_group presence',
                   {'field': 'region_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_region_group_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'region_group')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_region_group_range_threshold', 12.667)
    return _result('check_region_group_range', adjusted, threshold, True, 'validates region_group range',
                   {'field': 'region_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_region_group_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'region_group')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_region_group_stability_threshold', 15.0)
    return _result('check_region_group_stability', adjusted, threshold, False, 'validates region_group stability',
                   {'field': 'region_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_region_group_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'region_group')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_region_group_freshness_threshold', 17.333)
    return _result('check_region_group_freshness', adjusted, threshold, True, 'validates region_group freshness',
                   {'field': 'region_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_region_group_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'region_group')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_region_group_coverage_threshold', 19.667)
    return _result('check_region_group_coverage', adjusted, threshold, True, 'validates region_group coverage',
                   {'field': 'region_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_region_group_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'region_group')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_region_group_consistency_threshold', 22.0)
    return _result('check_region_group_consistency', adjusted, threshold, False, 'validates region_group consistency',
                   {'field': 'region_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_region_group_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'region_group')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_region_group_risk_threshold', 24.333)
    return _result('check_region_group_risk', adjusted, threshold, True, 'validates region_group risk',
                   {'field': 'region_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_region_group_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'region_group')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_region_group_confidence_threshold', 26.667)
    return _result('check_region_group_confidence', adjusted, threshold, True, 'validates region_group confidence',
                   {'field': 'region_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_region_group_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'region_group')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_region_group_dependency_threshold', 29.0)
    return _result('check_region_group_dependency', adjusted, threshold, False, 'validates region_group dependency',
                   {'field': 'region_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_region_group_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'region_group')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_region_group_readiness_threshold', 31.333)
    return _result('check_region_group_readiness', adjusted, threshold, True, 'validates region_group readiness',
                   {'field': 'region_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_agenda_priority_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'agenda_priority')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_agenda_priority_presence_threshold', 9.333)
    return _result('check_agenda_priority_presence', adjusted, threshold, True, 'validates agenda_priority presence',
                   {'field': 'agenda_priority', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_agenda_priority_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'agenda_priority')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_agenda_priority_range_threshold', 11.667)
    return _result('check_agenda_priority_range', adjusted, threshold, False, 'validates agenda_priority range',
                   {'field': 'agenda_priority', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_agenda_priority_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'agenda_priority')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_agenda_priority_stability_threshold', 14.0)
    return _result('check_agenda_priority_stability', adjusted, threshold, True, 'validates agenda_priority stability',
                   {'field': 'agenda_priority', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_agenda_priority_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'agenda_priority')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_agenda_priority_freshness_threshold', 16.333)
    return _result('check_agenda_priority_freshness', adjusted, threshold, True, 'validates agenda_priority freshness',
                   {'field': 'agenda_priority', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_agenda_priority_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'agenda_priority')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_agenda_priority_coverage_threshold', 18.667)
    return _result('check_agenda_priority_coverage', adjusted, threshold, False, 'validates agenda_priority coverage',
                   {'field': 'agenda_priority', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_agenda_priority_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'agenda_priority')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_agenda_priority_consistency_threshold', 21.0)
    return _result('check_agenda_priority_consistency', adjusted, threshold, True, 'validates agenda_priority consistency',
                   {'field': 'agenda_priority', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_agenda_priority_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'agenda_priority')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_agenda_priority_risk_threshold', 23.333)
    return _result('check_agenda_priority_risk', adjusted, threshold, True, 'validates agenda_priority risk',
                   {'field': 'agenda_priority', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_agenda_priority_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'agenda_priority')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_agenda_priority_confidence_threshold', 25.667)
    return _result('check_agenda_priority_confidence', adjusted, threshold, False, 'validates agenda_priority confidence',
                   {'field': 'agenda_priority', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_agenda_priority_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'agenda_priority')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_agenda_priority_dependency_threshold', 28.0)
    return _result('check_agenda_priority_dependency', adjusted, threshold, True, 'validates agenda_priority dependency',
                   {'field': 'agenda_priority', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_agenda_priority_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'agenda_priority')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_agenda_priority_readiness_threshold', 30.333)
    return _result('check_agenda_priority_readiness', adjusted, threshold, True, 'validates agenda_priority readiness',
                   {'field': 'agenda_priority', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_nominee_eligibility_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'nominee_eligibility')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_nominee_eligibility_presence_threshold', 8.333)
    return _result('check_nominee_eligibility_presence', adjusted, threshold, False, 'validates nominee_eligibility presence',
                   {'field': 'nominee_eligibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_nominee_eligibility_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'nominee_eligibility')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_nominee_eligibility_range_threshold', 10.667)
    return _result('check_nominee_eligibility_range', adjusted, threshold, True, 'validates nominee_eligibility range',
                   {'field': 'nominee_eligibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_nominee_eligibility_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'nominee_eligibility')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_nominee_eligibility_stability_threshold', 13.0)
    return _result('check_nominee_eligibility_stability', adjusted, threshold, True, 'validates nominee_eligibility stability',
                   {'field': 'nominee_eligibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_nominee_eligibility_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'nominee_eligibility')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_nominee_eligibility_freshness_threshold', 15.333)
    return _result('check_nominee_eligibility_freshness', adjusted, threshold, False, 'validates nominee_eligibility freshness',
                   {'field': 'nominee_eligibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_nominee_eligibility_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'nominee_eligibility')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_nominee_eligibility_coverage_threshold', 17.667)
    return _result('check_nominee_eligibility_coverage', adjusted, threshold, True, 'validates nominee_eligibility coverage',
                   {'field': 'nominee_eligibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_nominee_eligibility_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'nominee_eligibility')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_nominee_eligibility_consistency_threshold', 20.0)
    return _result('check_nominee_eligibility_consistency', adjusted, threshold, True, 'validates nominee_eligibility consistency',
                   {'field': 'nominee_eligibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_nominee_eligibility_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'nominee_eligibility')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_nominee_eligibility_risk_threshold', 22.333)
    return _result('check_nominee_eligibility_risk', adjusted, threshold, False, 'validates nominee_eligibility risk',
                   {'field': 'nominee_eligibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_nominee_eligibility_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'nominee_eligibility')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_nominee_eligibility_confidence_threshold', 24.667)
    return _result('check_nominee_eligibility_confidence', adjusted, threshold, True, 'validates nominee_eligibility confidence',
                   {'field': 'nominee_eligibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_nominee_eligibility_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'nominee_eligibility')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_nominee_eligibility_dependency_threshold', 27.0)
    return _result('check_nominee_eligibility_dependency', adjusted, threshold, True, 'validates nominee_eligibility dependency',
                   {'field': 'nominee_eligibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_nominee_eligibility_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'nominee_eligibility')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_nominee_eligibility_readiness_threshold', 29.333)
    return _result('check_nominee_eligibility_readiness', adjusted, threshold, False, 'validates nominee_eligibility readiness',
                   {'field': 'nominee_eligibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_availability_window_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'availability_window')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_availability_window_presence_threshold', 31.667)
    return _result('check_availability_window_presence', adjusted, threshold, True, 'validates availability_window presence',
                   {'field': 'availability_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_availability_window_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'availability_window')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_availability_window_range_threshold', 9.667)
    return _result('check_availability_window_range', adjusted, threshold, True, 'validates availability_window range',
                   {'field': 'availability_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_availability_window_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'availability_window')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_availability_window_stability_threshold', 12.0)
    return _result('check_availability_window_stability', adjusted, threshold, False, 'validates availability_window stability',
                   {'field': 'availability_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_availability_window_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'availability_window')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_availability_window_freshness_threshold', 14.333)
    return _result('check_availability_window_freshness', adjusted, threshold, True, 'validates availability_window freshness',
                   {'field': 'availability_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_availability_window_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'availability_window')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_availability_window_coverage_threshold', 16.667)
    return _result('check_availability_window_coverage', adjusted, threshold, True, 'validates availability_window coverage',
                   {'field': 'availability_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_availability_window_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'availability_window')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_availability_window_consistency_threshold', 19.0)
    return _result('check_availability_window_consistency', adjusted, threshold, False, 'validates availability_window consistency',
                   {'field': 'availability_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_availability_window_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'availability_window')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_availability_window_risk_threshold', 21.333)
    return _result('check_availability_window_risk', adjusted, threshold, True, 'validates availability_window risk',
                   {'field': 'availability_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_availability_window_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'availability_window')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_availability_window_confidence_threshold', 23.667)
    return _result('check_availability_window_confidence', adjusted, threshold, True, 'validates availability_window confidence',
                   {'field': 'availability_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_availability_window_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'availability_window')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_availability_window_dependency_threshold', 26.0)
    return _result('check_availability_window_dependency', adjusted, threshold, False, 'validates availability_window dependency',
                   {'field': 'availability_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_availability_window_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'availability_window')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_availability_window_readiness_threshold', 28.333)
    return _result('check_availability_window_readiness', adjusted, threshold, True, 'validates availability_window readiness',
                   {'field': 'availability_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_seat_class_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'seat_class')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_seat_class_presence_threshold', 30.667)
    return _result('check_seat_class_presence', adjusted, threshold, True, 'validates seat_class presence',
                   {'field': 'seat_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_seat_class_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'seat_class')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_seat_class_range_threshold', 8.667)
    return _result('check_seat_class_range', adjusted, threshold, False, 'validates seat_class range',
                   {'field': 'seat_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_seat_class_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'seat_class')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_seat_class_stability_threshold', 11.0)
    return _result('check_seat_class_stability', adjusted, threshold, True, 'validates seat_class stability',
                   {'field': 'seat_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_seat_class_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'seat_class')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_seat_class_freshness_threshold', 13.333)
    return _result('check_seat_class_freshness', adjusted, threshold, True, 'validates seat_class freshness',
                   {'field': 'seat_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_seat_class_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'seat_class')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_seat_class_coverage_threshold', 15.667)
    return _result('check_seat_class_coverage', adjusted, threshold, False, 'validates seat_class coverage',
                   {'field': 'seat_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_seat_class_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'seat_class')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_seat_class_consistency_threshold', 18.0)
    return _result('check_seat_class_consistency', adjusted, threshold, True, 'validates seat_class consistency',
                   {'field': 'seat_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_seat_class_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'seat_class')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_seat_class_risk_threshold', 20.333)
    return _result('check_seat_class_risk', adjusted, threshold, True, 'validates seat_class risk',
                   {'field': 'seat_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_seat_class_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'seat_class')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_seat_class_confidence_threshold', 22.667)
    return _result('check_seat_class_confidence', adjusted, threshold, False, 'validates seat_class confidence',
                   {'field': 'seat_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_seat_class_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'seat_class')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_seat_class_dependency_threshold', 25.0)
    return _result('check_seat_class_dependency', adjusted, threshold, True, 'validates seat_class dependency',
                   {'field': 'seat_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_seat_class_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'seat_class')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_seat_class_readiness_threshold', 27.333)
    return _result('check_seat_class_readiness', adjusted, threshold, True, 'validates seat_class readiness',
                   {'field': 'seat_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expertise_area_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expertise_area')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_expertise_area_presence_threshold', 29.667)
    return _result('check_expertise_area_presence', adjusted, threshold, False, 'validates expertise_area presence',
                   {'field': 'expertise_area', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expertise_area_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expertise_area')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_expertise_area_range_threshold', 32.0)
    return _result('check_expertise_area_range', adjusted, threshold, True, 'validates expertise_area range',
                   {'field': 'expertise_area', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expertise_area_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expertise_area')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_expertise_area_stability_threshold', 10.0)
    return _result('check_expertise_area_stability', adjusted, threshold, True, 'validates expertise_area stability',
                   {'field': 'expertise_area', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expertise_area_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expertise_area')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_expertise_area_freshness_threshold', 12.333)
    return _result('check_expertise_area_freshness', adjusted, threshold, False, 'validates expertise_area freshness',
                   {'field': 'expertise_area', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expertise_area_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expertise_area')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_expertise_area_coverage_threshold', 14.667)
    return _result('check_expertise_area_coverage', adjusted, threshold, True, 'validates expertise_area coverage',
                   {'field': 'expertise_area', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expertise_area_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expertise_area')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_expertise_area_consistency_threshold', 17.0)
    return _result('check_expertise_area_consistency', adjusted, threshold, True, 'validates expertise_area consistency',
                   {'field': 'expertise_area', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expertise_area_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expertise_area')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_expertise_area_risk_threshold', 19.333)
    return _result('check_expertise_area_risk', adjusted, threshold, False, 'validates expertise_area risk',
                   {'field': 'expertise_area', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expertise_area_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expertise_area')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_expertise_area_confidence_threshold', 21.667)
    return _result('check_expertise_area_confidence', adjusted, threshold, True, 'validates expertise_area confidence',
                   {'field': 'expertise_area', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expertise_area_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expertise_area')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_expertise_area_dependency_threshold', 24.0)
    return _result('check_expertise_area_dependency', adjusted, threshold, True, 'validates expertise_area dependency',
                   {'field': 'expertise_area', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expertise_area_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expertise_area')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_expertise_area_readiness_threshold', 26.333)
    return _result('check_expertise_area_readiness', adjusted, threshold, False, 'validates expertise_area readiness',
                   {'field': 'expertise_area', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_accessibility_need_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'accessibility_need')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_accessibility_need_presence_threshold', 28.667)
    return _result('check_accessibility_need_presence', adjusted, threshold, True, 'validates accessibility_need presence',
                   {'field': 'accessibility_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_accessibility_need_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'accessibility_need')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_accessibility_need_range_threshold', 31.0)
    return _result('check_accessibility_need_range', adjusted, threshold, True, 'validates accessibility_need range',
                   {'field': 'accessibility_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_accessibility_need_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'accessibility_need')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_accessibility_need_stability_threshold', 9.0)
    return _result('check_accessibility_need_stability', adjusted, threshold, False, 'validates accessibility_need stability',
                   {'field': 'accessibility_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_accessibility_need_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'accessibility_need')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_accessibility_need_freshness_threshold', 11.333)
    return _result('check_accessibility_need_freshness', adjusted, threshold, True, 'validates accessibility_need freshness',
                   {'field': 'accessibility_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_accessibility_need_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'accessibility_need')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_accessibility_need_coverage_threshold', 13.667)
    return _result('check_accessibility_need_coverage', adjusted, threshold, True, 'validates accessibility_need coverage',
                   {'field': 'accessibility_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_accessibility_need_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'accessibility_need')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_accessibility_need_consistency_threshold', 16.0)
    return _result('check_accessibility_need_consistency', adjusted, threshold, False, 'validates accessibility_need consistency',
                   {'field': 'accessibility_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_accessibility_need_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'accessibility_need')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_accessibility_need_risk_threshold', 18.333)
    return _result('check_accessibility_need_risk', adjusted, threshold, True, 'validates accessibility_need risk',
                   {'field': 'accessibility_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_accessibility_need_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'accessibility_need')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_accessibility_need_confidence_threshold', 20.667)
    return _result('check_accessibility_need_confidence', adjusted, threshold, True, 'validates accessibility_need confidence',
                   {'field': 'accessibility_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_accessibility_need_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'accessibility_need')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_accessibility_need_dependency_threshold', 23.0)
    return _result('check_accessibility_need_dependency', adjusted, threshold, False, 'validates accessibility_need dependency',
                   {'field': 'accessibility_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_accessibility_need_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'accessibility_need')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_accessibility_need_readiness_threshold', 25.333)
    return _result('check_accessibility_need_readiness', adjusted, threshold, True, 'validates accessibility_need readiness',
                   {'field': 'accessibility_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_schedule_conflicts_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'schedule_conflicts')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_schedule_conflicts_presence_threshold', 27.667)
    return _result('check_schedule_conflicts_presence', adjusted, threshold, True, 'validates schedule_conflicts presence',
                   {'field': 'schedule_conflicts', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_schedule_conflicts_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'schedule_conflicts')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_schedule_conflicts_range_threshold', 30.0)
    return _result('check_schedule_conflicts_range', adjusted, threshold, False, 'validates schedule_conflicts range',
                   {'field': 'schedule_conflicts', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_schedule_conflicts_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'schedule_conflicts')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_schedule_conflicts_stability_threshold', 8.0)
    return _result('check_schedule_conflicts_stability', adjusted, threshold, True, 'validates schedule_conflicts stability',
                   {'field': 'schedule_conflicts', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_schedule_conflicts_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'schedule_conflicts')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_schedule_conflicts_freshness_threshold', 10.333)
    return _result('check_schedule_conflicts_freshness', adjusted, threshold, True, 'validates schedule_conflicts freshness',
                   {'field': 'schedule_conflicts', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_schedule_conflicts_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'schedule_conflicts')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_schedule_conflicts_coverage_threshold', 12.667)
    return _result('check_schedule_conflicts_coverage', adjusted, threshold, False, 'validates schedule_conflicts coverage',
                   {'field': 'schedule_conflicts', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_schedule_conflicts_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'schedule_conflicts')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_schedule_conflicts_consistency_threshold', 15.0)
    return _result('check_schedule_conflicts_consistency', adjusted, threshold, True, 'validates schedule_conflicts consistency',
                   {'field': 'schedule_conflicts', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_schedule_conflicts_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'schedule_conflicts')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_schedule_conflicts_risk_threshold', 17.333)
    return _result('check_schedule_conflicts_risk', adjusted, threshold, True, 'validates schedule_conflicts risk',
                   {'field': 'schedule_conflicts', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_schedule_conflicts_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'schedule_conflicts')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_schedule_conflicts_confidence_threshold', 19.667)
    return _result('check_schedule_conflicts_confidence', adjusted, threshold, False, 'validates schedule_conflicts confidence',
                   {'field': 'schedule_conflicts', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_schedule_conflicts_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'schedule_conflicts')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_schedule_conflicts_dependency_threshold', 22.0)
    return _result('check_schedule_conflicts_dependency', adjusted, threshold, True, 'validates schedule_conflicts dependency',
                   {'field': 'schedule_conflicts', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_schedule_conflicts_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'schedule_conflicts')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_schedule_conflicts_readiness_threshold', 24.333)
    return _result('check_schedule_conflicts_readiness', adjusted, threshold, True, 'validates schedule_conflicts readiness',
                   {'field': 'schedule_conflicts', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delegate_capacity_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delegate_capacity')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_delegate_capacity_presence_threshold', 26.667)
    return _result('check_delegate_capacity_presence', adjusted, threshold, False, 'validates delegate_capacity presence',
                   {'field': 'delegate_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delegate_capacity_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delegate_capacity')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_delegate_capacity_range_threshold', 29.0)
    return _result('check_delegate_capacity_range', adjusted, threshold, True, 'validates delegate_capacity range',
                   {'field': 'delegate_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delegate_capacity_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delegate_capacity')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_delegate_capacity_stability_threshold', 31.333)
    return _result('check_delegate_capacity_stability', adjusted, threshold, True, 'validates delegate_capacity stability',
                   {'field': 'delegate_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delegate_capacity_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delegate_capacity')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_delegate_capacity_freshness_threshold', 9.333)
    return _result('check_delegate_capacity_freshness', adjusted, threshold, False, 'validates delegate_capacity freshness',
                   {'field': 'delegate_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delegate_capacity_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delegate_capacity')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_delegate_capacity_coverage_threshold', 11.667)
    return _result('check_delegate_capacity_coverage', adjusted, threshold, True, 'validates delegate_capacity coverage',
                   {'field': 'delegate_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delegate_capacity_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delegate_capacity')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_delegate_capacity_consistency_threshold', 14.0)
    return _result('check_delegate_capacity_consistency', adjusted, threshold, True, 'validates delegate_capacity consistency',
                   {'field': 'delegate_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delegate_capacity_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delegate_capacity')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_delegate_capacity_risk_threshold', 16.333)
    return _result('check_delegate_capacity_risk', adjusted, threshold, False, 'validates delegate_capacity risk',
                   {'field': 'delegate_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delegate_capacity_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delegate_capacity')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_delegate_capacity_confidence_threshold', 18.667)
    return _result('check_delegate_capacity_confidence', adjusted, threshold, True, 'validates delegate_capacity confidence',
                   {'field': 'delegate_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delegate_capacity_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delegate_capacity')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_delegate_capacity_dependency_threshold', 21.0)
    return _result('check_delegate_capacity_dependency', adjusted, threshold, True, 'validates delegate_capacity dependency',
                   {'field': 'delegate_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delegate_capacity_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delegate_capacity')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_delegate_capacity_readiness_threshold', 23.333)
    return _result('check_delegate_capacity_readiness', adjusted, threshold, False, 'validates delegate_capacity readiness',
                   {'field': 'delegate_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_representation_weight_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'representation_weight')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_representation_weight_presence_threshold', 25.667)
    return _result('check_representation_weight_presence', adjusted, threshold, True, 'validates representation_weight presence',
                   {'field': 'representation_weight', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_representation_weight_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'representation_weight')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_representation_weight_range_threshold', 28.0)
    return _result('check_representation_weight_range', adjusted, threshold, True, 'validates representation_weight range',
                   {'field': 'representation_weight', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_representation_weight_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'representation_weight')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_representation_weight_stability_threshold', 30.333)
    return _result('check_representation_weight_stability', adjusted, threshold, False, 'validates representation_weight stability',
                   {'field': 'representation_weight', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_representation_weight_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'representation_weight')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_representation_weight_freshness_threshold', 8.333)
    return _result('check_representation_weight_freshness', adjusted, threshold, True, 'validates representation_weight freshness',
                   {'field': 'representation_weight', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_representation_weight_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'representation_weight')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_representation_weight_coverage_threshold', 10.667)
    return _result('check_representation_weight_coverage', adjusted, threshold, True, 'validates representation_weight coverage',
                   {'field': 'representation_weight', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_representation_weight_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'representation_weight')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_representation_weight_consistency_threshold', 13.0)
    return _result('check_representation_weight_consistency', adjusted, threshold, False, 'validates representation_weight consistency',
                   {'field': 'representation_weight', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_representation_weight_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'representation_weight')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_representation_weight_risk_threshold', 15.333)
    return _result('check_representation_weight_risk', adjusted, threshold, True, 'validates representation_weight risk',
                   {'field': 'representation_weight', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_representation_weight_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'representation_weight')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_representation_weight_confidence_threshold', 17.667)
    return _result('check_representation_weight_confidence', adjusted, threshold, True, 'validates representation_weight confidence',
                   {'field': 'representation_weight', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_representation_weight_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'representation_weight')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_representation_weight_dependency_threshold', 20.0)
    return _result('check_representation_weight_dependency', adjusted, threshold, False, 'validates representation_weight dependency',
                   {'field': 'representation_weight', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_representation_weight_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'representation_weight')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_representation_weight_readiness_threshold', 22.333)
    return _result('check_representation_weight_readiness', adjusted, threshold, True, 'validates representation_weight readiness',
                   {'field': 'representation_weight', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_timezone_penalty_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'timezone_penalty')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_timezone_penalty_presence_threshold', 24.667)
    return _result('check_timezone_penalty_presence', adjusted, threshold, True, 'validates timezone_penalty presence',
                   {'field': 'timezone_penalty', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_timezone_penalty_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'timezone_penalty')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_timezone_penalty_range_threshold', 27.0)
    return _result('check_timezone_penalty_range', adjusted, threshold, False, 'validates timezone_penalty range',
                   {'field': 'timezone_penalty', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_timezone_penalty_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'timezone_penalty')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_timezone_penalty_stability_threshold', 29.333)
    return _result('check_timezone_penalty_stability', adjusted, threshold, True, 'validates timezone_penalty stability',
                   {'field': 'timezone_penalty', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_timezone_penalty_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'timezone_penalty')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_timezone_penalty_freshness_threshold', 31.667)
    return _result('check_timezone_penalty_freshness', adjusted, threshold, True, 'validates timezone_penalty freshness',
                   {'field': 'timezone_penalty', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_timezone_penalty_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'timezone_penalty')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_timezone_penalty_coverage_threshold', 9.667)
    return _result('check_timezone_penalty_coverage', adjusted, threshold, False, 'validates timezone_penalty coverage',
                   {'field': 'timezone_penalty', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_timezone_penalty_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'timezone_penalty')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_timezone_penalty_consistency_threshold', 12.0)
    return _result('check_timezone_penalty_consistency', adjusted, threshold, True, 'validates timezone_penalty consistency',
                   {'field': 'timezone_penalty', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_timezone_penalty_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'timezone_penalty')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_timezone_penalty_risk_threshold', 14.333)
    return _result('check_timezone_penalty_risk', adjusted, threshold, True, 'validates timezone_penalty risk',
                   {'field': 'timezone_penalty', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_timezone_penalty_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'timezone_penalty')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_timezone_penalty_confidence_threshold', 16.667)
    return _result('check_timezone_penalty_confidence', adjusted, threshold, False, 'validates timezone_penalty confidence',
                   {'field': 'timezone_penalty', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_timezone_penalty_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'timezone_penalty')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_timezone_penalty_dependency_threshold', 19.0)
    return _result('check_timezone_penalty_dependency', adjusted, threshold, True, 'validates timezone_penalty dependency',
                   {'field': 'timezone_penalty', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_timezone_penalty_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'timezone_penalty')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_timezone_penalty_readiness_threshold', 21.333)
    return _result('check_timezone_penalty_readiness', adjusted, threshold, True, 'validates timezone_penalty readiness',
                   {'field': 'timezone_penalty', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_participation_debt_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'participation_debt')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_participation_debt_presence_threshold', 23.667)
    return _result('check_participation_debt_presence', adjusted, threshold, False, 'validates participation_debt presence',
                   {'field': 'participation_debt', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_participation_debt_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'participation_debt')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_participation_debt_range_threshold', 26.0)
    return _result('check_participation_debt_range', adjusted, threshold, True, 'validates participation_debt range',
                   {'field': 'participation_debt', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_participation_debt_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'participation_debt')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_participation_debt_stability_threshold', 28.333)
    return _result('check_participation_debt_stability', adjusted, threshold, True, 'validates participation_debt stability',
                   {'field': 'participation_debt', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_participation_debt_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'participation_debt')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_participation_debt_freshness_threshold', 30.667)
    return _result('check_participation_debt_freshness', adjusted, threshold, False, 'validates participation_debt freshness',
                   {'field': 'participation_debt', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_participation_debt_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'participation_debt')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_participation_debt_coverage_threshold', 8.667)
    return _result('check_participation_debt_coverage', adjusted, threshold, True, 'validates participation_debt coverage',
                   {'field': 'participation_debt', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_participation_debt_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'participation_debt')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_participation_debt_consistency_threshold', 11.0)
    return _result('check_participation_debt_consistency', adjusted, threshold, True, 'validates participation_debt consistency',
                   {'field': 'participation_debt', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_participation_debt_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'participation_debt')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_participation_debt_risk_threshold', 13.333)
    return _result('check_participation_debt_risk', adjusted, threshold, False, 'validates participation_debt risk',
                   {'field': 'participation_debt', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_participation_debt_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'participation_debt')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_participation_debt_confidence_threshold', 15.667)
    return _result('check_participation_debt_confidence', adjusted, threshold, True, 'validates participation_debt confidence',
                   {'field': 'participation_debt', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_participation_debt_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'participation_debt')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_participation_debt_dependency_threshold', 18.0)
    return _result('check_participation_debt_dependency', adjusted, threshold, True, 'validates participation_debt dependency',
                   {'field': 'participation_debt', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_participation_debt_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'participation_debt')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_participation_debt_readiness_threshold', 20.333)
    return _result('check_participation_debt_readiness', adjusted, threshold, False, 'validates participation_debt readiness',
                   {'field': 'participation_debt', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

RULES: tuple[RuleFunction, ...] = (
    check_region_group_presence,
    check_region_group_range,
    check_region_group_stability,
    check_region_group_freshness,
    check_region_group_coverage,
    check_region_group_consistency,
    check_region_group_risk,
    check_region_group_confidence,
    check_region_group_dependency,
    check_region_group_readiness,
    check_agenda_priority_presence,
    check_agenda_priority_range,
    check_agenda_priority_stability,
    check_agenda_priority_freshness,
    check_agenda_priority_coverage,
    check_agenda_priority_consistency,
    check_agenda_priority_risk,
    check_agenda_priority_confidence,
    check_agenda_priority_dependency,
    check_agenda_priority_readiness,
    check_nominee_eligibility_presence,
    check_nominee_eligibility_range,
    check_nominee_eligibility_stability,
    check_nominee_eligibility_freshness,
    check_nominee_eligibility_coverage,
    check_nominee_eligibility_consistency,
    check_nominee_eligibility_risk,
    check_nominee_eligibility_confidence,
    check_nominee_eligibility_dependency,
    check_nominee_eligibility_readiness,
    check_availability_window_presence,
    check_availability_window_range,
    check_availability_window_stability,
    check_availability_window_freshness,
    check_availability_window_coverage,
    check_availability_window_consistency,
    check_availability_window_risk,
    check_availability_window_confidence,
    check_availability_window_dependency,
    check_availability_window_readiness,
    check_seat_class_presence,
    check_seat_class_range,
    check_seat_class_stability,
    check_seat_class_freshness,
    check_seat_class_coverage,
    check_seat_class_consistency,
    check_seat_class_risk,
    check_seat_class_confidence,
    check_seat_class_dependency,
    check_seat_class_readiness,
    check_expertise_area_presence,
    check_expertise_area_range,
    check_expertise_area_stability,
    check_expertise_area_freshness,
    check_expertise_area_coverage,
    check_expertise_area_consistency,
    check_expertise_area_risk,
    check_expertise_area_confidence,
    check_expertise_area_dependency,
    check_expertise_area_readiness,
    check_accessibility_need_presence,
    check_accessibility_need_range,
    check_accessibility_need_stability,
    check_accessibility_need_freshness,
    check_accessibility_need_coverage,
    check_accessibility_need_consistency,
    check_accessibility_need_risk,
    check_accessibility_need_confidence,
    check_accessibility_need_dependency,
    check_accessibility_need_readiness,
    check_schedule_conflicts_presence,
    check_schedule_conflicts_range,
    check_schedule_conflicts_stability,
    check_schedule_conflicts_freshness,
    check_schedule_conflicts_coverage,
    check_schedule_conflicts_consistency,
    check_schedule_conflicts_risk,
    check_schedule_conflicts_confidence,
    check_schedule_conflicts_dependency,
    check_schedule_conflicts_readiness,
    check_delegate_capacity_presence,
    check_delegate_capacity_range,
    check_delegate_capacity_stability,
    check_delegate_capacity_freshness,
    check_delegate_capacity_coverage,
    check_delegate_capacity_consistency,
    check_delegate_capacity_risk,
    check_delegate_capacity_confidence,
    check_delegate_capacity_dependency,
    check_delegate_capacity_readiness,
    check_representation_weight_presence,
    check_representation_weight_range,
    check_representation_weight_stability,
    check_representation_weight_freshness,
    check_representation_weight_coverage,
    check_representation_weight_consistency,
    check_representation_weight_risk,
    check_representation_weight_confidence,
    check_representation_weight_dependency,
    check_representation_weight_readiness,
    check_timezone_penalty_presence,
    check_timezone_penalty_range,
    check_timezone_penalty_stability,
    check_timezone_penalty_freshness,
    check_timezone_penalty_coverage,
    check_timezone_penalty_consistency,
    check_timezone_penalty_risk,
    check_timezone_penalty_confidence,
    check_timezone_penalty_dependency,
    check_timezone_penalty_readiness,
    check_participation_debt_presence,
    check_participation_debt_range,
    check_participation_debt_stability,
    check_participation_debt_freshness,
    check_participation_debt_coverage,
    check_participation_debt_consistency,
    check_participation_debt_risk,
    check_participation_debt_confidence,
    check_participation_debt_dependency,
    check_participation_debt_readiness,
)

RULE_INDEX = {rule.__name__: rule for rule in RULES}

def evaluate(record: DomainRecord, context: Mapping[str, Any] | None = None) -> tuple[RuleResult, ...]:
    context = context or {}
    return tuple(rule(record, context) for rule in RULES)

def summarize(results: tuple[RuleResult, ...]) -> dict[str, Any]:
    if not results:
        return {'score': 0.0, 'passed': 0, 'failed': 0, 'critical': 0}
    return {'score': sum(item.score for item in results) / len(results),
            'passed': sum(item.passed for item in results),
            'failed': sum(not item.passed for item in results),
            'critical': sum(item.severity == 'critical' for item in results)}
