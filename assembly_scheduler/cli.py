from __future__ import annotations

import argparse
import json
from typing import Sequence

from assembly_scheduler.scheduler import Application, run, verify


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog='assembly_scheduler', description='全球南方治理参与席位与议程排程中心')
    cli = root.add_subparsers(dest="command", required=True)
    execute = cli.add_parser("run")
    execute.add_argument("--fixture", required=True)
    execute.add_argument("--database", required=True)
    execute.add_argument("--output", required=True)
    check = cli.add_parser("verify")
    check.add_argument("--database", required=True)
    check.add_argument("--output", required=True)
    inspect = cli.add_parser("inspect")
    inspect.add_argument("--database", required=True)
    confirm = cli.add_parser("confirm", help="approve or reject a nomination and re-evaluate the plan")
    confirm.add_argument("--database", required=True)
    confirm.add_argument("--record-id", required=True)
    confirm.add_argument("--outcome", required=True, choices=("approved", "rejected"))
    confirm.add_argument("--reason", required=True)
    confirm.add_argument("--output")
    availability = cli.add_parser("availability", help="record an availability window change and re-evaluate")
    availability.add_argument("--database", required=True)
    availability.add_argument("--record-id", required=True)
    availability.add_argument("--window", required=True, type=float)
    availability.add_argument("--output")
    promote = cli.add_parser("promote", help="promote a recommended substitute into the confirmation flow")
    promote.add_argument("--database", required=True)
    promote.add_argument("--substitution-id", required=True)
    promote.add_argument("--reason", required=True)
    promote.add_argument("--output")
    plan = cli.add_parser("plan", help="re-evaluate the current seat plan and export the bundle")
    plan.add_argument("--database", required=True)
    plan.add_argument("--output", required=True)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "run":
        result = run(args.fixture, args.database, args.output)
    elif args.command == "verify":
        result = verify(args.database, args.output)
    elif args.command == "inspect":
        result = Application(args.database).inspect()
    elif args.command == "confirm":
        result = Application(args.database).confirm(
            args.record_id, args.outcome, args.reason, args.output
        )
    elif args.command == "availability":
        result = Application(args.database).change_availability(
            args.record_id, args.window, args.output
        )
    elif args.command == "promote":
        result = Application(args.database).promote_substitute(
            args.substitution_id, args.reason, args.output
        )
    else:
        application = Application(args.database)
        application.evaluate_plan()
        result = {"manifest": application.export_current(args.output)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
