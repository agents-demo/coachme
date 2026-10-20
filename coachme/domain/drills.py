"""A small catalog of common racket-sport drills: a short cue + progression.

Pure (stdlib only). The report's drills are free text; we match each one to a
catalog entry by keyword so the UI can show a practical cue and a next step.
"""

from __future__ import annotations

CATALOG: list[dict] = [
    {
        "keys": ("split-step", "split step", "timing hop"),
        "name": "Split-step",
        "cue": "Small hop as the opponent contacts; land as the ball leaves their racket.",
        "progression": "Add it to shadow footwork, then to multi-ball.",
    },
    {
        "keys": ("footwork", "shuffle", "step-and-plant", "step then", "step into"),
        "name": "Footwork",
        "cue": "Step the near foot into the hitting zone before you swing.",
        "progression": "Alternate wide and middle to force a committed step.",
    },
    {
        "keys": ("recovery", "re-set", "reset", "re-set drill"),
        "name": "Recovery",
        "cue": "Re-settle into a balanced ready crouch after every shot.",
        "progression": "Tap a neutral marker between balls.",
    },
    {
        "keys": ("weight transfer", "load", "crouch", "dip-and-drive", "dip and drive"),
        "name": "Load & drive",
        "cue": "Dip, then drive from the legs — the hips lead the arm.",
        "progression": "Add a visible crouch before each forehand.",
    },
    {
        "keys": ("shadow", "no ball"),
        "name": "Shadow swings",
        "cue": "Focus purely on the movement pattern.",
        "progression": "Add a small squat load on each landing.",
    },
    {
        "keys": ("multi-ball", "multiball"),
        "name": "Multi-ball",
        "cue": "High volume to groove the pattern.",
        "progression": "Randomise placement once it's clean.",
    },
    {
        "keys": ("serve", "toss"),
        "name": "Serve",
        "cue": "Consistent toss, full extension.",
        "progression": "Add target zones.",
    },
    {
        "keys": ("forehand",),
        "name": "Forehand",
        "cue": "Compact swing; close the racket early.",
        "progression": "Progress from placement to power.",
    },
    {
        "keys": ("backhand",),
        "name": "Backhand",
        "cue": "Compact; keep the elbow stable.",
        "progression": "Cross-court, then down-the-line.",
    },
]


def lookup(drill_text: str) -> dict | None:
    """Match a free-text drill to a catalog entry (name + cue + progression), or ``None``."""
    text = str(drill_text or "").lower()
    for entry in CATALOG:
        if any(key in text for key in entry["keys"]):
            return {"name": entry["name"], "cue": entry["cue"], "progression": entry["progression"]}
    return None
