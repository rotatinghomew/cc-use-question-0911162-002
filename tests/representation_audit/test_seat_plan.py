from __future__ import annotations

import unittest

from assembly_scheduler.nominations.participant import DomainRecord
from assembly_scheduler.representation_audit.eligibility import AuditSettings
from assembly_scheduler.representation_audit.seat_plan import build_plan, revise_plan
from assembly_scheduler.representation_audit.gap_report import representation_gaps


def record(record_id: str, region: str = "region_group-1", tag: str = "climate-finance",
           low_income: bool = False, **overrides) -> DomainRecord:
    payload = {
        "region_group": region,
        "agenda_priority": 20.0,
        "nominee_eligibility": 0.7,
        "availability_window": 30.0,
        "seat_class": 20.0,
        "expertise_area": 25.0,
        "expertise_tag": tag,
        "low_income": low_income,
        "accessibility_need": 0.5,
        "schedule_conflicts": 2.0,
        "delegate_capacity": 10.0,
        "representation_weight": 0.6,
        "timezone_penalty": 0.3,
        "participation_debt": 20.0,
    }
    payload.update(overrides)
    return DomainRecord(record_id, payload)


class SeatPlanTests(unittest.TestCase):
    def setUp(self):
        self.settings = AuditSettings(quota=3, low_income_groups=("region_group-0",))
        self.records = [
            record("n1", "region_group-0", low_income=True),
            record("n2", "region_group-1"),
            record("n3", "region_group-2", tag="digital-governance"),
            record("n4", "region_group-3", nominee_eligibility=0.1),
            record("n5", "region_group-0", low_income=True,
                   delegate_capacity=10.0, schedule_conflicts=10.0),
        ]

    def test_plan_respects_quota_and_ranks_feasible_nominees(self):
        plan = build_plan(self.records, self.settings)
        self.assertEqual(len(plan.seats), 3)
        self.assertEqual(len(plan.seated_record_ids), len(set(plan.seated_record_ids)))
        ranks = [seat.rank for seat in plan.seats]
        self.assertEqual(ranks, [1, 2, 3])

    def test_hard_blocked_nominee_gets_explicit_exclusion(self):
        plan = build_plan(self.records, self.settings)
        exclusion = next(item for item in plan.exclusions if item.record_id == "n4")
        self.assertEqual(exclusion.reason, "hard-constraint-blocked")
        self.assertIn("eligibility-below-floor", exclusion.blockers)
        self.assertTrue(exclusion.evidence["blockers"])

    def test_capacity_blocked_nominee_is_audited(self):
        plan = build_plan(self.records, self.settings)
        exclusion = next(item for item in plan.exclusions if item.record_id == "n5")
        self.assertIn("capacity-conflict-overrun", exclusion.blockers)

    def test_quota_competition_is_distinguished_from_blockers(self):
        settings = AuditSettings(quota=2)
        plan = build_plan(self.records[:3], settings)
        self.assertEqual(len(plan.seats), 2)
        overflow = next(item for item in plan.exclusions if item.reason == "capacity-competition")
        self.assertEqual(overflow.blockers, ())
        self.assertIn("score", overflow.evidence)

    def test_plan_hash_is_deterministic(self):
        first = build_plan(self.records, self.settings)
        second = build_plan(self.records, self.settings)
        self.assertEqual(first.plan_hash, second.plan_hash)

    def test_content_hash_ignores_version_number(self):
        first = build_plan(self.records, self.settings, version=1)
        second = build_plan(self.records, self.settings, version=2)
        self.assertEqual(first.content_hash, second.content_hash)
        self.assertNotEqual(first.plan_hash, second.plan_hash)

    def test_pinned_seats_are_retained_and_flagged(self):
        plan = build_plan(self.records, self.settings, pinned_record_ids=("n4",))
        pinned = [seat for seat in plan.seats if seat.pinned]
        self.assertEqual([seat.record_id for seat in pinned], ["n4"])
        self.assertTrue(any("pinned seat n4" in warning for warning in plan.warnings))

    def test_pinned_quota_overrun_is_rejected(self):
        with self.assertRaises(ValueError):
            build_plan(self.records, AuditSettings(quota=1), pinned_record_ids=("n1", "n2"))

    def test_unfillable_quota_emits_warning(self):
        settings = AuditSettings(quota=9)
        plan = build_plan(self.records, settings)
        self.assertTrue(any("fillable" in warning for warning in plan.warnings))


class PlanRevisionTests(unittest.TestCase):
    def setUp(self):
        self.settings = AuditSettings(quota=2)
        self.records = [record(f"n{index}") for index in range(1, 5)]

    def test_revision_versions_and_diffs_the_plan(self):
        first = build_plan(self.records, self.settings)
        next_plan, diff = revise_plan(self.records, self.settings, first,
                                      trigger="availability-change")
        self.assertEqual(next_plan.version, first.version + 1)
        self.assertEqual(diff.previous_version, first.version)
        self.assertEqual(diff.next_version, next_plan.version)
        self.assertIn("availability-change", " ".join(diff.warnings))

    def test_pinned_seat_cannot_be_displaced(self):
        first = build_plan(self.records, self.settings, pinned_record_ids=("n1",))
        next_plan, diff = revise_plan(self.records, self.settings, first,
                                      pinned_record_ids=("n1",), trigger="confirmation")
        self.assertIn("n1", next_plan.seated_record_ids)
        self.assertEqual(diff.displaced, ())
        self.assertIn("n1", diff.retained_pinned)

    def test_initial_diff_is_synthesised_without_previous_plan(self):
        plan, diff = revise_plan(self.records, self.settings, None)
        self.assertEqual(plan.version, 1)
        self.assertEqual(set(diff.added), set(plan.seated_record_ids))
        self.assertEqual(diff.removed, ())


class RepresentationGapTests(unittest.TestCase):
    def test_critical_gap_names_constraint_blockers(self):
        settings = AuditSettings(
            quota=2, low_income_share=0.5, low_income_groups=("region_group-0",),
            expertise_targets={"digital-governance": 1},
        )
        records = [
            record("li-blocked", "region_group-0", "digital-governance",
                   low_income=True, nominee_eligibility=0.1),
            record("li-capacity", "region_group-0", "digital-governance",
                   low_income=True, delegate_capacity=5.0, schedule_conflicts=5.0),
            record("other-1", "region_group-1"),
            record("other-2", "region_group-2"),
        ]
        plan = build_plan(records, settings)
        report = representation_gaps(records, plan)
        low_income = next(
            entry for entry in report["entries"]
            if entry["dimension"] == "low_income" and entry["bucket"] == "low-income"
        )
        self.assertEqual(low_income["target_seats"], 1)
        self.assertEqual(low_income["filled_seats"], 0)
        self.assertEqual(low_income["severity"], "critical")
        self.assertFalse(low_income["fillable"])
        self.assertIn("eligibility-below-floor", low_income["blockers"])
        self.assertIn("capacity-conflict-overrun", low_income["blockers"])
        self.assertEqual(set(low_income["blocked_record_ids"]), {"li-blocked", "li-capacity"})

    def test_warning_gap_points_to_feasible_substitutes(self):
        settings = AuditSettings(quota=1, expertise_targets={"digital-governance": 1})
        records = [
            record("digital-1", tag="digital-governance"),
            record("climate-1", tag="climate-finance"),
        ]
        plan = build_plan(records, settings)
        report = representation_gaps(records, plan)
        gap = next(
            entry for entry in report["entries"]
            if entry["dimension"] == "expertise_area" and entry["bucket"] == "digital-governance"
        )
        if gap["shortfall"]:
            self.assertEqual(gap["severity"], "warning")
            self.assertTrue(gap["fillable"])
            self.assertIn("digital-1", gap["available_substitute_ids"])

    def test_report_hash_covers_every_entry(self):
        settings = AuditSettings(quota=1)
        records = [record("n1"), record("n2", nominee_eligibility=0.1)]
        report = representation_gaps(records, build_plan(records, settings))
        self.assertIn("report_hash", report)
        self.assertEqual(report["quota"], 1)
        self.assertTrue(all(entry["shortfall"] >= 0 for entry in report["entries"]))

    def test_rejected_nominee_counts_as_blocked(self):
        settings = AuditSettings(quota=1, low_income_groups=("region_group-0",))
        records = [record("n1", "region_group-0", low_income=True), record("n2")]
        plan = build_plan(records, settings, rejected_record_ids={"n1"})
        report = representation_gaps(records, plan)
        low_income = next(
            entry for entry in report["entries"]
            if entry["dimension"] == "low_income" and entry["bucket"] == "low-income"
        )
        self.assertIn("confirmation-rejected", low_income["blockers"])
        self.assertIn("n1", low_income["blocked_record_ids"])


if __name__ == "__main__":
    unittest.main()
