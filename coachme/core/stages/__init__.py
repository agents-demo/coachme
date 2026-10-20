"""The pipeline stages, in run order: ``measure`` → ``observe`` → ``coach``.

``STAGES`` is the single source of truth for the stage set; the architecture test
checks it matches the packages in this folder.
"""

from coachme.core.stages import coach, investigate, measure, observe

STAGES = ("measure", "observe", "coach", "investigate")

__all__ = ["STAGES", "coach", "investigate", "measure", "observe"]
