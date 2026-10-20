"""Backfill ``metrics.footwork_series`` into saved reports that predate it.

``footwork_series`` (the lower-body left–right position over time) is computed
deterministically from the clip — no model calls — so older reports can be
refreshed in place instead of being re-analysed.

Usage:
    python scripts/backfill_footwork.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from coachme.core import config  # noqa: E402
from coachme.core.stages.measure import sampling  # noqa: E402
from coachme.core.video import metrics  # noqa: E402
from coachme.integrations.storage import runtime  # noqa: E402


def main() -> None:
    data = Path(runtime.DATA_DIR)
    done = skipped = failed = 0
    for path in sorted(data.glob("*_report.json")):
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive
            print(f"skip (unreadable): {path.name}: {exc}")
            skipped += 1
            continue

        m = report.get("metrics") or {}
        if m.get("footwork_series"):
            skipped += 1
            continue

        source = report.get("source")
        if not source or not Path(source).exists() or sampling.is_image(source):
            print(f"skip (no video): {path.name}")
            skipped += 1
            continue

        try:
            _meta, frames, times = sampling.sample_frames(source, config.max_frames(), config.use_cache())
            if not frames:
                print(f"skip (no frames): {path.name}")
                skipped += 1
                continue
            fresh = metrics.analyze(frames, times, with_pose=False)
            series = fresh.get("footwork_series") or []
            if not series:
                print(f"skip (empty series): {path.name}")
                skipped += 1
                continue
            m["footwork_series"] = series
            report["metrics"] = m
            path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"patched {path.name} ({len(series)} points)")
            done += 1
        except Exception as exc:
            print(f"failed {path.name}: {exc}")
            failed += 1

    print(f"\ndone={done} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    main()
