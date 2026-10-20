"""Provision the table-tennis ball detector: download a permissive YOLO model and export to ONNX.

Defaults to the MIT-licensed ``ashercn97/pingpongball-yolo`` model, exports it with the
Ultralytics YOLOv5 exporter, and copies the result to ``runtime/data/models/ball.onnx``
(the path the app auto-loads). Without this file the app uses the heuristic tracker.

This must run in a training environment (torch + the YOLOv5 exporter):

    pip install torch torchvision onnx onnxruntime dill ultralytics

Usage:
    python scripts/fetch_ball_model.py
    python scripts/fetch_ball_model.py --yolov5-dir C:\\path\\to\\yolov5
    python scripts/fetch_ball_model.py --weights path\\to\\your\\best.pt   # bring your own

License note: the default model is MIT. If you swap in another checkpoint, check its terms.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

DEFAULT_URL = "https://huggingface.co/ashercn97/pingpongball-yolo/resolve/main/best.pt"
DEFAULT_OUT = Path("runtime/data/models/ball.onnx")


def main() -> int:
    parser = argparse.ArgumentParser(description="Download + export the ball detector to ONNX.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Checkpoint URL (ignored if --weights given).")
    parser.add_argument("--weights", help="Local .pt checkpoint to export instead of downloading.")
    parser.add_argument("--yolov5-dir", help="Existing ultralytics/yolov5 checkout (else cloned to a temp dir).")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    workdir = Path(tempfile.gettempdir()) / "coachme_ball"
    workdir.mkdir(parents=True, exist_ok=True)

    weights = Path(args.weights) if args.weights else workdir / "best.pt"
    if not args.weights and not weights.exists():
        print(f"Downloading {args.url} ...")
        try:
            urllib.request.urlretrieve(args.url, weights)
        except Exception as exc:
            print(f"Download failed: {exc}")
            return 1

    yolov5 = Path(args.yolov5_dir) if args.yolov5_dir else workdir / "yolov5"
    if not yolov5.exists():
        print(f"Cloning ultralytics/yolov5 into {yolov5} ...")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/ultralytics/yolov5", str(yolov5)],
            check=False,
        )
        if result.returncode != 0:
            print("git clone failed. Pass --yolov5-dir pointing at an existing checkout.")
            return 1

    print("Exporting to ONNX (needs torch + the yolov5 requirements installed)...")
    cmd = [sys.executable, "export.py", "--weights", str(weights), "--include", "onnx", "--imgsz", str(args.imgsz), "--opset", "12"]
    result = subprocess.run(cmd, cwd=str(yolov5), check=False)
    if result.returncode != 0:
        print("Export failed. Install the exporter deps: pip install torch torchvision onnx onnxruntime dill -r yolov5/requirements.txt")
        return 1

    produced = weights.with_suffix(".onnx")
    if not produced.exists():
        print(f"Expected {produced} but it is missing.")
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(produced, out)
    print(f"Wrote {out} ({out.stat().st_size} bytes). The app will use it on the next analysis run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
