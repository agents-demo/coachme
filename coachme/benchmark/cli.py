"""Command-line entry point for the CoachMe benchmark."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from coachme.benchmark.manual_review import (
    import_hallucination_review,
    import_tool_review,
    write_hallucination_template,
    write_tool_template,
)
from coachme.benchmark.negative_control import make_negative_control
from coachme.benchmark.paths import BenchmarkError, data_root
from coachme.benchmark.privacy import prune_expired, withdraw_clip
from coachme.benchmark.ratings import import_rating_csv, rater_packet_zip
from coachme.benchmark.review import import_review, write_template
from coachme.benchmark.runner import DEFAULT_REQUIRED_CLIPS, DEFAULT_REQUIRED_RATERS, run_benchmark
from coachme.benchmark.scorer import score_run
from coachme.benchmark.stability import compare_runs
from coachme.benchmark.ui.server.auth import ROLES, UserStore


def _modes(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="coachme-benchmark", description="CoachMe benchmark runner")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="run one or more analysis modes over a manifest")
    p_run.add_argument("--manifest", required=True, help="path to manifest.json")
    p_run.add_argument("--out", default=None, help="output run directory (default: benchmark/runs/<run_id>)")
    p_run.add_argument("--modes", default="standard,investigator", help="comma-separated: standard,guided,investigator")
    p_run.add_argument("--environment", default="local", choices=["local", "staging", "production"])
    p_run.add_argument("--label", default=None, help="optional run label, e.g. pilot")
    p_run.add_argument("--required-clips", type=int, default=DEFAULT_REQUIRED_CLIPS)
    p_run.add_argument("--required-raters", type=int, default=DEFAULT_REQUIRED_RATERS)
    p_run.add_argument("--resume", action="store_true", help="skip clips with matching raw output")
    p_run.add_argument("--fail-fast", action="store_true")
    p_run.add_argument(
        "--negative-control",
        action="store_true",
        help="run the stripped-prompt known-bad baseline and label the run negative-control",
    )

    p_score = sub.add_parser("score", help="compute score.json and report.md")
    p_score.add_argument("--run", required=True, help="run directory")
    p_score.add_argument("--manifest", default=None, help="override manifest path")
    p_score.add_argument("--labels", default=None, help="override labels path")

    p_import = sub.add_parser("import", help="import one rater's blind-rating CSV")
    p_import.add_argument("--run", required=True, help="run directory")
    p_import.add_argument("--rater", required=True)
    p_import.add_argument("--file", required=True)
    p_import.add_argument("--force", action="store_true", help="replace an already submitted sheet")

    p_packets = sub.add_parser("packets", help="export separate blind rater packets")
    p_packets.add_argument("--run", required=True, help="run directory")
    p_packets.add_argument("--raters", required=True, help="comma-separated rater ids")
    p_packets.add_argument("--out", required=True, help="output zip path")

    p_review = sub.add_parser("evidence-review", help="write a manual evidence-review CSV template")
    p_review.add_argument("--run", required=True, help="run directory")
    p_review.add_argument("--out", required=True, help="output CSV path")

    p_review_import = sub.add_parser("evidence-import", help="import a completed evidence-review CSV")
    p_review_import.add_argument("--run", required=True, help="run directory")
    p_review_import.add_argument("--file", required=True, help="reviewed CSV path")
    p_review_import.add_argument("--reviewer", required=True, help="reviewer name")

    p_negative = sub.add_parser("negative-control", help="build a known-bad run from an existing run")
    p_negative.add_argument("--run", required=True, help="source run directory")
    p_negative.add_argument("--out", required=True, help="output run directory")

    p_tool = sub.add_parser("tool-review", help="write a tool-appropriateness CSV template")
    p_tool.add_argument("--run", required=True)
    p_tool.add_argument("--out", required=True)

    p_tool_import = sub.add_parser("tool-import", help="import a completed tool-appropriateness CSV")
    p_tool_import.add_argument("--run", required=True)
    p_tool_import.add_argument("--file", required=True)
    p_tool_import.add_argument("--reviewer", required=True)

    p_hallucination = sub.add_parser("hallucination-review", help="write a hallucination-review CSV template")
    p_hallucination.add_argument("--run", required=True)
    p_hallucination.add_argument("--out", required=True)

    p_hallucination_import = sub.add_parser("hallucination-import", help="import a completed hallucination-review CSV")
    p_hallucination_import.add_argument("--run", required=True)
    p_hallucination_import.add_argument("--file", required=True)
    p_hallucination_import.add_argument("--reviewer", required=True)

    p_withdraw = sub.add_parser("withdraw", help="withdraw consent and delete a clip and derived artifacts")
    p_withdraw.add_argument("--manifest", required=True)
    p_withdraw.add_argument("--clip", required=True)
    p_withdraw.add_argument("--reason", required=True)
    p_withdraw.add_argument("--data-root", default=None)

    p_prune = sub.add_parser("prune", help="withdraw clips whose consent or retention has expired")
    p_prune.add_argument("--manifest", required=True)
    p_prune.add_argument("--data-root", default=None)

    p_stability = sub.add_parser("stability", help="compare two scored runs for reproducibility")
    p_stability.add_argument("--run", required=True, help="first run directory")
    p_stability.add_argument("--against", required=True, help="second run directory")

    p_user_add = sub.add_parser("user-add", help="create a benchmark user")
    p_user_add.add_argument("--username", required=True)
    p_user_add.add_argument("--password", default=None, help="prompt when omitted")
    p_user_add.add_argument("--role", default="operator", choices=sorted(ROLES))
    p_user_add.add_argument("--tenant", default="default")
    p_user_add.add_argument("--data", default=None)

    p_user_list = sub.add_parser("user-list", help="list benchmark users")
    p_user_list.add_argument("--data", default=None)

    p_user_remove = sub.add_parser("user-remove", help="remove a benchmark user")
    p_user_remove.add_argument("--username", required=True)
    p_user_remove.add_argument("--data", default=None)

    p_ui = sub.add_parser("ui", help="local or remote review UI")
    p_ui.add_argument("--data", default=None)
    p_ui.add_argument("--port", type=int, default=8765)
    p_ui.add_argument("--host", default="127.0.0.1")
    p_ui.add_argument("--allow-remote", action="store_true", help="allow a non-loopback bind")
    p_ui.add_argument("--auth", action="store_true", help="require account login")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            out = Path(args.out).expanduser() if args.out else data_root() / "runs"
            if args.out is None:
                from coachme.benchmark.paths import run_id

                out = out / run_id()
            run = run_benchmark(
                manifest_path=args.manifest,
                out=out,
                modes=_modes(args.modes),
                environment=args.environment,
                label=args.label,
                required_clips=args.required_clips,
                required_raters=args.required_raters,
                resume=args.resume,
                fail_fast=args.fail_fast,
                negative_control=args.negative_control,
            )
            print(f"run: {out}")
            print(f"status: {run.get('status')}  clips: {run.get('clips_complete')}/{run.get('clips_total')}")
            print(f'next: coachme-benchmark score --run "{out}"')
            return 3 if run.get("status") == "failed" else 0
        if args.command == "score":
            score = score_run(args.run, manifest_path=args.manifest, labels_path=args.labels)
            print(f"release_eligible: {score['release_eligible']}")
            print("blocked_reasons: " + (", ".join(score.get("blocked_reasons") or []) or "none"))
            print(f"score: {Path(args.run).resolve() / 'score.json'}")
            return 0
        if args.command == "import":
            sheet = import_rating_csv(
                run_dir=args.run,
                rater=args.rater,
                csv_path=args.file,
                force=args.force,
            )
            print(f"imported {len(sheet['clips'])} ratings for {sheet['rater']}")
            return 0
        if args.command == "packets":
            raters = [item.strip() for item in args.raters.split(",") if item.strip()]
            data = rater_packet_zip(args.run, raters)
            target = Path(args.out).expanduser()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            print(f"packets: {target} ({len(raters)} rater(s))")
            return 0
        if args.command == "evidence-review":
            target = write_template(args.run, args.out)
            print(f"review template: {target}")
            return 0
        if args.command == "evidence-import":
            result = import_review(args.run, args.file, reviewer=args.reviewer)
            print(f"imported {result['imported']} reviewed finding(s) from {result['reviewer']}")
            return 0
        if args.command == "negative-control":
            run = make_negative_control(args.run, args.out)
            print(f"negative-control run: {Path(args.out).resolve()}")
            print(f"clips: {len(run.get('clips') or {})}")
            return 0
        if args.command == "tool-review":
            target = write_tool_template(args.run, args.out)
            print(f"tool review template: {target}")
            return 0
        if args.command == "tool-import":
            result = import_tool_review(args.run, args.file, reviewer=args.reviewer)
            print(f"imported {result['imported']} tool review(s) from {result['reviewer']}")
            return 0
        if args.command == "hallucination-review":
            target = write_hallucination_template(args.run, args.out)
            print(f"hallucination review template: {target}")
            return 0
        if args.command == "hallucination-import":
            result = import_hallucination_review(args.run, args.file, reviewer=args.reviewer)
            print(f"imported {result['imported']} hallucination review(s) from {result['reviewer']}")
            return 0
        if args.command == "withdraw":
            event = withdraw_clip(args.manifest, args.clip, reason=args.reason, data_root=args.data_root)
            print(f"withdrew {event['clip_id']}: {len(event['removed'])} path(s) removed")
            return 0
        if args.command == "prune":
            removed = prune_expired(args.manifest, data_root=args.data_root)
            print(f"pruned {len(removed)} clip(s)")
            return 0
        if args.command == "stability":
            result = compare_runs(args.run, args.against)
            print(f"stable: {result['stable']}")
            print(f"within_48h: {result['within_48h']}  same_config: {result['same_config']}")
            print(f"differences: {result['differences']}")
            print(f"written: {Path(args.run).resolve() / 'stability.json'}")
            return 0 if result["stable"] else 1
        if args.command == "user-add":
            import getpass

            password = args.password or getpass.getpass("Password: ")
            user = UserStore(data_root(args.data)).add(
                args.username,
                password,
                role=args.role,
                tenant=args.tenant,
            )
            print(f"created {user['username']} role={user['role']} tenant={user['tenant']}")
            return 0
        if args.command == "user-list":
            for user in UserStore(data_root(args.data)).list():
                print(f"{user['username']}\t{user['role']}\t{user['tenant']}\t{user.get('display_name', '')}")
            return 0
        if args.command == "user-remove":
            removed = UserStore(data_root(args.data)).remove(args.username)
            print("removed" if removed else "user not found")
            return 0 if removed else 1
        if args.command == "ui":
            import os
            import threading
            import webbrowser

            loopback = args.host in {"127.0.0.1", "localhost", "::1"}
            if not loopback and not args.allow_remote:
                raise BenchmarkError("non-loopback bind requires --allow-remote")
            if args.auth:
                os.environ["COACHME_BENCHMARK_AUTH"] = "1"
            if not loopback and os.getenv("COACHME_BENCHMARK_AUTH", "").lower() not in {"1", "true", "yes", "on"}:
                raise BenchmarkError("remote access requires --auth and at least one user")

            from coachme.benchmark.ui.server.app import create_app

            try:
                import uvicorn
            except ImportError as exc:
                raise BenchmarkError("the UI requires the 'api' extra: pip install -e .[api]") from exc

            url = f"http://{args.host}:{args.port}/"
            if loopback:
                threading.Timer(1.0, lambda: webbrowser.open(url)).start()
            print(f"benchmark UI: {url}")
            uvicorn.run(create_app(args.data), host=args.host, port=args.port, log_level="warning")
            return 0
    except BenchmarkError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
