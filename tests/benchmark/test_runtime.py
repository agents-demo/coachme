from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_coachme_data_dir_overrides_runtime_data(tmp_path: Path) -> None:
    target = tmp_path / "isolated"
    env = os.environ.copy()
    env["COACHME_DATA_DIR"] = str(target)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from coachme.integrations.storage import runtime; print(runtime.DATA_DIR)",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert Path(result.stdout.strip()) == target.resolve()
