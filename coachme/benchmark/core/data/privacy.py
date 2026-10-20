from __future__ import annotations

import json
import shutil
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from coachme.benchmark.core.data.paths import BenchmarkError, atomic_write_json, read_json
from coachme.benchmark.core.data.schemas import clip_path, load_manifest


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _remove(path: Path, removed: list[str], root: Path) -> None:
    if not path.exists():
        return
    try:
        relative = str(path.relative_to(root))
    except ValueError:
        relative = str(path)
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            path.unlink()
        except OSError:
            return
    removed.append(relative)


def _drop_clip_from_json(path: Path, clip_id: str, root: Path, removed: list[str]) -> None:
    data = read_json(path, None)
    if not isinstance(data, dict):
        return
    changed = False
    for key in ("clips",):
        target = data.get(key)
        if isinstance(target, dict) and clip_id in target:
            target.pop(clip_id, None)
            changed = True
    raters = data.get("raters")
    if isinstance(raters, dict):
        for entry in raters.values():
            if isinstance(entry, dict) and clip_id in entry:
                entry.pop(clip_id, None)
                changed = True
    if changed:
        atomic_write_json(path, data)
        try:
            removed.append(str(path.relative_to(root)))
        except ValueError:
            removed.append(str(path))


def withdraw_clip(
    manifest_path: str | Path,
    clip_id: str,
    *,
    reason: str,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    manifest_file = Path(manifest_path).expanduser().resolve()
    manifest, problems = load_manifest(manifest_file, require_files=False, verify_checksums=False)
    if problems:
        raise BenchmarkError("invalid manifest:\n- " + "\n- ".join(problems))
    clips = manifest.get("clips") or []
    clip = next((item for item in clips if item.get("id") == clip_id), None)
    if not clip:
        raise BenchmarkError(f"unknown clip: {clip_id}")
    root = Path(data_root).expanduser().resolve() if data_root else manifest_file.parent
    removed: list[str] = []
    try:
        source = clip_path(manifest, clip, manifest_file)
        _remove(source, removed, root)
    except BenchmarkError:
        pass
    manifest["clips"] = [item for item in clips if item.get("id") != clip_id]
    atomic_write_json(manifest_file, manifest)
    labels_path = manifest_file.parent / "labels.json"
    labels = read_json(labels_path, None)
    if isinstance(labels, dict):
        label_clips = labels.get("clips")
        if isinstance(label_clips, dict):
            label_clips.pop(clip_id, None)
            atomic_write_json(labels_path, labels)
    runs_dir = root / "runs"
    if runs_dir.is_dir():
        for run_dir in runs_dir.iterdir():
            if not run_dir.is_dir():
                continue
            run_data = read_json(run_dir / "run.json", {})
            if not isinstance(run_data, dict) or clip_id not in (run_data.get("clips") or {}):
                continue
            for mode in ("standard", "guided", "investigator"):
                _remove(run_dir / "raw" / mode / f"{clip_id}.json", removed, root)
                _remove(run_dir / "traces" / mode / f"{clip_id}.json", removed, root)
                _remove(run_dir / "analysis" / mode / clip_id, removed, root)
            _remove(run_dir / "blind" / clip_id, removed, root)
            _drop_clip_from_json(run_dir / "run.json", clip_id, root, removed)
            updated = read_json(run_dir / "run.json", {})
            if isinstance(updated, dict) and isinstance(updated.get("clips"), dict):
                updated["clips_total"] = len(updated["clips"])
                updated["clips_complete"] = sum(
                    1
                    for state in updated["clips"].values()
                    if isinstance(state, dict) and state.get("standard", {}).get("status") == "complete"
                )
                atomic_write_json(run_dir / "run.json", updated)
            _drop_clip_from_json(run_dir / "mapping.json", clip_id, root, removed)
            _drop_clip_from_json(run_dir / "adjudication.json", clip_id, root, removed)
            for path in (run_dir / "ratings").glob("*.json"):
                _drop_clip_from_json(path, clip_id, root, removed)
            for name in ("score.json", "report.md", "rating_sheet.csv"):
                _remove(run_dir / name, removed, root)
    event = {
        "at": _now(),
        "clip_id": clip_id,
        "reason": reason.strip() or "withdrawn",
        "removed": removed,
    }
    manifest_out = root / "deletion_manifest.jsonl"
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    with manifest_out.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def prune_expired(
    manifest_path: str | Path,
    *,
    data_root: str | Path | None = None,
    today: date | None = None,
) -> list[dict[str, Any]]:
    manifest_file = Path(manifest_path).expanduser().resolve()
    manifest, problems = load_manifest(manifest_file, require_files=False, verify_checksums=False)
    if problems:
        raise BenchmarkError("invalid manifest:\n- " + "\n- ".join(problems))
    current = today or date.today()
    removed: list[dict[str, Any]] = []
    for clip in list(manifest.get("clips") or []):
        consent = clip.get("consent") if isinstance(clip, dict) else None
        consent = consent if isinstance(consent, dict) else {}
        expires = consent.get("expires")
        granted = consent.get("date")
        retention = consent.get("retention_days")
        expired = False
        if isinstance(expires, str):
            try:
                expired = date.fromisoformat(expires) < current
            except ValueError:
                expired = False
        if not expired and isinstance(granted, str) and isinstance(retention, int):
            try:
                expired = date.fromisoformat(granted).toordinal() + retention < current.toordinal()
            except ValueError:
                expired = False
        if expired:
            removed.append(
                withdraw_clip(
                    manifest_file,
                    str(clip.get("id")),
                    reason="retention_expired",
                    data_root=data_root,
                )
            )
    return removed


__all__ = ["prune_expired", "withdraw_clip"]
