from __future__ import annotations

import unittest

from assembly_scheduler.nominations.participant import ContractError, DomainRecord
from assembly_scheduler.representation_audit.eligibility import (
    AuditSettings,
    expertise_tag,
    hard_blockers,
    is_feasible,
    is_low_income,
    settings_from_fixture,
)


def make_record(record_id: str, **overrides) -> DomainRecord:
    payload = {
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
    }
    payload.update(overrides)
    return DomainRecord(record_id, payload)


class AuditSettingsTests(unittest.TestCase):
    def test_defaults_are_stable(self):
        settings = AuditSettings()
        self.assertEqual(settings.quota, 4)
        self.assertEqual(settings.low_income_groups, ())
        self.assertEqual(settings.expertise_targets, {})

    def test_negative_quota_is_rejected(self):
        with self.assertRaises(ContractError):
            AuditSettings(quota=-1)

    def test_negative_expertise_target_is_rejected(self):
        with self.assertRaises(ContractError):
            AuditSettings(expertise_targets={"climate-finance": -2})

    def test_settings_round_trip_through_dict(self):
        settings = AuditSettings(
            quota=6, low_income_groups=("Region_Group-0",),
            expertise_targets={"digital-governance": 2},
        )
        restored = AuditSettings.from_dict(settings.as_dict())
        self.assertEqual(restored.quota, 6)
        self.assertEqual(restored.low_income_groups, ("region_group-0",))
        self.assertEqual(restored.expertise_targets, {"digital-governance": 2})

    def test_settings_from_fixture_uses_defaults_without_block(self):
        self.assertEqual(settings_from_fixture({}).quota, AuditSettings().quota)

    def test_settings_from_fixture_reads_policy_block(self):
        fixture = {"allocation": {"quota": 2, "low_income_share": 0.75}}
        settings = settings_from_fixture(fixture)
        self.assertEqual(settings.quota, 2)
        self.assertEqual(settings.low_income_share, 0.75)

    def test_non_object_allocation_block_is_rejected(self):
        with self.assertRaises(ContractError):
            settings_from_fixture({"allocation": []})


class LowIncomeAndExpertiseTests(unittest.TestCase):
    def test_explicit_low_income_marker_is_honoured(self):
        settings = AuditSettings()
        self.assertTrue(is_low_income(make_record("a", low_income=True), settings))
        self.assertFalse(is_low_income(make_record("b", low_income=False), settings))

    def test_group_membership_implies_low_income(self):
        settings = AuditSettings(low_income_groups=("region_group-0",))
        record = make_record("a").with_payload({"low_income": None})
        self.assertTrue(is_low_income(record, settings))
        outside = make_record("b", region_group="region_group-9").with_payload({"low_income": None})
        self.assertFalse(is_low_income(outside, settings))

    def test_expertise_tag_falls_back_to_numeric_bucket(self):
        record = make_record("a")
        record = record.with_payload({"expertise_tag": None})
        self.assertEqual(expertise_tag(record), "public-health")
        self.assertEqual(expertise_tag(make_record("b", expertise_tag="Climate Finance")),
                         "climate finance")


class HardBlockerTests(unittest.TestCase):
    def setUp(self):
        self.settings = AuditSettings()

    def test_feasible_record_has_no_blockers(self):
        self.assertEqual(hard_blockers(make_record("a"), self.settings), ())
        self.assertTrue(is_feasible(make_record("a"), self.settings))

    def test_eligibility_failure_is_blocked(self):
        record = make_record("a", nominee_eligibility=0.1)
        codes = {blocker.code for blocker in hard_blockers(record, self.settings)}
        self.assertIn("eligibility-below-floor", codes)

    def test_timezone_failure_is_blocked(self):
        record = make_record("a", timezone_penalty=0.9)
        codes = {blocker.code for blocker in hard_blockers(record, self.settings)}
        self.assertIn("timezone-outside-window", codes)

    def test_availability_failure_is_blocked(self):
        record = make_record("a", availability_window=2.0)
        codes = {blocker.code for blocker in hard_blockers(record, self.settings)}
        self.assertIn("availability-window-too-short", codes)

    def test_capacity_conflict_is_blocked_with_evidence(self):
        record = make_record("a", delegate_capacity=10.0, schedule_conflicts=9.9)
        blockers = hard_blockers(record, self.settings)
        self.assertEqual({blocker.code for blocker in blockers}, {"capacity-conflict-overrun"})
        self.assertIn("headroom_share", blockers[0].evidence)

    def test_combined_failures_are_all_reported(self):
        record = make_record("a", nominee_eligibility=0.1, timezone_penalty=0.95,
                             availability_window=1.0, delegate_capacity=5.0,
                             schedule_conflicts=5.0)
        codes = {blocker.code for blocker in hard_blockers(record, self.settings)}
        self.assertEqual(
            codes,
            {"eligibility-below-floor", "timezone-outside-window",
             "availability-window-too-short", "capacity-conflict-overrun"},
        )

    def test_explicit_rejection_blocks_independently_of_lifecycle(self):
        record = make_record("a", state="closed")
        self.assertTrue(is_feasible(record, self.settings))
        self.assertFalse(is_feasible(record, self.settings, {"a"}))
        codes = {blocker.code for blocker in hard_blockers(record, self.settings, {"a"})}
        self.assertIn("confirmation-rejected", codes)

    def test_blocker_evidence_contains_thresholds(self):
        record = make_record("a", nominee_eligibility=0.1)
        blocker = next(item for item in hard_blockers(record, self.settings)
                       if item.code == "eligibility-below-floor")
        self.assertEqual(blocker.evidence["floor"], self.settings.eligibility_floor)


if __name__ == "__main__":
    unittest.main()
