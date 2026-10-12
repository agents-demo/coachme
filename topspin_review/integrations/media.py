"""Outbound media artifacts: cut short highlight clips around flagged moments.

Uses the ``ffmpeg`` bundled by ``imageio-ffmpeg`` (no system ffmpeg needed). Best
effort: a failed cut is dropped, never raised.
"""

from __future__ import annotations

from pathlib import Path

from topspin_review.integrations.storage import runtime


def _ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def make_clip(video: str, start: float, end: float, out_path: Path) -> bool:
    import subprocess

    start = max(0.0, float(start))
    end = max(start + 0.5, float(end))
    try:
        exe = _ffmpeg()
        # Fast path: stream copy (works when cuts land on keyframes).
        subprocess.run(
            [exe, "-y", "-ss", f"{start}", "-to", f"{end}", "-i", str(video), "-c", "copy", str(out_path)],
            capture_output=True,
        )
        if out_path.exists() and out_path.stat().st_size > 0:
            return True
        # Fallback: re-encode (accurate but slower).
        subprocess.run(
            [
                exe, "-y", "-ss", f"{start}", "-i", str(video), "-t", f"{end - start}",
                "-c:v", "libx264", "-preset", "veryfast", "-an", str(out_path),
            ],
            capture_output=True,
        )
        return out_path.exists() and out_path.stat().st_size > 0
    except Exception:
        return False


def make_clips(
    video: str, times: list[float], stem: str, before: float = 1.0, after: float = 2.0, limit: int = 3
) -> dict:
    """Create up to ``limit`` short clips centred on ``times``."""
    clips: dict[str, str] = {}
    if not times:
        return clips
    out_dir = runtime.ARTIFACTS_DIR / f"{stem}_clips"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return clips
    for i, t in enumerate(sorted(set(times))[:limit]):
        out = out_dir / f"moment_{i}_{round(float(t), 1)}s.mp4"
        if make_clip(video, float(t) - before, float(t) + after, out):
            clips[str(round(float(t), 1))] = str(out)
    return clips


def make_reel(clip_paths: list[str], out_path: Path, width: int = 1280, height: int = 720) -> bool:
    """Concatenate clips into one highlight reel, re-encoded to a uniform size."""
    import os
    import subprocess
    import tempfile

    paths = [p for p in clip_paths if p and Path(p).exists()]
    if not paths:
        return False
    list_file = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
            list_file = fh.name
            for p in paths:
                fh.write(f"file '{Path(p).as_posix()}'\n")
        subprocess.run(
            [
                _ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", list_file,
                "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1",
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-an", str(out_path),
            ],
            capture_output=True,
        )
        return out_path.exists() and out_path.stat().st_size > 0
    except Exception:
        return False
    finally:
        if list_file:
            try:
                os.unlink(list_file)
            except Exception:
                pass


def export_clip(
    video: str, start: float, end: float, out_path: Path, fmt: str = "mp4", vertical: bool = False, width: int = 720
) -> bool:
    """Trim ``[start, end]`` and export as mp4 or gif; optional 9:16 vertical crop."""
    import subprocess

    start = max(0.0, float(start))
    end = max(start + 0.1, float(end))
    try:
        exe = _ffmpeg()
        if fmt == "gif":
            vf = []
            if vertical:
                vf.append("crop=ih*9/16:ih:(iw-ih*9/16)/2:0")
            vf += ["fps=12", f"scale={width}:-1:flags=lanczos"]
            graph = ",".join(vf) + ",split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
            subprocess.run(
                [exe, "-y", "-ss", str(start), "-to", str(end), "-i", str(video), "-vf", graph, str(out_path)],
                capture_output=True,
            )
        else:
            vf = []
            if vertical:
                vf.append("crop=ih*9/16:ih:(iw-ih*9/16)/2:0")
                vf.append("scale=720:1280")
            vf.append("setsar=1")
            subprocess.run(
                [
                    exe, "-y", "-ss", str(start), "-to", str(end), "-i", str(video),
                    "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", "-an", str(out_path),
                ],
                capture_output=True,
            )
        return out_path.exists() and out_path.stat().st_size > 0
    except Exception:
        return False
