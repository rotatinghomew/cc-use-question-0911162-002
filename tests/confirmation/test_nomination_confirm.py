from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from assembly_scheduler.nominations.participant import ContractError, DomainRecord
from assembly_scheduler.confirmation.nomination_confirm import (
    OUTCOME_APPROVED,
    OUTCOME_REJECTED,
    Confirmation,
    confirm_nomination,
    pinned_record_ids,
    update_availability,
)


def make_record(record_id: str, state: str = "eligible") -> DomainRecord:
    return DomainRecord(
        record_id,
        {
            "region_group": "region_group-0",
            "agenda_priority": 20.0,
            "nominee_eligibility": 0.7,
            "availability_window": 30.0,
            "seat_class": 20.0,
            "expertise_area": 25.0,
            "expertise_tag": "digital-governance",
            "low_income": True,
            "accessibility_need": 0.5,
            "schedule_conflicts": 2.0,
            "delegate_capacity": 10.0,
            "representation_weight": 0.6,
            "timezone_penalty": 0.3,
            "participation_debt": 20.0,
        },
        state,
    )


class ConfirmationCommandTests(unittest.TestCase):
    def test_approval_confirms_eligible_nomination(self):
        record = make_record("n1", "eligible")
        advanced, confirmation = confirm_nomination(record, OUTCOME_APPROVED, "approved by committee")
        self.assertEqual(advanced.state, "confirmed")
        self.assertEqual(advanced.version, record.version + 1)
        self.assertEqual(confirmation.outcome, OUTCOME_APPROVED)
        self.assertEqual(confirmation.record_id, "n1")

    def test_rejection_keeps_matched_nomination_unconfirmed(self):
        record = make_record("n1", "matched")
        advanced, confirmation = confirm_nomination(record, OUTCOME_REJECTED, "paperwork missing")
        self.assertEqual(advanced.state, "matched")
        self.assertEqual(confirmation.outcome, OUTCOME_REJECTED)

    def test_held_closed_nomination_can_be_revived_by_approval(self):
        record = make_record("n1", "closed")
        advanced, confirmation = confirm_nomination(record, OUTCOME_APPROVED, "manual override")
        self.assertEqual(advanced.state, "confirmed")
        self.assertEqual(confirmation.outcome, OUTCOME_APPROVED)

    def test_held_closed_nomination_returns_to_matched_on_rejection(self):
        record = make_record("n1", "closed")
        advanced, _ = confirm_nomination(record, OUTCOME_REJECTED, "not viable")
        self.assertEqual(advanced.state, "matched")

    def test_confirmed_nomination_cannot_be_reconfirmed(self):
        record = make_record("n1", "confirmed")
        with self.assertRaisesRegex(ContractError, "cannot be confirmed"):
            confirm_nomination(record, OUTCOME_APPROVED, "again")

    def test_unknown_outcome_is_rejected(self):
        record = make_record("n1")
        with self.assertRaises(ContractError):
            confirm_nomination(record, "maybe", "reason")

    def test_reason_is_required(self):
        record = make_record("n1")
        with self.assertRaisesRegex(ContractError, "reason is required"):
            confirm_nomination(record, OUTCOME_APPROVED, "  ")

    def test_confirmation_identifier_is_deterministic(self):
        record = make_record("n1")
        first = Confirmation.make(record, OUTCOME_APPROVED, "same reason")
        second = Confirmation.make(record, OUTCOME_APPROVED, "same reason")
        # The workflow identifier is content-derived and timestamp-independent.
        self.assertEqual(first.confirmation_id, second.confirmation_id)
        self.assertEqual(first.record_id, second.record_id)
        self.assertEqual(first.outcome, second.outcome)
        self.assertEqual(first.record_version, second.record_version)


class AvailabilityUpdateTests(unittest.TestCase):
    def test_availability_change_creates_new_version(self):
        record = make_record("n1")
        updated = update_availability(record, 12.5)
        self.assertEqual(updated.payload["availability_window"], 12.5)
        self.assertEqual(updated.version, record.version + 1)
        self.assertEqual(updated.state, record.state)

    def test_negative_window_is_rejected(self):
        record = make_record("n1")
        with self.assertRaises(ContractError):
            update_availability(record, -3.0)

    def test_non_numeric_window_is_rejected(self):
        record = make_record("n1")
        with self.assertRaises(ContractError):
            update_availability(record, "soon")


class PinnedRecordTests(unittest.TestCase):
    def test_only_approved_protected_nominations_are_pinned(self):
        records = {
            "approved-confirmed": make_record("approved-confirmed", "confirmed"),
            "approved-scheduled": make_record("approved-scheduled", "scheduled"),
            "rejected": make_record("rejected", "matched"),
            "unconfirmed": make_record("unconfirmed", "matched"),
            "stale-approval": make_record("stale-approval", "eligible"),
        }
        confirmations = {
            "approved-confirmed": {"outcome": OUTCOME_APPROVED},
            "approved-scheduled": {"outcome": OUTCOME_APPROVED},
            "rejected": {"outcome": OUTCOME_REJECTED},
            "stale-approval": {"outcome": OUTCOME_APPROVED},
        }
        pins = pinned_record_ids(records, confirmations)
        self.assertEqual(set(pins), {"approved-confirmed", "approved-scheduled"})

    def test_no_confirmations_means_no_pins(self):
        records = {"n1": make_record("n1", "confirmed")}
        self.assertEqual(pinned_record_ids(records, {}), ())


if __name__ == "__main__":
    unittest.main()
