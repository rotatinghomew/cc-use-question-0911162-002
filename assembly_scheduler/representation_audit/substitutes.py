"""Ranked, feasible substitute recommendations.

Substitutes only draw from nominations that pass every hard constraint, so a
recommendation is always operationally viable. Each recommendation states the
representation gap it would close, the constraints it satisfies and the stable
identifier used by the nomination confirmation workflow.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from assembly_scheduler.nominations.participant import DomainRecord, stable_hash
from assembly_scheduler.representation_audit.eligibility import (
    AuditSettings,
    candidate_score,
    expertise_tag,
    hard_blockers,
    is_low_income,
)
from assembly_scheduler.representation_audit.gap_report import (
    DIMENSION_EXPERTISE_AREA,
    DIMENSION_LOW_INCOME,
    DIMENSION_REGION_GROUP,
)
from assembly_scheduler.representation_audit.seat_plan import SeatPlan

DEFAULT_LIMIT = 3
STATUS_PROPOSED = "proposed"
STATUS_PROMOTED = "promoted"
STATUS_SUPERSEDED = "superseded"


@dataclass(frozen=True)
class Substitution:
    substitution_id: str
    record_id: str
    rank: int
    score: float
    region_group: str
    expertise_tag: str
    low_income: bool
    closes_gaps: tuple[str, ...]
    satisfied_constraints: tuple[str, ...]
    status: str
    rationale: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "substitution_id": self.substitution_id,
            "record_id": self.record_id,
            "rank": self.rank,
            "score": self.score,
            "region_group": self.region_group,
            "expertise_tag": self.expertise_tag,
            "low_income": self.low_income,
            "closes_gaps": list(self.closes_gaps),
            "satisfied_constraints": list(self.satisfied_constraints),
            "status": self.status,
            "rationale": self.rationale,
        }


def _open_gap_keys(gap_report: dict[str, Any]) -> set[str]:
    return {
        f"{entry['dimension']}:{entry['bucket']}"
        for entry in gap_report.get("entries", [])
        if entry["shortfall"] > 0
    }


def _gap_keys_for_record(
    record: DomainRecord, settings: AuditSettings, open_gaps: set[str]
) -> tuple[str, ...]:
    candidates = (
        f"{DIMENSION_LOW_INCOME}:low-income" if is_low_income(record, settings) else None,
        f"{DIMENSION_REGION_GROUP}:{record.payload.get('region_group', 'unknown')}",
        f"{DIMENSION_EXPERTISE_AREA}:{expertise_tag(record)}",
    )
    return tuple(key for key in candidates if key and key in open_gaps)


def recommend_substitutes(
    records: Iterable[DomainRecord],
    plan: SeatPlan,
    gap_report: dict[str, Any],
    limit: int = DEFAULT_LIMIT,
    promoted_record_ids: Iterable[str] | None = (),
) -> dict[str, Any]:
    settings = plan.settings
    seated = set(plan.seated_record_ids)
    promoted = set(promoted_record_ids or ())
    open_gaps = _open_gap_keys(gap_report)
    rejected_record_ids = {
        item.record_id for item in plan.exclusions if "confirmation-rejected" in item.blockers
    }

    suggestions: list[Substitution] = []
    for record in sorted(records, key=lambda item: (-candidate_score(item), item.record_id)):
        if record.record_id in seated:
            continue
        blockers = hard_blockers(record, settings, rejected_record_ids)
        if blockers:
            continue
        closes = _gap_keys_for_record(record, settings, open_gaps)
        # Recommendations must serve at least one open representation gap.
        if not closes:
            continue
        satisfied = tuple(
            sorted(
                {
                    "nominee_eligibility",
                    "timezone_window",
                    "availability_window",
                    "delegate_capacity",
                }
            )
        )
        substitution_id = stable_hash(
            {"plan_version": plan.version, "record_id": record.record_id, "kind": "substitution"}
        )[:24]
        status = STATUS_PROMOTED if record.record_id in promoted else STATUS_PROPOSED
        suggestions.append(
            Substitution(
                substitution_id,
                record.record_id,
                0,
                candidate_score(record),
                str(record.payload.get("region_group", "unknown")),
                expertise_tag(record),
                is_low_income(record, settings),
                closes,
                satisfied,
                status,
                "passes every hard constraint and fills one or more open representation gaps",
            )
        )

    suggestions.sort(key=lambda item: (-item.score, item.record_id))
    suggestions = [
        Substitution(
            item.substitution_id, item.record_id, index + 1, item.score, item.region_group,
            item.expertise_tag, item.low_income, item.closes_gaps, item.satisfied_constraints,
            item.status, item.rationale,
        )
        for index, item in enumerate(suggestions[: max(1, limit)])
    ]

    body = [item.as_dict() for item in suggestions]
    return {
        "plan_version": plan.version,
        "plan_hash": plan.plan_hash,
        "limit": max(1, limit),
        "recommendations": body,
        "recommendation_hash": stable_hash({"plan_hash": plan.plan_hash, "recommendations": body}),
    }
