"""The pipeline — stages of analysis, run by two interchangeable strategies.

- :mod:`~coachme.core.stages.measure` — stage 1: clip → frames + measurements.
- :mod:`~coachme.core.stages.observe` — stage 2: frames → observations.
- :mod:`~coachme.core.stages.coach` — stage 3: observations → coaching report.
- :mod:`~coachme.core.strategies` — deterministic / agentic modes over the stages.

Import the orchestrator from this package, never a concrete strategy module:

    from coachme import core

    strategy = core.resolve(agentic=True)
    result = await strategy.analyze(core.Params(video_path, progress=...))

Side-effect free.
"""

from coachme.core.params import Params
from coachme.core.stages import STAGES
from coachme.core.strategies import (
    AGENTIC,
    DETERMINISTIC,
    STRATEGIES,
    Strategy,
    default_name,
    get_strategy,
    resolve,
)

__all__ = [
    "AGENTIC",
    "DETERMINISTIC",
    "STAGES",
    "STRATEGIES",
    "Params",
    "Strategy",
    "default_name",
    "get_strategy",
    "resolve",
]
