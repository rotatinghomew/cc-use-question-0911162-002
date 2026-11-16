from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from assembly_scheduler.nominations.participant import ContractError, records_from_fixture
from assembly_scheduler.records.schedule_store import Repository
from assembly_scheduler.scheduler import Application, run, verify
from assembly_scheduler.delivery.schedule_pack import verify_bundle

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "acceptance.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class SeatPlanEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / "state.sqlite3"
        self.output = self.root / "output"

    def test_run_emits_quota_plan_gaps_and_substitutions(self):
        result = run(FIXTURE, self.database, self.output)
        plan = result["seat_plan"]
        self.assertEqual(plan["quota"], 4)
        self.assertEqual(len(plan["seats"]), 4)
        self.assertTrue(plan["exclusions"])
        reasons = {item["reason"] for item in plan["exclusions"]}
        self.assertIn("hard-constraint-blocked", reasons)
        self.assertTrue(any("blockers" in item and item["blockers"] for item in plan["exclusions"]))
        self.assertGreater(result["representation_gaps"]["gap_count"], 0)
        self.assertTrue(result["substitutions"]["recommendations"])

    def test_low_income_and_expertise_gaps_distinguish_competition_from_constraints(self):
        result = run(FIXTURE, self.database, self.output)
        entries = result["representation_gaps"]["entries"]
        low_income = next(
            item for item in entries
            if item["dimension"] == "low_income" and item["bucket"] == "low-income"
        )
        self.assertGreater(low_income["shortfall"], 0)
        # A feasible nominee exists but loses the quota competition: warning,
        # with explicit substitute and constraint evidence alongside it.
        self.assertEqual(low_income["severity"], "warning")
        self.assertTrue(low_income["fillable"])
        self.assertIn("delegate_nomination-001", low_income["available_substitute_ids"])
        self.assertTrue(
            {"eligibility-below-floor", "capacity-conflict-overrun"} & set(low_income["blockers"])
        )
        self.assertIn("delegate_nomination-006", low_income["blocked_record_ids"])
        digital = next(
            item for item in entries
            if item["dimension"] == "expertise_area" and item["bucket"] == "digital-governance"
        )
        self.assertGreater(digital["shortfall"], 0)
        # No feasible nominee remains, so this gap cannot self-heal: critical.
        self.assertEqual(digital["severity"], "critical")
        self.assertFalse(digital["fillable"])
        self.assertEqual(digital["available_substitute_ids"], [])
        self.assertIn("eligibility-below-floor", digital["blockers"])

    def test_bundle_contains_every_audit_artifact(self):
        run(FIXTURE, self.database, self.output)
        for name in ("seat-plan.json", "representation-gaps.json", "substitutions.json",
                     "plan-diffs.json", "seat-plan.csv", "representation-gaps.csv",
                     "exclusions.csv", "substitutions.csv"):
            self.assertTrue((self.output / name).is_file(), name)
        self.assertEqual(verify_bundle(self.output), [])
        self.assertTrue(verify(self.database, self.output)["ok"])

    def test_gap_csv_is_machine_readable(self):
        run(FIXTURE, self.database, self.output)
        with (self.output / "representation-gaps.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(rows)
        self.assertIn("available_substitute_ids", rows[0])
        self.assertIn("blocked_record_ids", rows[0])

    def test_plan_and_diffs_are_persisted_with_versions(self):
        application = Application(self.database)
        application.run_fixture(load_fixture(), self.output)
        stored = application.repository.latest_seat_plan()
        self.assertEqual(stored["version"], 1)
        self.assertEqual(len(application.repository.plan_diff_rows()), 1)


class ReEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / "state.sqlite3"
        self.output = self.root / "output"
        self.application = Application(self.database)
        self.application.run_fixture(load_fixture(), self.output)

    def test_rejection_forces_reallocation_and_records_blocker(self):
        seated_before = set(
            seat["record_id"] for seat in self.application.repository.latest_seat_plan()["seats"]
        )
        victim = next(iter(seated_before - {"delegate_nomination-002"}))
        result = self.application.confirm(victim, "rejected", "eligibility paperwork withdrawn",
                                         self.output)
        self.assertIn(victim, result["diff"]["removed"])
        self.assertTrue(result["diff"]["added"])
        exclusion = next(item for item in result["plan"]["exclusions"]
                         if item["record_id"] == victim)
        self.assertIn("confirmation-rejected", exclusion["blockers"])
        self.assertEqual(result["plan"]["version"], 2)

    def test_approval_pins_seat_against_unrelated_candidate_change(self):
        approved = self.application.confirm(
            "delegate_nomination-002", "approved", "committee confirmation", self.output
        )
        self.assertEqual(approved["record_state"], "confirmed")
        self.assertIn("delegate_nomination-002", approved["plan"]["pinned_record_ids"])

        changed = self.application.change_availability(
            "delegate_nomination-007", 5.0, self.output
        )
        seated = {seat["record_id"] for seat in changed["plan"]["seats"]}
        self.assertIn("delegate_nomination-002", seated)
        self.assertEqual(changed["diff"]["displaced"], [])
        pinned_seat = next(seat for seat in changed["plan"]["seats"]
                           if seat["record_id"] == "delegate_nomination-002")
        self.assertTrue(pinned_seat["pinned"])

    def test_availability_change_reassesses_affected_nomination(self):
        before = self.application.repository.get_record("delegate_nomination-001")
        result = self.application.change_availability(
            "delegate_nomination-001", 1.0, self.output
        )
        exclusion = next(item for item in result["plan"]["exclusions"]
                         if item["record_id"] == "delegate_nomination-001")
        self.assertIn("availability-window-too-short", exclusion["blockers"])
        self.assertEqual(result["record_version"], before.version + 1)
        stored = self.application.repository.get_record("delegate_nomination-001")
        self.assertEqual(stored.payload["availability_window"], 1.0)

    def test_promote_substitute_runs_through_confirmation_flow(self):
        initial = self.application.repository.latest_seat_plan()
        self.application.export_current(self.output)
        recommendation = next(
            item for item in
            json.loads((self.output / "substitutions.json").read_text(encoding="utf-8"))[
                "recommendations"
            ]
        )
        result = self.application.promote_substitute(
            recommendation["substitution_id"], "close representation gap", self.output
        )
        self.assertIn(recommendation["record_id"],
                      [seat["record_id"] for seat in result["plan"]["seats"]])
        self.assertTrue(any(
            seat["record_id"] == recommendation["record_id"] and seat["pinned"]
            for seat in result["plan"]["seats"]
        ))
        self.assertGreater(result["plan"]["version"], initial["version"])

    def test_stale_substitution_identifier_is_rejected(self):
        with self.assertRaisesRegex(ContractError, "unknown or no longer viable"):
            self.application.promote_substitute("not-a-real-id", "reason", self.output)

    def test_unknown_nomination_commands_raise_contract_error(self):
        with self.assertRaisesRegex(ContractError, "unknown nomination"):
            self.application.confirm("missing-001", "approved", "reason")
        with self.assertRaisesRegex(ContractError, "unknown nomination"):
            self.application.change_availability("missing-001", 9.0)

    def test_every_revision_appends_verifiable_events(self):
        self.application.confirm("delegate_nomination-002", "approved", "first", self.output)
        self.application.confirm("delegate_nomination-003", "rejected", "second", self.output)
        repository = Repository(self.database)
        self.assertEqual(repository.verify_chain(), [])
        diffs = repository.plan_diff_rows()
        self.assertGreaterEqual(len(diffs), 3)
        self.assertEqual(diffs[-1]["next_version"], repository.latest_seat_plan()["version"])
        self.assertEqual(len(repository.list_confirmations()), 2)

    def test_re_export_keeps_bundle_verifiable_after_revision(self):
        self.application.confirm("delegate_nomination-002", "approved", "pin", self.output)
        self.application.export_current(self.output)
        self.assertEqual(verify_bundle(self.output), [])
        summary = json.loads((self.output / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["seat_plan_version"],
                         self.application.repository.latest_seat_plan()["version"])
        self.assertGreaterEqual(summary["representation_gap_count"], 0)

    def test_identical_re_run_does_not_manufacture_plan_versions(self):
        first = run(FIXTURE, self.database, self.output)
        second = run(FIXTURE, self.database, self.output)
        self.assertEqual(first["seat_plan"]["version"], second["seat_plan"]["version"])
        self.assertEqual(
            len(Repository(self.database).plan_diff_rows()),
            1,
        )

    def test_confirmation_pins_survive_fixture_re_runs(self):
        self.application.confirm(
            "delegate_nomination-002", "approved", "durable confirmation", self.output
        )
        rerun = self.application.run_fixture(load_fixture(), self.output)
        self.assertIn("delegate_nomination-002", rerun["seat_plan"]["pinned_record_ids"])
        stored = Repository(self.database).get_record("delegate_nomination-002")
        self.assertEqual(stored.state, "confirmed")

    def test_rejections_keep_nomination_blocked_across_re_runs(self):
        self.application.confirm(
            "delegate_nomination-003", "rejected", "withdrawn nomination", self.output
        )
        rerun = self.application.run_fixture(load_fixture(), self.output)
        exclusion = next(item for item in rerun["seat_plan"]["exclusions"]
                         if item["record_id"] == "delegate_nomination-003")
        self.assertIn("confirmation-rejected", exclusion["blockers"])

    def test_rejection_can_be_overturned_by_later_approval(self):
        self.application.confirm("delegate_nomination-002", "rejected", "first review", self.output)
        revised = self.application.confirm(
            "delegate_nomination-002", "approved", "appeal upheld", self.output
        )
        self.assertIn("delegate_nomination-002",
                      [seat["record_id"] for seat in revised["plan"]["seats"]])
        self.assertEqual(
            self.application.repository.latest_confirmation("delegate_nomination-002")["outcome"],
            "approved",
        )
        self.assertFalse(any(
            item["record_id"] == "delegate_nomination-002"
            for item in revised["plan"]["exclusions"]
        ))


if __name__ == "__main__":
    unittest.main()
