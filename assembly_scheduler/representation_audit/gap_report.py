"""Verifiable representation gap reporting.

A gap entry compares the policy target against the actual seat distribution for
a protected dimension, records whether the pool could have filled the gap, and
attributes every blocked nomination to the concrete constraint that stopped it.
This is what lets the agenda team answer members: the missing seat is either a
capacity/quota effect or an eligibility, timezone or availability constraint.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from assembly_scheduler.nominations.participant import DomainRecord, stable_hash
from assembly_scheduler.representation_audit.eligibility import (
    AuditSettings,
    expertise_tag,
    hard_blockers,
    is_feasible,
    is_low_income,
)
from assembly_scheduler.representation_audit.seat_plan import SeatPlan

DIMENSION_LOW_INCOME = "low_income"
DIMENSION_REGION_GROUP = "region_group"
DIMENSION_EXPERTISE_AREA = "expertise_area"


@dataclass(frozen=True)
class RepresentationGap:
    dimension: str
    bucket: str
    target_seats: int
    filled_seats: int
    shortfall: int
    pool_size: int
    feasible_pool_size: int
    fillable: bool
    severity: str
    blockers: tuple[str, ...]
    blocked_record_ids: tuple[str, ...]
    available_substitute_ids: tuple[str, ...]
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "bucket": self.bucket,
            "target_seats": self.target_seats,
            "filled_seats": self.filled_seats,
            "shortfall": self.shortfall,
            "pool_size": self.pool_size,
            "feasible_pool_size": self.feasible_pool_size,
            "fillable": self.fillable,
            "severity": self.severity,
            "blockers": list(self.blockers),
            "blocked_record_ids": list(self.blocked_record_ids),
            "available_substitute_ids": list(self.available_substitute_ids),
            "message": self.message,
        }


def _severity(shortfall: int, fillable: bool) -> str:
    if shortfall <= 0:
        return "info"
    # Constraints block every remaining nominee: the gap cannot self-heal.
    return "critical" if not fillable else "warning"


def _bucket(record: DomainRecord, dimension: str, settings: AuditSettings) -> str:
    if dimension == DIMENSION_LOW_INCOME:
        return "low-income" if is_low_income(record, settings) else "other"
    if dimension == DIMENSION_EXPERTISE_AREA:
        return expertise_tag(record)
    return str(record.payload.get("region_group", "unknown"))


def _gap_entry(
    dimension: str,
    bucket: str,
    target: int,
    pool: list[DomainRecord],
    seated_ids: set[str],
    settings: AuditSettings,
    rejected_record_ids: set[str],
) -> RepresentationGap:
    filled = sum(1 for row in pool if row.record_id in seated_ids)
    shortfall = max(0, target - filled)
    feasible_pool = [row for row in pool if is_feasible(row, settings, rejected_record_ids)]
    unseated_feasible = [row for row in feasible_pool if row.record_id not in seated_ids]
    # A gap is fillable whenever an unseated feasible nominee exists in the
    # bucket, even if that nominee currently loses the quota competition.
    fillable = len(unseated_feasible) > 0 and shortfall > 0
    quota_driven = fillable and shortfall <= len(unseated_feasible)

    blocked: list[DomainRecord] = []
    blocker_codes: set[str] = set()
    for row in pool:
        if row.record_id in seated_ids:
            continue
        blockers = hard_blockers(row, settings, rejected_record_ids)
        if blockers:
            blocked.append(row)
            blocker_codes.update(blocker.code for blocker in blockers)

    if shortfall <= 0:
        message = f"{dimension}:{bucket} meets its target of {target} seat(s)"
    elif quota_driven:
        message = (
            f"{dimension}:{bucket} is short {shortfall} seat(s); feasible nominees exist "
            f"({len(unseated_feasible)} unseated), so the gap is driven by quota competition "
            "rather than hard constraints"
        )
    elif fillable:
        message = (
            f"{dimension}:{bucket} is short {shortfall} seat(s); only {len(unseated_feasible)} "
            "unseated feasible nominee(s) can be promoted, and the rest of the pool is blocked by: "
            f"{', '.join(sorted(blocker_codes)) or 'no recorded constraints'}"
        )
    else:
        message = (
            f"{dimension}:{bucket} is short {shortfall} seat(s) and no unseated feasible nominee "
            f"exists; blocking constraints: {', '.join(sorted(blocker_codes)) or 'none'}"
        )

    return RepresentationGap(
        dimension,
        bucket,
        target,
        filled,
        shortfall,
        len(pool),
        len(feasible_pool),
        fillable,
        _severity(shortfall, fillable),
        tuple(sorted(blocker_codes)),
        tuple(row.record_id for row in sorted(blocked, key=lambda item: item.record_id)),
        tuple(row.record_id for row in sorted(unseated_feasible, key=lambda item: item.record_id)),
        message,
    )


def _largest_remainder_targets(weights: dict[str, int], total: int) -> dict[str, int]:
    """Allocate integer targets proportionally without losing seats to rounding."""
    eligible = {key: max(0, value) for key, value in weights.items() if max(0, value) > 0}
    if not eligible or total <= 0:
        return {key: 0 for key in weights}
    weight_sum = sum(eligible.values())
    floors = {key: total * value // weight_sum for key, value in eligible.items()}
    remainder = total - sum(floors.values())
    order = sorted(
        eligible,
        key=lambda key: (-(total * eligible[key] / weight_sum - floors[key]), key),
    )
    targets = dict(floors)
    for key in order[:remainder]:
        targets[key] += 1
    for key in weights:
        targets.setdefault(key, 0)
    return targets


def representation_gaps(
    records: Iterable[DomainRecord], plan: SeatPlan
) -> dict[str, Any]:
    settings = plan.settings
    rows = sorted(records, key=lambda item: item.record_id)
    seated_ids = set(plan.seated_record_ids)
    rejected_record_ids = {
        item.record_id for item in plan.exclusions if "confirmation-rejected" in item.blockers
    }
    entries: list[RepresentationGap] = []

    # Low-income dimension: policy target derived from the declared seat share.
    low_income_target = round(settings.quota * settings.low_income_share)
    low_pool = [row for row in rows if is_low_income(row, settings)]
    other_pool = [row for row in rows if not is_low_income(row, settings)]
    entries.append(
        _gap_entry(DIMENSION_LOW_INCOME, "low-income", low_income_target, low_pool,
                   seated_ids, settings, rejected_record_ids)
    )
    entries.append(
        _gap_entry(DIMENSION_LOW_INCOME, "other", max(0, settings.quota - low_income_target),
                   other_pool, seated_ids, settings, rejected_record_ids)
    )

    # Region dimension: targets follow the nomination pool proportions.
    region_weights: dict[str, int] = {}
    for row in rows:
        bucket = _bucket(row, DIMENSION_REGION_GROUP, settings)
        region_weights[bucket] = region_weights.get(bucket, 0) + 1
    region_targets = _largest_remainder_targets(region_weights, settings.quota)
    for bucket in sorted(region_weights):
        pool = [row for row in rows if _bucket(row, DIMENSION_REGION_GROUP, settings) == bucket]
        entries.append(
            _gap_entry(DIMENSION_REGION_GROUP, bucket, region_targets[bucket], pool,
                       seated_ids, settings, rejected_record_ids)
        )

    # Expertise dimension: explicit policy targets where declared.
    expertise_buckets = {expertise_tag(row) for row in rows} | set(settings.expertise_targets)
    for bucket in sorted(expertise_buckets):
        target = settings.expertise_targets.get(bucket, 0)
        pool = [row for row in rows if expertise_tag(row) == bucket]
        entries.append(
            _gap_entry(DIMENSION_EXPERTISE_AREA, bucket, target, pool,
                       seated_ids, settings, rejected_record_ids)
        )

    open_gaps = [entry for entry in entries if entry.shortfall > 0]
    critical = [entry for entry in open_gaps if entry.severity == "critical"]
    body = [entry.as_dict() for entry in entries]
    return {
        "plan_version": plan.version,
        "plan_hash": plan.plan_hash,
        "quota": plan.quota,
        "filled_seats": len(plan.seats),
        "gap_count": len(open_gaps),
        "critical_count": len(critical),
        "entries": body,
        "report_hash": stable_hash({"plan_hash": plan.plan_hash, "entries": body}),
    }
