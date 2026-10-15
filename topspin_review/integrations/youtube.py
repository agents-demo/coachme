"""Download a YouTube (or any yt-dlp-supported) video to a local file for analysis.

`yt-dlp` is an optional dependency: everything else in the project works without it,
and this only reports a friendly error when a link is analysed and it is missing.
"""

from __future__ import annotations

import re
from pathlib import Path

_URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)


class YoutubeUnavailable(RuntimeError):
    """Raised when yt-dlp is not installed."""


def is_url(value: str) -> bool:
    """Whether `value` looks like an http(s) URL."""
    return bool(_URL_RE.match((value or "").strip()))


def _ffmpeg_location() -> str | None:
    """The ``ffmpeg`` binary to hand yt-dlp, using the one bundled by imageio-ffmpeg.

    yt-dlp needs ffmpeg to merge separate video/audio streams; without a system ffmpeg
    we fall back to the copy that ships with ``imageio-ffmpeg`` (already a dependency
    for video reading). Returns ``None`` when neither is available, letting yt-dlp try
    its own lookup.
    """
    import shutil  # noqa: PLC0415

    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg  # noqa: PLC0415  (optional dependency, imported on use)

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # noqa: BLE001 - any failure means "let yt-dlp decide"
        return None


def download(url: str, dest_dir: Path, max_height: int = 720) -> Path:
    """Download the best mp4 up to `max_height` pixels tall and return the saved path.

    Raises ``ValueError`` for a non-URL, ``YoutubeUnavailable`` when yt-dlp is absent,
    and lets yt-dlp's own errors propagate for anything else.
    """
    url = (url or "").strip()
    if not is_url(url):
        raise ValueError("That doesn't look like a video link.")

    try:
        import yt_dlp  # noqa: PLC0415  (optional dependency, imported on use)
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise YoutubeUnavailable(
            "yt-dlp isn't installed. Run `pip install yt-dlp` to analyze YouTube links."
        ) from exc

    dest_dir.mkdir(parents=True, exist_ok=True)
    opts = {
        # Prefer an mp4 (video+audio merged) no taller than max_height; fall back gracefully.
        "format": (
            f"bv*[height<={max_height}][ext=mp4]+ba[ext=m4a]/"
            f"b[height<={max_height}][ext=mp4]/b[height<={max_height}]/b"
        ),
        "outtmpl": str(dest_dir / "%(title).80s-%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
    }
    ffmpeg = _ffmpeg_location()
    if ffmpeg:
        opts["ffmpeg_location"] = ffmpeg
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = Path(ydl.prepare_filename(info))

    # A merge can change the extension to .mp4; find whatever actually landed.
    if not path.exists():
        merged = path.with_suffix(".mp4")
        if merged.exists():
            path = merged
    if not path.exists():
        video_id = str(info.get("id") or "")
        matches = sorted(dest_dir.glob(f"*{video_id}*")) if video_id else []
        if matches:
            path = matches[0]
    return path
