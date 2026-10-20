from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from coachme.benchmark.core.data.paths import atomic_write_json, read_json, sha256_text


def canonical(mapping: dict[str, Any], clip_id: str) -> dict[str, str]:
    entry = (mapping.get("clips") or {}).get(clip_id) or {}
    return {"A": str(entry.get("A", "")), "B": str(entry.get("B", ""))}


def stored(mapping: dict[str, Any], rater: str, clip_id: str) -> dict[str, str] | None:
    entry = ((mapping.get("raters") or {}).get(rater) or {}).get(clip_id)
    if not isinstance(entry, dict) or entry.get("A") not in {"standard", "investigator"}:
        return None
    if entry.get("B") not in {"standard", "investigator"}:
        return None
    return {"A": str(entry["A"]), "B": str(entry["B"])}


def ensure_rater_mapping(run_dir: str | Path, run_id: str, rater: str, clip_id: str) -> dict[str, str]:
    """Return and persist a deterministic per-rater A/B order."""
    path = Path(run_dir).resolve() / "mapping.json"
    mapping = read_json(path, {})
    mapping = mapping if isinstance(mapping, dict) else {}
    existing = stored(mapping, rater, clip_id)
    if existing:
        return existing
    base = canonical(mapping, clip_id)
    if not base["A"] or not base["B"]:
        base = {"A": "standard", "B": "investigator"}
    names = [base["A"], base["B"]]
    seed = int(sha256_text(f"{run_id}:{rater}:{clip_id}")[:16], 16)
    random.Random(seed).shuffle(names)
    raters = mapping.setdefault("raters", {})
    raters.setdefault(rater, {})[clip_id] = {"A": names[0], "B": names[1]}
    atomic_write_json(path, mapping)
    return {"A": names[0], "B": names[1]}


def preference_mode(item: dict[str, Any], mapping: dict[str, Any], rater: str, clip_id: str) -> str:
    preferred = str(item.get("preferred", "tie"))
    if preferred not in {"A", "B"}:
        return "tie"
    item_mapping = item.get("mapping")
    if isinstance(item_mapping, dict) and item_mapping.get(preferred):
        return str(item_mapping[preferred])
    stored_mapping = stored(mapping, rater, clip_id) or canonical(mapping, clip_id)
    return str(stored_mapping.get(preferred, "tie"))


__all__ = ["canonical", "ensure_rater_mapping", "preference_mode", "stored"]
