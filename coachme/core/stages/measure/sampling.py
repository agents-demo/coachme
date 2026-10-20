"""Adaptive, motion-weighted frame sampling.

Even sampling wastes frames on dead time and skips short bursts of action. This
probes the clip cheaply, then spends the frame budget where the image is actually
changing (weighted by motion, with a baseline everywhere), so footwork and swing
moments are more likely to be captured. Frame caching lives in
:mod:`coachme.integrations.storage.cache`.
"""

from __future__ import annotations

from pathlib import Path

import imageio
import numpy as np
from PIL import Image

from coachme.core import config
from coachme.integrations.storage import cache

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS


def load_image(path: str | Path) -> tuple[dict, list[Image.Image], list[float]]:
    """Return ``(meta, [image], [0.0])`` for a single still picture."""
    img = Image.open(str(path)).convert("RGB")
    meta = {"fps": 0, "duration": 0, "size": img.size}
    return meta, [img], [0.0]


def _scaled_reader(path: str, width: int = 160, height: int = 90):
    """Reader that decodes frames downscaled (cheap probing for long clips)."""
    try:
        return imageio.get_reader(path, format="ffmpeg", output_params=["-vf", f"scale={width}:{height}"])
    except Exception:
        return imageio.get_reader(path, format="ffmpeg")


def _read_rgb(reader, idx: int) -> Image.Image | None:
    """Decode frame ``idx`` as RGB, or ``None`` when the reader can't reach it.

    The estimated frame count (``duration * fps``) can overshoot what the decoder can
    actually seek to, so the last few indices may raise ``IndexError``/``StopIteration``.
    """
    try:
        return Image.fromarray(reader.get_data(idx)).convert("RGB")
    except Exception:
        return None


def _read_gray(reader, idx: int, size: tuple[int, int] = (160, 90)) -> np.ndarray | None:
    """Decode frame ``idx`` as a small grayscale array, or ``None`` when unavailable."""
    try:
        img = Image.fromarray(reader.get_data(idx)).convert("L")
        if img.size != size:
            img = img.resize(size)
        return np.asarray(img, dtype=np.float32)
    except Exception:
        return None


def _probe_indices(total: int, budget: int) -> list[int]:
    if total <= budget:
        return list(range(total))
    return sorted({int(round(i * (total - 1) / (budget - 1))) for i in range(budget)})


def _allocate(count: int, energies: list[float]) -> list[int]:
    """Split ``count`` samples across intervals, weighted by motion energy."""
    k = len(energies)
    if k == 0 or count <= 0:
        return [0] * k
    peak = max(energies) or 1.0
    weights = [0.3 + (e / peak) for e in energies]  # 0.3 baseline so no interval starves
    total = sum(weights)
    raw = [count * w / total for w in weights]
    counts = [int(r) for r in raw]
    remainder = count - sum(counts)
    order = sorted(range(k), key=lambda i: raw[i] - counts[i], reverse=True)
    for i in range(remainder):
        counts[order[i % k]] += 1
    return counts


def _select_indices(probe: list[int], energies: list[float], max_frames: int, total: int) -> list[int]:
    if total <= max_frames:
        return list(range(total))

    # one motion value per interval between consecutive probes
    interval_energy = [max(0.0, e) for e in energies]
    counts = _allocate(max_frames, interval_energy)

    chosen: set[int] = set()
    for i, c in enumerate(counts):
        start, end = probe[i], probe[i + 1]
        if c <= 0 or end <= start:
            continue
        for j in range(c):
            idx = int(round(start + (j + 1) * (end - start) / (c + 1)))
            chosen.add(min(idx, total - 1))
    chosen.add(0)
    chosen.add(total - 1)
    return sorted(chosen)


def sample_window(video_path: str | Path, start: float, end: float, count: int = 4) -> tuple[list[Image.Image], list[float]]:
    """Sample ``count`` frames evenly inside ``[start, end]`` seconds."""
    path = Path(video_path)
    if not path.exists() or count <= 0:
        return [], []

    reader = imageio.get_reader(str(path), format="ffmpeg")
    try:
        try:
            meta = dict(reader.get_meta_data())
        except Exception:
            meta = {}
        fps = float(meta.get("fps") or 30)
        duration = meta.get("duration")
        if duration:
            total = max(1, int(float(duration) * fps))
        else:
            try:
                total = int(reader.count_frames())
            except Exception:
                total = 0

        lo = max(0, int(round(float(start) * fps)))
        hi = int(round(float(end) * fps))
        if hi <= lo:
            hi = lo + count
        if total:
            lo = min(lo, total - 1)
            hi = min(max(hi, lo + 1), total)

        if count == 1:
            indices = [lo]
        else:
            indices = sorted({int(round(lo + i * (hi - lo) / (count - 1))) for i in range(count)})

        frames: list[Image.Image] = []
        times: list[float] = []
        for idx in indices:
            try:
                frames.append(Image.fromarray(reader.get_data(idx)).convert("RGB"))
                times.append(idx / fps)
            except Exception:
                continue
        return frames, times
    finally:
        reader.close()


def sample_even(video_path: str | Path, count: int) -> tuple[list[Image.Image], list[float]]:
    """Up to ``count`` frames spread **evenly across the whole clip** (not a window)."""
    path = Path(video_path)
    if not path.exists() or count <= 0:
        return [], []
    reader = imageio.get_reader(str(path), format="ffmpeg")
    try:
        try:
            meta = dict(reader.get_meta_data())
        except Exception:
            meta = {}
        fps = float(meta.get("fps") or 30)
        duration = meta.get("duration")
        if duration:
            total = max(1, int(float(duration) * fps))
        else:
            try:
                total = int(reader.count_frames())
            except Exception:
                total = 0
        if total <= 0:
            return [], []
        if total <= count:
            indices = list(range(total))
        else:
            indices = sorted({int(round(i * (total - 1) / (count - 1))) for i in range(count)})
        frames: list[Image.Image] = []
        times: list[float] = []
        for idx in indices:
            try:
                frames.append(Image.fromarray(reader.get_data(idx)).convert("RGB"))
                times.append(idx / fps)
            except Exception:
                continue
        return frames, times
    finally:
        reader.close()


def sample_burst(
    video_path: str | Path, start: float, end: float, target_fps: float = 8.0, cap: int = 20
) -> tuple[list[Image.Image], list[float]]:
    """Sample ``[start, end]`` at ~``target_fps`` (denser than sample_window)."""
    path = Path(video_path)
    if not path.exists():
        return [], []

    reader = imageio.get_reader(str(path), format="ffmpeg")
    try:
        try:
            meta = dict(reader.get_meta_data())
        except Exception:
            meta = {}
        fps = float(meta.get("fps") or 30)
        total = int(reader.count_frames()) if not meta.get("duration") else 0

        lo = max(0, int(round(float(start) * fps)))
        hi = int(round(float(end) * fps))
        if hi <= lo:
            hi = lo + 1
        if total:
            lo = min(lo, total - 1)
            hi = min(max(hi, lo + 1), total)

        step = max(1, int(round(fps / max(float(target_fps), 0.5))))
        count = min(cap, max(0, (hi - lo) // step + 1))
        indices = [lo + k * step for k in range(count)]

        frames: list[Image.Image] = []
        times: list[float] = []
        for idx in indices:
            try:
                frames.append(Image.fromarray(reader.get_data(idx)).convert("RGB"))
                times.append(idx / fps)
            except Exception:
                continue
        return frames, times
    finally:
        reader.close()


def sample_frames(
    video_path: str | Path, max_frames: int = 12, use_cache: bool = True
) -> tuple[dict, list[Image.Image], list[float]]:
    """Return ``(metadata, frames, timestamps)`` sampled where motion happens."""
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"video not found: {path}")

    if use_cache:
        cached = cache.load(path, max_frames, config.max_seconds())
        if cached is not None:
            return cached

    reader = imageio.get_reader(str(path), format="ffmpeg")
    try:
        try:
            meta = dict(reader.get_meta_data())
        except Exception:
            meta = {}

        fps = float(meta.get("fps") or 30)
        duration = meta.get("duration")
        if duration:
            total = max(1, int(float(duration) * fps))
        else:
            try:
                total = int(reader.count_frames())
            except Exception:
                total = 0

        cap_seconds = config.max_seconds()
        if cap_seconds > 0:
            total = min(total, max(1, int(cap_seconds * fps)))

        if total and total > 0:
            probes = _probe_indices(total, min(config.probe_budget(), max(2, total)))
            probe_reader = _scaled_reader(str(path), 160, 90)
            try:
                # Keep only the probes we could actually decode, so the motion series
                # stays aligned with the indices (an unreachable tail can't break it).
                valid_probes: list[int] = []
                probe_gray: list[np.ndarray] = []
                for idx in probes:
                    gray = _read_gray(probe_reader, idx)
                    if gray is None:
                        gray = _read_gray(reader, idx)
                    if gray is not None:
                        valid_probes.append(idx)
                        probe_gray.append(gray)
            finally:
                try:
                    probe_reader.close()
                except Exception:
                    pass
            if len(valid_probes) >= 2:
                energies = [
                    float(np.abs(probe_gray[i] - probe_gray[i - 1]).mean()) for i in range(1, len(probe_gray))
                ]
                indices = _select_indices(valid_probes, energies, max_frames, total)
            else:
                indices = _probe_indices(total, min(max_frames, max(2, total)))
            frames = []
            timestamps = []
            for idx in indices:
                img = _read_rgb(reader, idx)
                if img is not None:
                    frames.append(img)
                    timestamps.append(idx / fps)
            if not frames:
                # Seeking failed for every chosen index — read sequentially instead.
                fallback = imageio.get_reader(str(path), format="ffmpeg")
                try:
                    step = max(1, total // max_frames) if total else 30
                    for i, arr in enumerate(fallback):
                        if i % step == 0:
                            frames.append(Image.fromarray(arr).convert("RGB"))
                            timestamps.append(i / fps)
                        if len(frames) >= max_frames:
                            break
                except Exception:
                    pass
                finally:
                    fallback.close()
        else:
            frames = []
            timestamps = []
            for i, arr in enumerate(reader):
                if i % 30 == 0:
                    frames.append(Image.fromarray(arr).convert("RGB"))
                    timestamps.append(i / fps)
                if len(frames) >= max_frames:
                    break
    finally:
        reader.close()

    if use_cache and frames:
        try:
            cache.save(path, max_frames, config.max_seconds(), meta, frames, timestamps)
        except Exception:
            pass
    return meta, frames, timestamps
