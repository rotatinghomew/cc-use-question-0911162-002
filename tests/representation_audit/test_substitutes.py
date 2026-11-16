from __future__ import annotations

import unittest

from assembly_scheduler.nominations.participant import DomainRecord
from assembly_scheduler.representation_audit.eligibility import AuditSettings
from assembly_scheduler.representation_audit.seat_plan import build_plan
from assembly_scheduler.representation_audit.gap_report import representation_gaps
from assembly_scheduler.representation_audit.substitutes import (
    STATUS_PROMOTED,
    STATUS_PROPOSED,
    recommend_substitutes,
)


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


class SubstitutionTests(unittest.TestCase):
    def setUp(self):
        self.settings = AuditSettings(
            quota=2, low_income_share=0.5, low_income_groups=("region_group-0",),
            expertise_targets={"digital-governance": 1},
        )
        self.records = [
            record("li-feasible", "region_group-0", "climate-finance", low_income=True),
            record("li-blocked", "region_group-0", "digital-governance",
                   low_income=True, nominee_eligibility=0.1),
            record("other-a", "region_group-1", "climate-finance",
                   nominee_eligibility=0.95, representation_weight=0.95),
            record("other-b", "region_group-2", "public-health",
                   nominee_eligibility=0.9, representation_weight=0.9),
        ]
        self.plan = build_plan(self.records, self.settings)
        self.gap_report = representation_gaps(self.records, self.plan)
        self.assertNotIn("li-feasible", self.plan.seated_record_ids)

    def test_only_feasible_unseated_nominees_are_recommended(self):
        result = recommend_substitutes(self.records, self.plan, self.gap_report)
        ids = {item["record_id"] for item in result["recommendations"]}
        self.assertNotIn("li-blocked", ids)
        self.assertNotIn("other-b", ids)
        self.assertIn("li-feasible", ids)

    def test_recommendation_carries_gap_and_constraint_evidence(self):
        result = recommend_substitutes(self.records, self.plan, self.gap_report)
        target = next(item for item in result["recommendations"]
                      if item["record_id"] == "li-feasible")
        self.assertIn("low_income:low-income", target["closes_gaps"])
        self.assertEqual(
            set(target["satisfied_constraints"]),
            {"nominee_eligibility", "timezone_window", "availability_window", "delegate_capacity"},
        )
        self.assertTrue(target["substitution_id"])
        self.assertEqual(target["status"], STATUS_PROPOSED)

    def test_ranking_is_stable_and_limited(self):
        result = recommend_substitutes(self.records, self.plan, self.gap_report, limit=1)
        self.assertLessEqual(len(result["recommendations"]), 1)
        self.assertEqual(result["recommendations"][0]["rank"], 1)
        again = recommend_substitutes(self.records, self.plan, self.gap_report, limit=1)
        self.assertEqual(
            result["recommendations"][0]["substitution_id"],
            again["recommendations"][0]["substitution_id"],
        )

    def test_promoted_record_is_flagged(self):
        result = recommend_substitutes(
            self.records, self.plan, self.gap_report,
            promoted_record_ids={"li-feasible"},
        )
        target = next(item for item in result["recommendations"]
                      if item["record_id"] == "li-feasible")
        self.assertEqual(target["status"], STATUS_PROMOTED)

    def test_recommendation_hash_tracks_plan_version(self):
        result = recommend_substitutes(self.records, self.plan, self.gap_report)
        self.assertEqual(result["plan_hash"], self.plan.plan_hash)
        self.assertIn("recommendation_hash", result)

    def test_seated_nominees_are_never_recommended(self):
        result = recommend_substitutes(self.records, self.plan, self.gap_report)
        seated = set(self.plan.seated_record_ids)
        self.assertTrue(not (seated & {item["record_id"] for item in result["recommendations"]}))


if __name__ == "__main__":
    unittest.main()
