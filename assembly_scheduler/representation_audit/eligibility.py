"""Feasibility evaluation for delegate nominations.

Every rejection from the seat plan must be attributable to an explicit,
auditable blocker instead of an opaque total score. The checks here model the
real constraints raised by the agenda team: nomination eligibility, timezone
penalty, availability windows and delegate capacity conflicts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from assembly_scheduler.nominations.participant import (
    ContractError,
    DomainRecord,
    bounded,
    finite_number,
    normalized_text,
)
from assembly_scheduler.representation_signal.representation_balance import representation_balance

DEFAULT_QUOTA = 4
DEFAULT_ELIGIBILITY_FLOOR = 0.40
DEFAULT_TIMEZONE_CEILING = 0.60
DEFAULT_AVAILABILITY_FLOOR = 14.0
DEFAULT_CAPACITY_HEADROOM = 0.25
DEFAULT_LOW_INCOME_SHARE = 0.50


@dataclass(frozen=True)
class AuditSettings:
    """Configurable allocation policy for a planning round."""

    quota: int = DEFAULT_QUOTA
    eligibility_floor: float = DEFAULT_ELIGIBILITY_FLOOR
    timezone_ceiling: float = DEFAULT_TIMEZONE_CEILING
    availability_floor: float = DEFAULT_AVAILABILITY_FLOOR
    capacity_headroom: float = DEFAULT_CAPACITY_HEADROOM
    low_income_share: float = DEFAULT_LOW_INCOME_SHARE
    low_income_groups: tuple[str, ...] = ()
    expertise_targets: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "quota", int(self.quota))
        if self.quota < 0:
            raise ContractError("seat quota cannot be negative")
        object.__setattr__(self, "eligibility_floor", bounded(self.eligibility_floor))
        object.__setattr__(self, "timezone_ceiling", bounded(self.timezone_ceiling))
        object.__setattr__(self, "low_income_share", bounded(self.low_income_share))
        if self.availability_floor < 0:
            raise ContractError("availability floor cannot be negative")
        if not 0.0 <= self.capacity_headroom <= 1.0:
            raise ContractError("capacity headroom must stay within 0..1")
        object.__setattr__(
            self,
            "low_income_groups",
            tuple(normalized_text(item) for item in self.low_income_groups if normalized_text(item)),
        )
        targets: dict[str, int] = {}
        for key, value in (self.expertise_targets or {}).items():
            count = int(value)
            if count < 0:
                raise ContractError("expertise target cannot be negative")
            targets[normalized_text(key)] = count
        object.__setattr__(self, "expertise_targets", targets)

    def as_dict(self) -> dict[str, Any]:
        return {
            "quota": self.quota,
            "eligibility_floor": self.eligibility_floor,
            "timezone_ceiling": self.timezone_ceiling,
            "availability_floor": self.availability_floor,
            "capacity_headroom": self.capacity_headroom,
            "low_income_share": self.low_income_share,
            "low_income_groups": list(self.low_income_groups),
            "expertise_targets": dict(sorted(self.expertise_targets.items())),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AuditSettings":
        value = value or {}
        return cls(
            quota=value.get("quota", DEFAULT_QUOTA),
            eligibility_floor=value.get("eligibility_floor", DEFAULT_ELIGIBILITY_FLOOR),
            timezone_ceiling=value.get("timezone_ceiling", DEFAULT_TIMEZONE_CEILING),
            availability_floor=value.get("availability_floor", DEFAULT_AVAILABILITY_FLOOR),
            capacity_headroom=value.get("capacity_headroom", DEFAULT_CAPACITY_HEADROOM),
            low_income_share=value.get("low_income_share", DEFAULT_LOW_INCOME_SHARE),
            low_income_groups=tuple(value.get("low_income_groups", ())),
            expertise_targets=dict(value.get("expertise_targets", {})),
        )


def settings_from_fixture(fixture: Mapping[str, Any]) -> AuditSettings:
    """Read policy from an optional ``allocation`` block; defaults stay stable."""
    raw = fixture.get("allocation") if isinstance(fixture, Mapping) else None
    if raw is None:
        return AuditSettings()
    if not isinstance(raw, Mapping):
        raise ContractError("fixture allocation block must be an object")
    return AuditSettings.from_dict(raw)


@dataclass(frozen=True)
class Blocker:
    """A single, evidence-backed reason a nomination cannot take a seat."""

    code: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "evidence": self.evidence}


def _ratio(value: Any) -> float:
    number = finite_number(value)
    return bounded(number / 100.0 if number > 1.0 else number)


def is_low_income(record: DomainRecord, settings: AuditSettings) -> bool:
    payload = record.payload
    marker = payload.get("low_income")
    if isinstance(marker, bool):
        return marker
    if isinstance(marker, str) and normalized_text(marker) in {"true", "yes", "1", "y"}:
        return True
    if isinstance(marker, (int, float)) and not isinstance(marker, bool):
        return _ratio(marker) >= 0.5
    group = normalized_text(payload.get("region_group", "unknown"))
    return group in settings.low_income_groups


def expertise_tag(record: DomainRecord) -> str:
    """Return the declared expertise category.

    Nominations may carry an explicit ``expertise_tag``; otherwise the numeric
    ``expertise_area`` bucket is used so legacy fixtures remain explainable.
    """
    explicit = record.payload.get("expertise_tag")
    if explicit not in (None, ""):
        return normalized_text(explicit)
    raw = finite_number(record.payload.get("expertise_area", 0.0))
    buckets = ("climate-finance", "digital-governance", "public-health", "trade-policy")
    return buckets[min(len(buckets) - 1, int(raw) // 10)]


def hard_blockers(
    record: DomainRecord,
    settings: AuditSettings,
    rejected_record_ids: Iterable[str] | None = None,
) -> tuple[Blocker, ...]:
    """Evaluate every hard constraint independently so combined failures show.

    ``rejected_record_ids`` carries explicit human rejections from the
    confirmation workflow; the automated scorecard's lifecycle state is not a
    hard constraint because scorecard holds do not withdraw a nomination.
    """
    payload = record.payload
    blockers: list[Blocker] = []

    if record.record_id in set(rejected_record_ids or ()):
        blockers.append(
            Blocker(
                "confirmation-rejected",
                "nomination was rejected during confirmation and cannot occupy a seat",
                {"record_id": record.record_id},
            )
        )

    eligibility = _ratio(payload.get("nominee_eligibility", 0.0))
    if eligibility < settings.eligibility_floor:
        blockers.append(
            Blocker(
                "eligibility-below-floor",
                "nominee eligibility is below the confirmation floor",
                {"nominee_eligibility": eligibility, "floor": settings.eligibility_floor},
            )
        )

    timezone = _ratio(payload.get("timezone_penalty", 0.0))
    if timezone > settings.timezone_ceiling:
        blockers.append(
            Blocker(
                "timezone-outside-window",
                "timezone penalty exceeds the acceptable window ceiling",
                {"timezone_penalty": timezone, "ceiling": settings.timezone_ceiling},
            )
        )

    availability = finite_number(payload.get("availability_window", 0.0))
    if availability < settings.availability_floor:
        blockers.append(
            Blocker(
                "availability-window-too-short",
                "available window does not cover the minimum programme window",
                {"availability_window": availability, "floor": settings.availability_floor},
            )
        )

    capacity = finite_number(payload.get("delegate_capacity", 0.0))
    conflicts = finite_number(payload.get("schedule_conflicts", 0.0))
    headroom = capacity - conflicts
    headroom_share = bounded(headroom / max(1.0, capacity))
    if capacity <= conflicts or headroom_share < settings.capacity_headroom:
        blockers.append(
            Blocker(
                "capacity-conflict-overrun",
                "schedule conflicts consume more than the allowed capacity headroom",
                {
                    "delegate_capacity": capacity,
                    "schedule_conflicts": conflicts,
                    "headroom": headroom,
                    "headroom_share": headroom_share,
                    "required_share": settings.capacity_headroom,
                },
            )
        )

    return tuple(blockers)


def is_feasible(
    record: DomainRecord,
    settings: AuditSettings,
    rejected_record_ids: Iterable[str] | None = None,
) -> bool:
    return not hard_blockers(record, settings, rejected_record_ids)


def candidate_score(record: DomainRecord) -> float:
    """Deterministic, explainable ranking score used for quota competition."""
    signal = representation_balance(record.payload)
    eligibility = _ratio(record.payload.get("nominee_eligibility", 0.0))
    weight = _ratio(record.payload.get("representation_weight", 0.0))
    return bounded(signal.score * 0.6 + eligibility * 0.25 + weight * 0.15)
