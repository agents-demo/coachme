"""CoachMe benchmark: manifests, labels, runs, scoring and blind ratings."""

from coachme.benchmark.core.data.paths import BenchmarkError
from coachme.benchmark.core.evaluation.scorer import score_run

__all__ = ["BenchmarkError", "score_run"]
