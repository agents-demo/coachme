"""CLI command: analyze a session video."""

from __future__ import annotations

from topspin_review.core import Params, resolve
from topspin_review.core.bootstrap import run as run_async
from topspin_review.integrations.agents import ConfigError
from topspin_review.surfaces.cli.commands._display import print_report


def _parse_box(text: str | None) -> tuple[float, float, float, float] | None:
    if not text:
        return None
    try:
        parts = [float(x) for x in text.split(",")]
    except ValueError as exc:
        raise SystemExit("--box needs 4 comma-separated numbers: left,top,right,bottom") from exc
    if len(parts) != 4:
        raise SystemExit("--box needs 4 comma-separated numbers: left,top,right,bottom")
    return (parts[0], parts[1], parts[2], parts[3])


def run(path: str, box: str | None = None, agentic: bool = False, mode: str | None = None) -> int:
    from topspin_review.core import get_strategy

    strategy = get_strategy(mode) if mode else resolve(agentic)

    try:
        outcome = run_async(strategy.analyze(Params(video_path=path, region_box=_parse_box(box))))
    except (ConfigError, FileNotFoundError) as exc:
        print(f"error: {exc}")
        return 2
    result = outcome.get("result") if isinstance(outcome, dict) else None
    output = result.get("output") if isinstance(result, dict) else str(result)
    print("\n[coach] " + (output or "").strip())
    print(f"\n(frames analyzed: {outcome.get('frames')})")
    if outcome.get("report_path"):
        print(f"report saved to: {outcome['report_path']}")
    usage = (outcome.get("report") or {}).get("usage") or {}
    if usage:
        print(
            f"(usage: {usage.get('calls', 0)} calls · "
            f"{usage.get('total_tokens', 0)} tokens · "
            f"vision {usage.get('vision', {}).get('total_tokens', 0)} / "
            f"text {usage.get('text', {}).get('total_tokens', 0)})"
        )
    print_report(outcome.get("report") or {})
    return 0
