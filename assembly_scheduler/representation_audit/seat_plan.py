"""Quota-aware seat allocation with protected, pinned confirmations.

The plan keeps two guarantees the agenda team asked for:

1. every unseated nomination gets explicit exclusion evidence (hard blocker
   versus capacity competition), so a total score can never hide the cause;
2. confirmed seats are pinned and can never be displaced by unrelated
   candidate changes — re-evaluation only fills genuinely vacant seats.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from assembly_scheduler.nominations.participant import DomainRecord, stable_hash
from assembly_scheduler.representation_audit.eligibility import (
    AuditSettings,
    candidate_score,
    expertise_tag,
    hard_blockers,
    is_low_income,
)


@dataclass(frozen=True)
class Exclusion:
    record_id: str
    reason: str
    detail: str
    blockers: tuple[str, ...]
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "reason": self.reason,
            "detail": self.detail,
            "blockers": list(self.blockers),
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class SeatedNominee:
    record_id: str
    rank: int
    score: float
    pinned: bool
    low_income: bool
    region_group: str
    expertise_tag: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "rank": self.rank,
            "score": self.score,
            "pinned": self.pinned,
            "low_income": self.low_income,
            "region_group": self.region_group,
            "expertise_tag": self.expertise_tag,
        }


@dataclass(frozen=True)
class SeatPlan:
    version: int
    quota: int
    settings: AuditSettings
    seats: tuple[SeatedNominee, ...]
    exclusions: tuple[Exclusion, ...]
    pinned_record_ids: tuple[str, ...]
    warnings: tuple[str, ...]
    plan_hash: str

    @property
    def seated_record_ids(self) -> tuple[str, ...]:
        return tuple(seat.record_id for seat in self.seats)

    @property
    def content_hash(self) -> str:
        """Version-independent identity: identical allocations hash equally."""
        return stable_hash(
            {
                "quota": self.quota,
                "settings": self.settings.as_dict(),
                "seats": [seat.as_dict() for seat in self.seats],
                "exclusions": [item.as_dict() for item in self.exclusions],
                "pinned_record_ids": list(self.pinned_record_ids),
                "warnings": list(self.warnings),
            }
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "quota": self.quota,
            "settings": self.settings.as_dict(),
            "seats": [seat.as_dict() for seat in self.seats],
            "exclusions": [item.as_dict() for item in self.exclusions],
            "pinned_record_ids": list(self.pinned_record_ids),
            "warnings": list(self.warnings),
            "plan_hash": self.plan_hash,
            "content_hash": self.content_hash,
        }


def _rank_key(record: DomainRecord) -> tuple[float, str]:
    return (-candidate_score(record), record.record_id)


def build_plan(
    records: Iterable[DomainRecord],
    settings: AuditSettings,
    pinned_record_ids: Iterable[str] | None = None,
    version: int = 1,
    rejected_record_ids: Iterable[str] | None = None,
) -> SeatPlan:
    """Allocate up to ``quota`` seats while pinning confirmed nominations."""
    rows = sorted(records, key=lambda item: item.record_id)
    pinned = {item for item in pinned_record_ids or ()}
    rejected = {item for item in rejected_record_ids or ()}
    warnings: list[str] = []
    exclusions: list[Exclusion] = []
    seats: list[SeatedNominee] = []

    # 1. Protected confirmed seats always survive, even if they no longer pass
    #    the generic feasibility checks (the warning makes the drift visible).
    pinned_rows = [row for row in rows if row.record_id in pinned]
    if len(pinned_rows) > settings.quota:
        raise ValueError("pinned confirmations exceed the available seat quota")
    for row in pinned_rows:
        blockers = hard_blockers(row, settings, rejected)
        if blockers:
            warnings.append(
                f"pinned seat {row.record_id} no longer satisfies: "
                + ", ".join(blocker.code for blocker in blockers)
            )
        seats.append(
            SeatedNominee(
                row.record_id,
                0,
                candidate_score(row),
                True,
                is_low_income(row, settings),
                str(row.payload.get("region_group", "unknown")),
                expertise_tag(row),
            )
        )

    candidates = [row for row in rows if row.record_id not in pinned]
    feasible: list[DomainRecord] = []
    for row in candidates:
        blockers = hard_blockers(row, settings, rejected)
        if blockers:
            exclusions.append(
                Exclusion(
                    row.record_id,
                    "hard-constraint-blocked",
                    "nomination fails one or more mandatory constraints",
                    tuple(blocker.code for blocker in blockers),
                    {"blockers": [blocker.as_dict() for blocker in blockers]},
                )
            )
        else:
            feasible.append(row)

    feasible.sort(key=_rank_key)

    # 2. Fill the remaining seats purely by explainable ranking.
    open_seats = settings.quota - len(seats)
    promoted = feasible[: max(0, open_seats)]
    overflow = feasible[max(0, open_seats):]
    for row in overflow:
        exclusions.append(
            Exclusion(
                row.record_id,
                "capacity-competition",
                "feasible nomination lost the reduced quota to higher-ranked peers",
                (),
                {"score": candidate_score(row), "quota": settings.quota},
            )
        )

    for row in promoted:
        seats.append(
            SeatedNominee(
                row.record_id,
                0,
                candidate_score(row),
                False,
                is_low_income(row, settings),
                str(row.payload.get("region_group", "unknown")),
                expertise_tag(row),
            )
        )

    ordered = sorted(seats, key=lambda seat: (not seat.pinned, -seat.score, seat.record_id))
    seats = [
        SeatedNominee(
            seat.record_id, index + 1, seat.score, seat.pinned,
            seat.low_income, seat.region_group, seat.expertise_tag,
        )
        for index, seat in enumerate(ordered)
    ]

    if len(seats) < settings.quota:
        warnings.append(
            f"only {len(seats)} of {settings.quota} seats fillable from the nomination pool"
        )

    body = {
        "version": version,
        "quota": settings.quota,
        "settings": settings.as_dict(),
        "seats": [seat.as_dict() for seat in seats],
        "exclusions": [item.as_dict() for item in exclusions],
        "pinned_record_ids": sorted(pinned),
        "warnings": warnings,
    }
    return SeatPlan(
        version,
        settings.quota,
        settings,
        tuple(seats),
        tuple(exclusions),
        tuple(sorted(pinned)),
        tuple(warnings),
        stable_hash(body),
    )


@dataclass(frozen=True)
class PlanDiff:
    previous_version: int
    next_version: int
    added: tuple[str, ...]
    removed: tuple[str, ...]
    retained_pinned: tuple[str, ...]
    displaced: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "previous_version": self.previous_version,
            "next_version": self.next_version,
            "added": list(self.added),
            "removed": list(self.removed),
            "retained_pinned": list(self.retained_pinned),
            "displaced": list(self.displaced),
            "warnings": list(self.warnings),
        }


def revise_plan(
    records: Iterable[DomainRecord],
    settings: AuditSettings,
    previous: SeatPlan | None,
    pinned_record_ids: Iterable[str] | None = None,
    trigger: str = "re-evaluation",
    rejected_record_ids: Iterable[str] | None = None,
) -> tuple[SeatPlan, PlanDiff]:
    """Re-evaluate a plan and prove that no pinned seat was displaced."""
    next_version = 1 if previous is None else previous.version + 1
    next_plan = build_plan(records, settings, pinned_record_ids, next_version, rejected_record_ids)

    if previous is None:
        diff = PlanDiff(
            0,
            next_version,
            next_plan.seated_record_ids,
            (),
            next_plan.pinned_record_ids,
            (),
            (f"initial plan created via {trigger}",),
        )
        return next_plan, diff

    prior_seats = set(previous.seated_record_ids)
    next_seats = set(next_plan.seated_record_ids)
    added = tuple(sorted(next_seats - prior_seats))
    removed = tuple(sorted(prior_seats - next_seats))

    prior_pinned = set(previous.pinned_record_ids)
    displaced = tuple(sorted(prior_pinned - next_seats))
    retained_pinned = tuple(sorted(prior_pinned & next_seats))
    if displaced:
        raise RuntimeError(f"pinned seat displacement detected: {', '.join(displaced)}")

    warnings = list(next_plan.warnings)
    warnings.append(f"plan revised via {trigger}; {len(added)} added, {len(removed)} removed")
    diff = PlanDiff(
        previous.version,
        next_version,
        added,
        removed,
        retained_pinned,
        (),
        tuple(warnings),
    )
    return next_plan, diff


def exclusion_index(plan: SeatPlan) -> Mapping[str, Exclusion]:
    return {item.record_id: item for item in plan.exclusions}
