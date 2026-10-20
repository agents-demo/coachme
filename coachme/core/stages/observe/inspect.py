"""Focused window inspection for investigator mode.

The investigator asks the vision model a specific question about a sampled
window. This module renders one sheet inside the inspector workspace and asks for
a strict JSON answer. It deliberately does not expose shell or list tools in the
prompt; the inspector should only read the provided image.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

from coachme.core.stages.observe import render_images
from coachme.core.stages.observe.ask_agent import ask
from coachme.core.video import imaging

INSPECT_SYSTEM = (
    "You are a racket-sport video analyst. Read only the image path you are given. "
    "Do not call bash, list_files, or any tool other than read_file. Do not inspect "
    "files with Python. After read_file returns the image, answer the question with "
    "ONLY the requested JSON. Never invent spin, ball speed, or exact angles."
)

INSPECT_PROMPT = """These are {n} frames sampled in order from {start:.2f}s to {end:.2f}s
of a {sport} session. Player: level {level}, {hand}-handed, working on {goal}.

Question: {question}

Read this image once: {sheet}
Do NOT call bash, list_files, or any tool other than read_file. Do NOT inspect
the file with Python. After read_file returns the image, answer immediately.

Answer only what the frames show. Do not invent spin, ball speed or exact
angles. If the racket face, wrist or contact point is not visible, say so.
Return ONLY this JSON:
{{
  "observations": "short paragraph",
  "signals": [
    {{"signal": "short finding", "evidence_times": [seconds], "confidence": "high|medium|low"}}
  ],
  "limitations": ["..."]
}}"""


async def inspect(
    agent: Any,
    frames: list[Image.Image],
    timestamps: list[float],
    question: str,
    profile: dict,
    *,
    media_dir: Path,
    start: float,
    end: float,
) -> dict:
    """Ask the restricted vision inspector about one window."""
    if not frames:
        return {"observations": "", "signals": [], "limitations": ["No frames in window."]}
    sheet = imaging.contact_sheet(frames, timestamps, cols=min(4, len(frames)))
    name = f"look_{int(round(start * 1000))}_{int(round(end * 1000))}.png"
    sheet_path = render_images.save(sheet, media_dir, name)
    prompt = INSPECT_PROMPT.format(
        n=len(frames),
        start=float(start),
        end=float(end),
        sport=profile.get("sport", "table tennis"),
        level=profile.get("level", "unknown"),
        hand=profile.get("dominant_hand", "right"),
        goal=profile.get("goal", "improve"),
        question=str(question).strip(),
        sheet=sheet_path,
    )
    parsed = await ask(agent, prompt)
    if not parsed.get("observations") and not parsed.get("signals"):
        parsed = await ask(agent, prompt + "\nReturn only the JSON object, with no prose.")
    parsed.setdefault("observations", "")
    parsed.setdefault("signals", [])
    parsed.setdefault("limitations", [])
    parsed["sheet_path"] = sheet_path
    return _clean(parsed, start=start, end=end)


def _clean(parsed: dict, *, start: float, end: float) -> dict:
    signals = []
    for item in parsed.get("signals") or []:
        if not isinstance(item, dict) or not item.get("signal"):
            continue
        times = []
        for value in item.get("evidence_times") or []:
            try:
                t = round(float(value), 2)
            except (TypeError, ValueError):
                continue
            if start - 0.15 <= t <= end + 0.15:
                times.append(t)
        confidence = str(item.get("confidence", "low")).lower()
        if confidence not in {"high", "medium", "low"}:
            confidence = "low"
        signals.append({"signal": str(item["signal"]), "evidence_times": times, "confidence": confidence})
    parsed["signals"] = signals
    parsed["limitations"] = [str(item) for item in (parsed.get("limitations") or [])]
    return parsed


__all__ = ["INSPECT_PROMPT", "INSPECT_SYSTEM", "inspect"]
