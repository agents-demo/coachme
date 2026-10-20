$ErrorActionPreference = "Stop"
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"
if (-not (Test-Path "runtime\data\sample.mp4")) { & $PY tests\integration\make_sample.py }
& $PY -m coachme.surfaces.cli analyze runtime/data/sample.mp4
