"""Application settings, read from the environment (.env).

Only behaviour that shapes *what the app does* lives here (sampling, feature
toggles, budgets). Anything about reaching model/embedding endpoints — provider,
keys, URLs, model names, timeouts — lives in :mod:`coachme.integrations.agents.settings`.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


# --- vision sampling ------------------------------------------------------- #
def max_frames() -> int:
    return int(os.getenv("VISION_MAX_FRAMES", "12"))


def max_width() -> int:
    return int(os.getenv("VISION_MAX_WIDTH", "768"))


def zoom_frames() -> int:
    """Frames sampled inside the windows the first pass asks to inspect."""
    return int(os.getenv("VISION_ZOOM_FRAMES", "6"))


def max_windows() -> int:
    return int(os.getenv("VISION_MAX_WINDOWS", "3"))


def zoom_fps() -> float:
    """Target frames-per-second when sampling a zoom burst inside a window."""
    return float(os.getenv("VISION_ZOOM_FPS", "8"))


def use_cache() -> bool:
    return _bool("VISION_CACHE", "true")


def max_seconds() -> float:
    """Cap analysis to the first N seconds of a clip (0 = whole clip)."""
    return float(os.getenv("VISION_MAX_SECONDS", "0"))


def probe_budget() -> int:
    """How many cheap frames to read when locating motion-heavy windows."""
    return int(os.getenv("VISION_PROBE_BUDGET", "64"))


# --- analysis behaviour ---------------------------------------------------- #
def agentic_mode() -> bool:
    """Run the model-driven strategy instead of the fixed one."""
    return _bool("AGENTIC_MODE", "false")


def demo_fallback() -> bool:
    """On a failed run, fall back to the last recorded report for the same clip."""
    return _bool("DEMO_FALLBACK", "true")


def verify_reports() -> bool:
    """Run a verification pass that drops unsupported issues."""
    return _bool("VERIFY_REPORTS", "true")


def clips_enabled() -> bool:
    """Cut short highlight clips around flagged moments."""
    return _bool("HIGHLIGHT_CLIPS", "true")


def ball_model() -> str:
    """Ball detector mode: ``auto`` (use the ONNX model when present) or ``off``."""
    return os.getenv("BALL_MODEL", "auto").strip().lower()


def ball_sample_fps() -> float:
    """Target fps for the dedicated ball-tracking pass (the ball is on screen briefly)."""
    return float(os.getenv("BALL_SAMPLE_FPS", "10"))


def ball_max_frames() -> int:
    """Upper bound on frames in the dedicated ball pass."""
    return int(os.getenv("BALL_MAX_FRAMES", "400"))


def retrieval_enabled() -> bool:
    """Add lexically-retrieved past sessions to the report context."""
    return _bool("RETRIEVAL", "true")


# --- investigator budgets -------------------------------------------------- #
def investigator_max_tool_calls() -> int:
    return int(os.getenv("INVESTIGATOR_MAX_TOOL_CALLS", "24"))


def investigator_max_seconds() -> float:
    return float(os.getenv("INVESTIGATOR_MAX_SECONDS", "360"))


def investigator_max_tokens() -> int:
    return int(os.getenv("INVESTIGATOR_MAX_TOKENS", "80000"))


def investigator_max_frames() -> int:
    return int(os.getenv("INVESTIGATOR_MAX_FRAMES", "160"))


def investigator_max_window_seconds() -> float:
    return float(os.getenv("INVESTIGATOR_MAX_WINDOW_SECONDS", "10"))


def investigator_max_window_frames() -> int:
    return int(os.getenv("INVESTIGATOR_MAX_WINDOW_FRAMES", "12"))


def rails() -> list[str]:
    """Names of the backend rails to enable on report agents (``RAILS`` env).

    ``true``/``false`` toggle the default set; otherwise a comma-separated list of
    names (known: ``token_budget``, ``memory``). The rails themselves are built by
    the backend, not here.
    """
    raw = os.getenv("RAILS", "true").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return ["token_budget", "memory"]
    if raw in {"0", "false", "no", "off", ""}:
        return []
    return [name.strip() for name in raw.split(",") if name.strip()]
