"""The pipeline stages, in run order: ``measure`` → ``observe`` → ``coach``.

``STAGES`` is the single source of truth for the stage set; the architecture test
checks it matches the packages in this folder.
"""

from topspin_review.core.stages import coach, measure, observe

STAGES = ("measure", "observe", "coach")

__all__ = ["STAGES", "coach", "measure", "observe"]
