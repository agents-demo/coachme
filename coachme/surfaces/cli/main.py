"""Command-line interface for CoachMe: argument parsing and dispatch.

Usage:
    python -m coachme.surfaces.cli profile
    python -m coachme.surfaces.cli analyze [video_path]
    python -m coachme.surfaces.cli history
"""

from __future__ import annotations

import argparse
import sys

from coachme.core.bootstrap import setup
from coachme.integrations.storage import runtime
from coachme.surfaces.cli.commands import analyze, compare, export, history, profile, reset


def _configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    setup()
    _configure_console()

    parser = argparse.ArgumentParser(prog="coachme", description="CoachMe CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("profile", help="set your profile")
    p_analyze = sub.add_parser("analyze", help="analyze a session video")
    p_analyze.add_argument("path", nargs="?", default=str(runtime.DATA_DIR / "sample.mp4"), help="video file path")
    p_analyze.add_argument(
        "--box",
        default=None,
        help="normalized player region 'left,top,right,bottom' (0..1) to ignore other people",
    )
    p_analyze.add_argument(
        "--agentic",
        action="store_true",
        help="let the model drive analysis by inspecting windows itself (slower; alias for --mode agentic)",
    )
    p_analyze.add_argument(
        "--mode",
        default=None,
        choices=["deterministic", "agentic", "investigator"],
        help="analysis strategy; overrides --agentic when set (investigator is experimental)",
    )
    sub.add_parser("history", help="show recent reports")
    p_export = sub.add_parser("export", help="export the latest (or a specific) report")
    p_export.add_argument("video", nargs="?", default=None, help="video file name")
    p_compare = sub.add_parser("compare", help="compare two analyzed videos")
    p_compare.add_argument("video_a", help="older video file name")
    p_compare.add_argument("video_b", help="newer video file name")
    sub.add_parser("reset", help="clear saved reports")

    args = parser.parse_args(argv)

    if args.command == "profile":
        return profile.run()
    if args.command == "analyze":
        return analyze.run(
            args.path,
            getattr(args, "box", None),
            getattr(args, "agentic", False),
            getattr(args, "mode", None),
        )
    if args.command == "history":
        return history.run()
    if args.command == "export":
        return export.run(args.video)
    if args.command == "compare":
        return compare.run(args.video_a, args.video_b)
    if args.command == "reset":
        return reset.run()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
