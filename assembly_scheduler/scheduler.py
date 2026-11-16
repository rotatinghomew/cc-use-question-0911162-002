from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from assembly_scheduler.nominations.participant import ContractError, Decision, DomainRecord, records_from_fixture, stable_hash
from assembly_scheduler.records.schedule_store import Repository
from assembly_scheduler.confirmation.attendance import advance_for_outcome, decide
from assembly_scheduler.confirmation.nomination_confirm import (
    OUTCOME_APPROVED,
    OUTCOME_REJECTED,
    PROTECTED_STATES,
    confirm_nomination,
    pinned_record_ids,
    update_availability,
)
from assembly_scheduler.delivery.schedule_pack import export_bundle, verify_bundle
from assembly_scheduler.allocation.seat_match import derive_context
from assembly_scheduler.representation_signal.representation_balance import augment_context
from assembly_scheduler.representation_audit.eligibility import AuditSettings, settings_from_fixture
from assembly_scheduler.representation_audit.seat_plan import SeatPlan, build_plan, revise_plan
from assembly_scheduler.representation_audit.gap_report import representation_gaps
from assembly_scheduler.representation_audit.substitutes import recommend_substitutes

PLAN_TRIGGER_FIXTURE = "fixture-run"
PLAN_TRIGGER_CONFIRM = "confirmation"
PLAN_TRIGGER_AVAILABILITY = "availability-change"
PLAN_TRIGGER_PROMOTION = "substitution-promotion"


class Application:
    def __init__(self, database: str | Path, context: Mapping[str, Any] | None = None):
        self.repository = Repository(database)
        self.context = dict(context or {})

    def ingest(self, record: DomainRecord) -> DomainRecord:
        current = self.repository.get_record(record.record_id)
        if current is None:
            self.repository.save_record(record)
            return record
        if current.fingerprint == record.fingerprint:
            return current
        # Fixture replay carries fresh payload data but must never roll back a
        # human-driven lifecycle state (e.g. a confirmed or rejected nomination).
        preserved_state = current.state if current.state != record.state else record.state
        replacement = DomainRecord(record.record_id, record.payload, preserved_state,
                                   current.version + 1, record.occurred_at, record.source)
        self.repository.save_record(replacement, expected_version=current.version)
        return replacement

    def process(self, record: DomainRecord) -> tuple[DomainRecord, Decision]:
        stored = self.ingest(record)
        # Human confirmations own the lifecycle from this point on; the
        # automated scorecard must not demote a confirmed or scheduled seat.
        if stored.state in PROTECTED_STATES and self.latest_confirmation(stored.record_id) is not None:
            prior_rows = self.repository.decision_rows()
            prior = next((row for row in prior_rows if row["record_id"] == stored.record_id), None)
            if prior is not None:
                return stored, _decision_from_row(prior)
        context = dict(self.context)
        context.update(derive_context(stored, self.repository))
        context.update(augment_context(stored, self.repository))
        decision = decide(stored, context)
        self.repository.save_decision(decision)
        advanced = advance_for_outcome(stored, decision)
        if advanced.fingerprint != stored.fingerprint:
            self.repository.save_record(advanced, expected_version=stored.version)
        return advanced, decision

    def latest_confirmation(self, record_id: str) -> dict[str, Any] | None:
        return self.repository.latest_confirmation(record_id)

    # ------------------------------------------------------------------
    # Representation audit planning
    # ------------------------------------------------------------------
    def _current_pins(self) -> tuple[str, ...]:
        records = {row.record_id: row for row in self.repository.list_records()}
        confirmations = {item["record_id"]: item for item in self.repository.list_confirmations()}
        return pinned_record_ids(records, confirmations)

    def _current_rejections(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                item["record_id"]
                for item in self.repository.list_confirmations()
                if item.get("outcome") == OUTCOME_REJECTED
            )
        )

    def _load_settings(self) -> AuditSettings:
        stored = self.repository.latest_seat_plan()
        if stored and stored.get("settings"):
            return AuditSettings.from_dict(stored["settings"])
        return AuditSettings()

    def evaluate_plan(
        self,
        settings: AuditSettings | None = None,
        trigger: str = PLAN_TRIGGER_FIXTURE,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Build (or revise) the seat plan plus gap and substitute reports.

        A new plan version is only persisted when the allocation actually
        changes, so identical re-runs stay idempotent and cannot manufacture
        revision history or dislodge protected seats.
        """
        settings = settings or self._load_settings()
        records = self.repository.list_records()
        pins = self._current_pins()
        rejected = self._current_rejections()
        previous_payload = self.repository.latest_seat_plan()
        previous = None
        if previous_payload:
            previous = self._rehydrate_plan(previous_payload)
        if previous is None:
            plan = build_plan(records, settings, pins, version=1,
                              rejected_record_ids=rejected)
            _, diff = revise_plan(records, settings, None, pins, trigger,
                                  rejected_record_ids=rejected)
        else:
            candidate, candidate_diff = revise_plan(records, settings, previous, pins, trigger,
                                                     rejected_record_ids=rejected)
            if candidate.content_hash == previous.content_hash:
                # Allocation unchanged: keep the persisted version and history.
                plan = previous
                diff = candidate_diff
            else:
                plan = candidate
                diff = candidate_diff
        gap_report = representation_gaps(records, plan)
        promoted = {
            item["record_id"]
            for item in self.repository.list_confirmations()
            if item.get("outcome") == OUTCOME_APPROVED
        }
        substitutions = recommend_substitutes(records, plan, gap_report, promoted_record_ids=promoted)
        if persist and (previous is None or plan.content_hash != previous.content_hash):
            self.repository.save_seat_plan(plan)
            self.repository.save_plan_diff(diff, trigger)
        return {"plan": plan, "gaps": gap_report, "substitutions": substitutions,
                "diff": diff, "pins": pins}

    @staticmethod
    def _rehydrate_plan(payload: Mapping[str, Any]) -> SeatPlan:
        settings = AuditSettings.from_dict(payload.get("settings", {}))
        return _plan_from_payload(payload, settings)

    def run_fixture(self, fixture: Mapping[str, Any], output: str | Path) -> dict[str, Any]:
        records = records_from_fixture(fixture)
        fixture_hash = stable_hash(fixture)
        run_id = self.repository.begin_run(fixture_hash, len(records))
        decisions: dict[str, Decision] = {}
        final_records: list[DomainRecord] = []
        for record in records:
            final_record, decision = self.process(record)
            final_records.append(final_record)
            decisions[record.record_id] = decision
        # Rebuild the plan from the *current* repository state so that earlier
        # confirmations, rejections and pins survive a repeated fixture run.
        settings = settings_from_fixture(fixture)
        audit = self.evaluate_plan(settings, trigger=PLAN_TRIGGER_FIXTURE)
        snapshot = self.repository.snapshot()
        if snapshot["chain_errors"]:
            raise ContractError("audit chain verification failed")
        manifest = export_bundle(
            output, final_records, decisions, snapshot, self.repository.event_rows(),
            seat_plan=audit["plan"].as_dict(), gap_report=audit["gaps"],
            substitutions=audit["substitutions"], plan_diffs=self.repository.plan_diff_rows(),
        )
        result = {"run_id": run_id, "fixture_hash": fixture_hash, "records": len(final_records),
                  "decisions": len(decisions), "manifest": manifest, "snapshot": snapshot,
                  "seat_plan": audit["plan"].as_dict(),
                  "representation_gaps": audit["gaps"],
                  "substitutions": audit["substitutions"]}
        completed = self.repository.completed_run(run_id)
        if completed is not None:
            # Re-runs are idempotent on records/decisions but still refresh the
            # stored run result with the latest representation audit.
            self.repository.refresh_run(run_id, result)
            return result
        self.repository.finish_run(run_id, result)
        return result

    # ------------------------------------------------------------------
    # Confirmation-driven re-evaluation
    # ------------------------------------------------------------------
    def confirm(self, record_id: str, outcome: str, reason: str,
                output: str | Path | None = None) -> dict[str, Any]:
        record = self.repository.get_record(record_id)
        if record is None:
            raise ContractError(f"unknown nomination: {record_id}")
        advanced, confirmation = confirm_nomination(record, outcome, reason)
        if advanced.fingerprint != record.fingerprint:
            self.repository.save_record(advanced, expected_version=record.version)
        self.repository.save_confirmation(confirmation, advanced)
        audit = self.evaluate_plan(trigger=PLAN_TRIGGER_CONFIRM)
        result = {
            "confirmation": confirmation.as_dict(),
            "record_state": advanced.state,
            "plan": audit["plan"].as_dict(),
            "diff": audit["diff"].as_dict(),
            "representation_gaps": audit["gaps"],
            "substitutions": audit["substitutions"],
        }
        if output is not None:
            result["manifest"] = self.export_current(output)
        return result

    def change_availability(self, record_id: str, availability_window: float,
                            output: str | Path | None = None) -> dict[str, Any]:
        record = self.repository.get_record(record_id)
        if record is None:
            raise ContractError(f"unknown nomination: {record_id}")
        updated = update_availability(record, availability_window)
        self.repository.save_record(updated, expected_version=record.version)
        audit = self.evaluate_plan(trigger=PLAN_TRIGGER_AVAILABILITY)
        result = {
            "record_id": record_id,
            "availability_window": availability_window,
            "record_version": updated.version,
            "plan": audit["plan"].as_dict(),
            "diff": audit["diff"].as_dict(),
            "representation_gaps": audit["gaps"],
            "substitutions": audit["substitutions"],
        }
        if output is not None:
            result["manifest"] = self.export_current(output)
        return result

    def promote_substitute(self, substitution_id: str, reason: str,
                           output: str | Path | None = None) -> dict[str, Any]:
        """Promote a recommended substitute through the confirmation flow."""
        records = self.repository.list_records()
        latest_plan = self.repository.latest_seat_plan()
        if latest_plan is None:
            raise ContractError("no seat plan exists yet")
        plan = _plan_from_payload(latest_plan, self._load_settings())
        gap_report = representation_gaps(records, plan)
        recommendations = recommend_substitutes(
            records, plan, gap_report,
            promoted_record_ids={item["record_id"] for item in self.repository.list_confirmations()},
        )
        match = next(
            (item for item in recommendations["recommendations"]
             if item["substitution_id"] == substitution_id),
            None,
        )
        if match is None:
            raise ContractError(f"unknown or no longer viable substitution: {substitution_id}")
        return self.confirm(match["record_id"], OUTCOME_APPROVED, reason, output)

    def export_current(self, output: str | Path) -> dict[str, Any]:
        records = self.repository.list_records()
        decisions = {row["record_id"]: _decision_from_row(row) for row in self.repository.decision_rows()}
        plan_payload = self.repository.latest_seat_plan() or {}
        if plan_payload:
            records_for_report = self.repository.list_records()
            plan = _plan_from_payload(plan_payload, self._load_settings())
            gap_report = representation_gaps(records_for_report, plan)
            substitutions = recommend_substitutes(
                records_for_report, plan, gap_report,
                promoted_record_ids={
                    item["record_id"] for item in self.repository.list_confirmations()
                    if item.get("outcome") == OUTCOME_APPROVED
                },
            )
        else:
            gap_report, substitutions = {}, {}
        snapshot = self.repository.snapshot()
        return export_bundle(
            output, records, decisions, snapshot, self.repository.event_rows(),
            seat_plan=plan_payload, gap_report=gap_report, substitutions=substitutions,
            plan_diffs=self.repository.plan_diff_rows(),
        )

    def inspect(self) -> dict[str, Any]:
        return {"snapshot": self.repository.snapshot(), "records": [record.__dict__ for record in self.repository.list_records()],
                "decisions": self.repository.decision_rows(),
                "confirmations": self.repository.list_confirmations(),
                "seat_plan": self.repository.latest_seat_plan(),
                "plan_diffs": self.repository.plan_diff_rows()}


def _plan_from_payload(payload: Mapping[str, Any], settings: AuditSettings) -> SeatPlan:
    """Rebuild an equivalent immutable plan from its persisted serial form."""
    from assembly_scheduler.representation_audit.seat_plan import Exclusion, SeatedNominee

    seats = tuple(
        SeatedNominee(
            item["record_id"], item["rank"], item["score"], item["pinned"],
            item["low_income"], item["region_group"], item["expertise_tag"],
        )
        for item in payload.get("seats", [])
    )
    exclusions = tuple(
        Exclusion(
            item["record_id"], item["reason"], item["detail"], tuple(item.get("blockers", [])),
            item.get("evidence", {}),
        )
        for item in payload.get("exclusions", [])
    )
    return SeatPlan(
        payload.get("version", 1),
        payload.get("quota", settings.quota),
        settings,
        seats,
        exclusions,
        tuple(payload.get("pinned_record_ids", [])),
        tuple(payload.get("warnings", [])),
        payload.get("plan_hash", ""),
    )


def _decision_from_row(row: Mapping[str, Any]) -> Decision:
    from assembly_scheduler.nominations.participant import RuleResult

    rules = tuple(
        RuleResult(item["code"], item["passed"], item["score"], item["severity"],
                   item["message"], item.get("evidence", {}))
        for item in row.get("rules", [])
    )
    return Decision(row["record_id"], row["outcome"], row["score"], tuple(row["reasons"]),
                    rules, row.get("metrics", {}), row.get("decided_at", ""))


def load_fixture(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read fixture: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("fixture root must be an object")
    return value


def run(fixture_path: str | Path, database: str | Path, output: str | Path,
        context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return Application(database, context).run_fixture(load_fixture(fixture_path), output)


def verify(database: str | Path, output: str | Path) -> dict[str, Any]:
    repository = Repository(database)
    chain_errors = repository.verify_chain()
    bundle_errors = verify_bundle(output)
    return {"ok": not chain_errors and not bundle_errors, "chain_errors": chain_errors,
            "bundle_errors": bundle_errors, "snapshot": repository.snapshot()}
