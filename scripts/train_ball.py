"""Train a YOLOv8-nano ball detector and export it to ONNX for the app.

Requires the training extra:  pip install ultralytics

The app loads ``runtime/data/models/ball.onnx`` automatically (override with
``BALL_MODEL_PATH``). Until that file exists it uses the heuristic tracker, so this
step is optional and additive.

Dataset: a YOLO-format set with one class, ``ball`` (class 0). A permissively
licensed table-tennis-ball dataset works; the app only needs the exported ONNX.

Usage:
    python scripts/train_ball.py --data path/to/data.yaml --epochs 80 --imgsz 640
    python scripts/train_ball.py --export-only runs/detect/ball/weights/best.pt
"""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_OUT = Path("runtime/data/models/ball.onnx")


def main() -> int:
    parser = argparse.ArgumentParser(description="Train + export the ball detector to ONNX.")
    parser.add_argument("--data", help="Dataset YAML (single class 'ball').")
    parser.add_argument("--model", default="yolov8n.pt", help="Base weights to fine-tune from.")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Where to write ball.onnx.")
    parser.add_argument("--export-only", help="Skip training; export this .pt checkpoint instead.")
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics is not installed. Run: pip install ultralytics")
        return 1

    if args.export_only:
        weights = args.export_only
    else:
        if not args.data:
            parser.error("--data is required unless --export-only is given")
        model = YOLO(args.model)
        results = model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz)
        weights = str(Path(results.save_dir) / "weights" / "best.pt")

    print(f"Exporting {weights} -> ONNX (opset 12)")
    YOLO(weights).export(format="onnx", imgsz=args.imgsz, opset=12, simplify=True)

    produced = Path(weights).with_suffix(".onnx")
    if not produced.exists():
        print(f"Expected ONNX at {produced} but it is missing.")
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(produced.read_bytes())
    print(f"Wrote {out}. The app will use it on the next analysis run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
