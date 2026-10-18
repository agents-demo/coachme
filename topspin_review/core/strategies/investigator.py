"""Model-as-orchestrator analysis strategy (experimental).

The deterministic strategy measures first. This one gives the model a toolbox and
lets it decide what to inspect. It is intentionally opt-in and independent of the
demo pipeline.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from topspin_review.core import config
from topspin_review.core.i18n import language_instruction
from topspin_review.core.params import Params
from topspin_review.core.progress import Progress, tick
from topspin_review.core.run_session import RunSession
from topspin_review.core.stages.investigate.context import InvestigationContext
from topspin_review.core.stages.investigate.prompts import INVESTIGATOR_SYSTEM, initial_query
from topspin_review.core.stages.investigate.tools import build_tools
from topspin_review.core.strategies.base import Strategy
from topspin_review.integrations import reporting
from topspin_review.integrations.agents import TextParams, build, run_agent
from topspin_review.integrations.agents.agent.rails import TokenBudgetRail, _count_tokens
from topspin_review.integrations.agents.telemetry.recorder import Recorder
from topspin_review.integrations.storage import json_store, runtime, store


class InvestigatorStrategy(Strategy):
    """Opt-in strategy where the model owns the investigation path."""

    name = "investigator"
    description = "Model-driven investigation with evidence tools."
    allow_demo_fallback = False

    def _prepare(self, params: Params) -> None:
        from topspin_review.core.bootstrap import setup

        progress = params.progress
        tick(progress, "preparing", 2)
        setup()
        if not Path(params.video_path).exists():
            raise FileNotFoundError(f"Video not found: {params.video_path}")

        params.profile = store.get_profile()
        params.profile["language"] = params.language
        params.measured = {}
        params.meta = {}
        params.frames = []
        params.timestamps = []
        params.artifact_paths = {}
        params.is_still = False

        params.investigation = InvestigationContext(
            video_path=params.video_path,
            profile=params.profile,
            language=params.language,
            progress=progress,
            data_dir=runtime.DATA_DIR,
            artifacts_dir=runtime.ARTIFACTS_DIR,
        )
        ctx: InvestigationContext = params.investigation
        recorder = Recorder(media_dir=str(ctx.media_dir))
        recorder.install()
        params.session = RunSession(
            video_path=params.video_path,
            recorder=recorder,
            vision_agent=None,
            media_dir=ctx.media_dir,
        )

    async def _run(self, params: Params, progress: Progress | None) -> tuple[Any, dict]:
        ctx: InvestigationContext = params.investigation
        tick(progress, "investigator: building tools", 10)
        tools = build_tools(ctx)
        rails = [name for name in config.rails() if name != "token_budget"]
        extra_rails = [TokenBudgetRail(config.investigator_max_tokens(), _count_tokens)]
        built = build(
            TextParams(
                system_prompt=INVESTIGATOR_SYSTEM,
                tools=tools,
                rails=rails,
                extra_rails=extra_rails,
                max_iterations=35,
                parallel_tool_calls=False,
                enable_task_loop=False,
                workspace=str(ctx.workspace_dir),
                media_dir=str(ctx.media_dir),
                recorder=params.session.recorder,
            )
        )
        previous = self._previous_summary(params).get("text", "")
        tick(progress, "investigator: reasoning", 25)
        result = await run_agent(
            built.agent,
            initial_query(
                profile=params.profile,
                history=previous,
                language_instruction=language_instruction(params.language),
            ),
        )
        tick(progress, "investigator: saving report", 92)
        return result, {"investigation": ctx.snapshot()}

    async def _finalize(
        self,
        params: Params,
        result: Any,
        extras: dict,
        progress: Progress | None,
    ) -> dict[str, Any]:
        ctx: InvestigationContext = params.investigation
        if not ctx.saved:
            self._save_partial(ctx, "no_report")

        report = dict(ctx.saved_report or {})
        evidence = ctx.ledger.records()
        investigation = dict(report.get("investigation") or {})
        investigation.update(
            {
                "schema_version": 1,
                "prompt_version": "inv-v1",
                "toolset_version": "tools-v1",
                "run_id": ctx.run_id,
                "coverage": ctx.coverage(),
                "untested": ctx.untested(),
                "budget": ctx.budget.snapshot(),
                "tool_calls": ctx.budget.tool_calls,
            }
        )
        report["mode"] = "investigator"
        report["evidence"] = [record.id for record in evidence]
        report["investigation"] = investigation
        report["source"] = params.video_path
        report["metrics"] = params.measured
        report["frames"] = 0
        report["frame_times"] = []
        report["fps"] = None
        investigation_path = Path(ctx.report_target.artifact_dir) / "investigation.json"
        json_store.write_json(
            investigation_path,
            {
                "run_id": ctx.run_id,
                "budget": ctx.budget.snapshot(),
                "coverage": ctx.coverage(),
                "untested": ctx.untested(),
                "evidence": [record.to_dict() for record in evidence],
            },
        )
        artifacts = dict(report.get("artifacts") or {})
        artifacts["investigation"] = str(investigation_path)
        report["artifacts"] = artifacts
        report["usage"] = params.session.usage_summary()
        timings: list = []
        if progress is not None:
            try:
                timings = progress.snapshot().get("timings") or []
            except Exception:
                timings = []
        report["timings"] = timings
        try:
            report["exports"] = reporting.write(report)
        except Exception:
            report["exports"] = {}

        store.add_report_at(ctx.report_target.working_report, report)
        store.add_report_at(ctx.report_target.final_report, report)
        tick(progress, "done", 100)
        return {
            "result": result,
            "report": report,
            "report_path": str(ctx.report_target.final_report),
            "observations": "",
            "frames": 0,
            "meta": {},
            "timings": timings,
        }

    def _save_partial(self, ctx: InvestigationContext, reason: str) -> None:
        records = ctx.ledger.records()
        if not records:
            raise RuntimeError(f"investigation failed before evidence: {reason}")
        report = {
            "date": date.today().isoformat(),
            "sport": ctx.profile.get("sport", "table tennis"),
            "summary": f"Analysis stopped early: {reason}. Only the inspected evidence is reported.",
            "strengths": [],
            "issues": [],
            "drills": [],
            "focus": "",
            "progress": "",
            "limitations": [
                f"Analysis stopped early: {reason}.",
                "Not assessed: " + ", ".join(ctx.untested()) + ".",
            ],
            "mode": "investigator",
            "evidence": [record.id for record in records],
            "investigation": {
                "coverage": ctx.coverage(),
                "untested": ctx.untested(),
                "stop_reason": reason,
            },
        }
        ctx.allow_partial = True
        saved = json.loads(ctx.save_report(json.dumps(report)))
        if not saved.get("ok"):
            raise RuntimeError(f"could not save partial report: {saved.get('error')}")


__all__ = ["InvestigatorStrategy"]
