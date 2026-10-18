"""Thread-safe progress reporting for long-running analysis runs.

The analysis updates a :class:`Progress` from the worker thread; a UI (e.g. the
Streamlit app) polls :meth:`Progress.snapshot` from the main thread and renders a
progress bar/stage. It also records how long each stage took. ``tick`` is a no-op
when no reporter is attached.
"""

from __future__ import annotations

import threading
import time


class Progress:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stage = "startup"  # the initial placeholder; its time = pre-run overhead (imports/setup)
        self._pct = 0.0
        self._detail = ""
        self._done = False
        self._error: str | None = None
        self._stem: str | None = None
        self._start = time.monotonic()
        self._last = self._start
        self._timings: list[dict] = []
        self._events: list[dict] = []
        self._event_seq = 0

    def update(self, stage: str, pct: float, detail: str = "") -> None:
        with self._lock:
            now = time.monotonic()
            self._timings.append({"stage": self._stage, "seconds": round(now - self._last, 2)})
            self._last = now
            self._stage = stage
            self._pct = float(pct)
            self._detail = detail

    def event(self, kind: str, **payload: object) -> None:
        """Append a bounded investigator event (tool call, warning, stop)."""
        with self._lock:
            self._event_seq += 1
            event = {
                "seq": self._event_seq,
                "t": round(time.monotonic() - self._start, 2),
                "kind": str(kind),
                **payload,
            }
            self._events.append(event)
            if len(self._events) > 200:
                del self._events[:-200]

    def finish(self, stem: str | None = None) -> None:
        with self._lock:
            self._stage = "done"
            self._pct = 100.0
            self._done = True
            self._stem = stem

    def fail(self, message: str) -> None:
        with self._lock:
            self._done = True
            self._error = message

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "stage": self._stage,
                "pct": self._pct,
                "detail": self._detail,
                "done": self._done,
                "error": self._error,
                "stem": self._stem,
                "elapsed": round(time.monotonic() - self._start, 2),
                "timings": list(self._timings),
                "events": list(self._events),
            }

    def stage(self) -> str:
        """The stage currently running (for attributing telemetry to a step)."""
        with self._lock:
            return self._stage


def tick(progress: Progress | None, stage: str, pct: float, detail: str = "") -> None:
    """Update ``progress`` if present; never raises."""
    if progress is not None:
        try:
            progress.update(stage, pct, detail)
        except Exception:
            pass
