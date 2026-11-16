from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from assembly_scheduler.nominations.participant import Decision, DomainRecord, canonical_json, stable_hash, utc_now


def ensure_output(path: str | Path) -> Path:
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    return output


def write_json(path: Path, value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    path.write_text(body + "\n", encoding="utf-8")
    return stable_hash(value)


def write_records(path: Path, records: Iterable[DomainRecord], decisions: Mapping[str, Decision]) -> int:
    rows = []
    for record in records:
        decision = decisions.get(record.record_id)
        rows.append({"record_id": record.record_id, "state": record.state, "version": record.version,
                     "source": record.source, "fingerprint": record.fingerprint,
                     "outcome": decision.outcome if decision else "", "score": decision.score if decision else ""})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "state", "version", "source", "fingerprint", "outcome", "score"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_rules(path: Path, decisions: Mapping[str, Decision]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "code", "passed", "score", "severity", "message"])
        writer.writeheader()
        for record_id, decision in sorted(decisions.items()):
            for result in decision.rule_results:
                writer.writerow({"record_id": record_id, "code": result.code, "passed": result.passed,
                                 "score": result.score, "severity": result.severity, "message": result.message})
                count += 1
    return count


def write_seat_plan(path: Path, seat_plan: Mapping[str, Any] | None) -> int:
    seat_plan = seat_plan or {"seats": [], "exclusions": []}
    with path.open("w", encoding="utf-8", newline="") as handle:
        fields = ["rank", "record_id", "pinned", "low_income", "region_group", "expertise_tag", "score"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for seat in seat_plan.get("seats", []):
            writer.writerow({key: seat.get(key, "") for key in fields})
    return len(seat_plan.get("seats", []))


def write_exclusions(path: Path, seat_plan: Mapping[str, Any] | None) -> int:
    seat_plan = seat_plan or {"exclusions": []}
    with path.open("w", encoding="utf-8", newline="") as handle:
        fields = ["record_id", "reason", "detail", "blockers"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in seat_plan.get("exclusions", []):
            writer.writerow({
                "record_id": item.get("record_id", ""),
                "reason": item.get("reason", ""),
                "detail": item.get("detail", ""),
                "blockers": "|".join(item.get("blockers", [])),
            })
    return len(seat_plan.get("exclusions", []))


def write_gaps(path: Path, gap_report: Mapping[str, Any] | None) -> int:
    gap_report = gap_report or {"entries": []}
    with path.open("w", encoding="utf-8", newline="") as handle:
        fields = ["dimension", "bucket", "target_seats", "filled_seats", "shortfall",
                  "pool_size", "feasible_pool_size", "fillable", "severity", "blockers",
                  "blocked_record_ids", "available_substitute_ids", "message"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in gap_report.get("entries", []):
            row = {key: entry.get(key, "") for key in fields}
            row["blockers"] = "|".join(entry.get("blockers", []))
            row["blocked_record_ids"] = "|".join(entry.get("blocked_record_ids", []))
            row["available_substitute_ids"] = "|".join(entry.get("available_substitute_ids", []))
            writer.writerow(row)
    return len(gap_report.get("entries", []))


def write_substitutions(path: Path, substitutions: Mapping[str, Any] | None) -> int:
    substitutions = substitutions or {"recommendations": []}
    with path.open("w", encoding="utf-8", newline="") as handle:
        fields = ["rank", "substitution_id", "record_id", "score", "region_group",
                  "expertise_tag", "low_income", "closes_gaps", "status", "rationale"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in substitutions.get("recommendations", []):
            row = {key: item.get(key, "") for key in fields}
            row["closes_gaps"] = "|".join(item.get("closes_gaps", []))
            writer.writerow(row)
    return len(substitutions.get("recommendations", []))


def build_summary(records: list[DomainRecord], decisions: Mapping[str, Decision], snapshot: Mapping[str, Any],
                  seat_plan: Mapping[str, Any] | None = None,
                  gap_report: Mapping[str, Any] | None = None,
                  substitutions: Mapping[str, Any] | None = None) -> dict[str, Any]:
    outcomes: dict[str, int] = {}
    for decision in decisions.values():
        outcomes[decision.outcome] = outcomes.get(decision.outcome, 0) + 1
    scores = [decision.score for decision in decisions.values()]
    seat_plan = seat_plan or {}
    gap_report = gap_report or {}
    substitutions = substitutions or {}
    return {"product": '全球南方治理参与席位与议程排程中心', "entity": 'delegate_nomination', "generated_at": utc_now(),
            "record_count": len(records), "decision_count": len(decisions), "outcomes": outcomes,
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "minimum_score": min(scores) if scores else 0.0, "maximum_score": max(scores) if scores else 0.0,
            "seat_plan_version": seat_plan.get("version", 0),
            "seat_quota": seat_plan.get("quota", 0),
            "seated_count": len(seat_plan.get("seats", [])),
            "exclusion_count": len(seat_plan.get("exclusions", [])),
            "representation_gap_count": gap_report.get("gap_count", 0),
            "critical_gap_count": gap_report.get("critical_count", 0),
            "substitution_count": len(substitutions.get("recommendations", [])),
            "repository": snapshot}


def export_bundle(output: str | Path, records: list[DomainRecord], decisions: Mapping[str, Decision],
                  snapshot: Mapping[str, Any], events: list[dict[str, Any]],
                  seat_plan: Mapping[str, Any] | None = None,
                  gap_report: Mapping[str, Any] | None = None,
                  substitutions: Mapping[str, Any] | None = None,
                  plan_diffs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    root = ensure_output(output)
    summary = build_summary(records, decisions, snapshot, seat_plan, gap_report, substitutions)
    record_count = write_records(root / "records.csv", records, decisions)
    rule_count = write_rules(root / "rules.csv", decisions)
    seat_rows = write_seat_plan(root / "seat-plan.csv", seat_plan)
    exclusion_rows = write_exclusions(root / "exclusions.csv", seat_plan)
    gap_rows = write_gaps(root / "representation-gaps.csv", gap_report)
    substitution_rows = write_substitutions(root / "substitutions.csv", substitutions)
    summary_hash = write_json(root / "summary.json", summary)
    decision_hash = write_json(root / "decisions.json", [value.as_dict() for _, value in sorted(decisions.items())])
    event_hash = write_json(root / "audit-events.json", events)
    seat_plan_hash = write_json(root / "seat-plan.json", seat_plan or {})
    gap_hash = write_json(root / "representation-gaps.json", gap_report or {})
    substitution_hash = write_json(root / "substitutions.json", substitutions or {})
    diff_hash = write_json(root / "plan-diffs.json", plan_diffs or [])
    manifest = {"files": {"summary.json": summary_hash, "decisions.json": decision_hash,
                           "audit-events.json": event_hash, "seat-plan.json": seat_plan_hash,
                           "representation-gaps.json": gap_hash,
                           "substitutions.json": substitution_hash,
                           "plan-diffs.json": diff_hash},
                "record_rows": record_count, "rule_rows": rule_count,
                "seat_rows": seat_rows, "exclusion_rows": exclusion_rows,
                "gap_rows": gap_rows, "substitution_rows": substitution_rows,
                "created_at": utc_now()}
    manifest["manifest_hash"] = stable_hash(manifest)
    write_json(root / "manifest.json", manifest)
    return manifest


def verify_bundle(output: str | Path) -> list[str]:
    root = Path(output)
    errors: list[str] = []
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return ["manifest.json is missing"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_hash = manifest.pop("manifest_hash", "")
    if stable_hash(manifest) != expected_manifest_hash:
        errors.append("manifest hash mismatch")
    for name, expected in manifest.get("files", {}).items():
        path = root / name
        if not path.is_file():
            errors.append(f"{name} is missing")
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if stable_hash(value) != expected:
            errors.append(f"{name} hash mismatch")
    return errors
