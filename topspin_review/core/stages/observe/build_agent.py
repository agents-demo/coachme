"""Vision-agent policy: the prompt for the video-understanding agent.

Like the report agent (``coaching/agent.py``), this is a thin business policy over
the backend agent builder. It returns the build result, whose recorder is the run
recorder (the vision agent is the first agent built in a run).
"""

from __future__ import annotations

from typing import Any

from topspin_review.core.bootstrap import setup
from topspin_review.core.stages.observe import prompts
from topspin_review.integrations.agents import VisionParams, build
from topspin_review.integrations.storage import runtime


def build_agent(
    *,
    media_dir: str,
    workspace: str | None = None,
    max_iterations: int = 4,
    system_prompt: str | None = None,
    recorder: Any = None,
) -> Any:
    """Build the vision DeepAgent (reads rendered images via ``read_file``).

    Pass ``recorder`` to share the run's telemetry trace so that vision token
    costs appear in the same usage summary as the orchestrator agent.
    """
    setup()
    return build(
        VisionParams(
            system_prompt=system_prompt or prompts.VISION_AGENT_SYSTEM,
            workspace=workspace or str(runtime.ARTIFACTS_DIR),
            media_dir=media_dir,
            max_iterations=max_iterations,
            recorder=recorder,
        )
    )
