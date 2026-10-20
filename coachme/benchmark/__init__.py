"""CoachMe benchmark: manifests, labels, runs, scoring and blind ratings."""

from coachme.benchmark.paths import BenchmarkError
from coachme.benchmark.scorer import score_run

__all__ = ["BenchmarkError", "score_run"]
