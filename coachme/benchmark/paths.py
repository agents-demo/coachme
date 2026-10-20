"""Filesystem helpers for the benchmark subsystem.

The benchmark deliberately uses its own data root. Real clips, labels, ratings
and runs must never be written into ``runtime/data`` or committed to git.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = PROJECT_ROOT / "benchmark-data"


class BenchmarkError(ValueError):
    """A user-facing benchmark error."""


def data_root(override: str | Path | None = None) -> Path:
    """Resolve the benchmark data root."""
    if override:
        return Path(override).expanduser().resolve()
    raw = os.getenv("COACHME_BENCHMARK_DATA", "").strip()
    return Path(raw).expanduser().resolve() if raw else DEFAULT_DATA_ROOT


def ensure_data_root(root: str | Path | None = None) -> Path:
    resolved = data_root(root)
    for name in ("clips", "runs"):
        (resolved / name).mkdir(parents=True, exist_ok=True)
    return resolved


def run_id(now: datetime | None = None) -> str:
    """A filesystem-safe run identifier."""
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{secrets.token_hex(2)}"


def resolve_under(root: str | Path, value: str | Path, *, label: str = "path") -> Path:
    """Resolve ``value`` and require it to stay under ``root``."""
    root_path = Path(root).expanduser().resolve()
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = root_path / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root_path)
    except ValueError as exc:
        raise BenchmarkError(f"{label} escapes root: {value}") from exc
    return resolved


def safe_relative(value: str | Path, *, label: str = "path") -> Path:
    """Return a relative path, rejecting absolute paths and ``..`` escapes."""
    path = Path(value)
    if path.is_absolute():
        raise BenchmarkError(f"{label} must be relative: {value}")
    resolved = path.resolve()
    if resolved == Path(resolved.anchor):
        raise BenchmarkError(f"{label} must not be the filesystem root")
    if ".." in path.parts:
        raise BenchmarkError(f"{label} must not contain '..': {value}")
    return path


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: str | Path, default: Any = None) -> Any:
    resolved = Path(path)
    if not resolved.exists():
        return default
    try:
        return json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def atomic_write_json(path: str | Path, data: Any) -> Path:
    """Write JSON with an atomic replace so readers never see partial data."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{secrets.token_hex(4)}.tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
    return target


def atomic_write_text(path: str | Path, text: str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{secrets.token_hex(4)}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
    return target


def file_sha256_or_empty(path: str | Path | None) -> str:
    if not path:
        return ""
    resolved = Path(path)
    return sha256_file(resolved) if resolved.exists() else ""


__all__ = [
    "BenchmarkError",
    "DEFAULT_DATA_ROOT",
    "PROJECT_ROOT",
    "atomic_write_json",
    "atomic_write_text",
    "data_root",
    "ensure_data_root",
    "file_sha256_or_empty",
    "read_json",
    "resolve_under",
    "run_id",
    "safe_relative",
    "sha256_file",
    "sha256_json",
    "sha256_text",
]
