"""Nomination confirmation commands wired back into seat planning.

Confirmations are explicit decisions recorded against a nomination:

* ``approve`` moves an eligible/matched nomination to ``confirmed`` and its seat
  becomes pinned for every later planning round;
* ``reject`` keeps the nomination out of the seat pool and forces a
  re-evaluation that fills the vacated seat with a ranked substitute;
* availability changes only re-evaluate affected agenda arrangements while
  pinned confirmations remain protected.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from assembly_scheduler.nominations.participant import ContractError, DomainRecord, identifier, stable_hash, utc_now

OUTCOME_APPROVED = "approved"
OUTCOME_REJECTED = "rejected"
CONFIRMATION_OUTCOMES = (OUTCOME_APPROVED, OUTCOME_REJECTED)

# States from which a human confirmation can still be issued. The scorecard
# parks holds in ``closed``; that is not a human rejection, so held nominations
# remain confirmable until an explicit decision is recorded.
CONFIRMABLE_STATES = ("eligible", "matched", "closed")
# States whose seat must be protected during re-evaluation.
PROTECTED_STATES = ("confirmed", "scheduled")


@dataclass(frozen=True)
class Confirmation:
    confirmation_id: str
    record_id: str
    outcome: str
    reason: str
    record_version: int
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_id", identifier(self.record_id))
        if self.outcome not in CONFIRMATION_OUTCOMES:
            raise ContractError("confirmation outcome must be approved or rejected")
        if not self.reason.strip():
            raise ContractError("confirmation reason is required")
        if self.record_version < 1:
            raise ContractError("record version must be positive")

    @property
    def fingerprint(self) -> str:
        return stable_hash(self.as_dict())

    def as_dict(self) -> dict[str, Any]:
        return {
            "confirmation_id": self.confirmation_id,
            "record_id": self.record_id,
            "outcome": self.outcome,
            "reason": self.reason,
            "record_version": self.record_version,
            "created_at": self.created_at,
        }

    @classmethod
    def make(cls, record: DomainRecord, outcome: str, reason: str) -> "Confirmation":
        confirmation_id = stable_hash(
            {"record_id": record.record_id, "record_version": record.version,
             "outcome": outcome, "reason": reason, "kind": "confirmation"}
        )[:24]
        return cls(confirmation_id, record.record_id, outcome, reason, record.version)


def confirm_nomination(record: DomainRecord, outcome: str, reason: str) -> tuple[DomainRecord, Confirmation]:
    """Apply an approval/rejection while honouring the forward-only lifecycle.

    Scorecard holds end in ``closed`` but are not human decisions, so an
    explicit confirmation revives the nomination: approvals jump to
    ``confirmed`` and rejections return to ``matched`` for re-allocation.
    """
    if outcome not in CONFIRMATION_OUTCOMES:
        raise ContractError("confirmation outcome must be approved or rejected")
    if record.state not in CONFIRMABLE_STATES:
        raise ContractError(
            f"nomination in state {record.state} cannot be confirmed; expected one of {', '.join(CONFIRMABLE_STATES)}"
        )
    confirmation = Confirmation.make(record, outcome, reason)
    if outcome == OUTCOME_APPROVED:
        advanced = record.with_state("confirmed")
        return advanced, confirmation
    if record.state == "closed":
        return record.with_state("matched"), confirmation
    return record, confirmation


def update_availability(record: DomainRecord, availability_window: Any) -> DomainRecord:
    """Record an availability change as a new payload version."""
    try:
        window = float(availability_window)
    except (TypeError, ValueError) as exc:
        raise ContractError("availability window must be numeric") from exc
    if window < 0:
        raise ContractError("availability window cannot be negative")
    return record.with_payload({"availability_window": window})


def pinned_record_ids(records: Mapping[str, DomainRecord], confirmations: Mapping[str, Any]) -> tuple[str, ...]:
    """A seat is pinned only when a stored approval matches the current lifecycle."""
    pinned: list[str] = []
    for record_id, record in records.items():
        confirmation = confirmations.get(record_id)
        if confirmation is None:
            continue
        if confirmation.get("outcome") != OUTCOME_APPROVED:
            continue
        if record.state not in PROTECTED_STATES:
            continue
        pinned.append(record_id)
    return tuple(sorted(pinned))
