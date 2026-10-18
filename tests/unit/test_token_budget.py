"""Verify that token usage from the rail is reflected in Budget.tokens."""
from __future__ import annotations

from topspin_review.integrations.agents.agent.rails import TokenBudgetRail


class _FakeCtx:
    """Minimal stand-in for the openjiuwen agent context."""

    def __init__(self) -> None:
        self._force_finish_called = False

    def request_force_finish(self, payload) -> None:
        self._force_finish_called = True


class _FakeResponse:
    pass


def _make_rail(budget: int, tokens_per_call: int) -> TokenBudgetRail:
    return TokenBudgetRail(budget, lambda _response: tokens_per_call)


def test_rail_accumulates_used() -> None:
    import asyncio

    rail = _make_rail(budget=1000, tokens_per_call=100)
    ctx = _FakeCtx()

    async def _run():
        # Simulate three model calls
        for _ in range(3):
            await rail.after_model_call(ctx, response=_FakeResponse())

    asyncio.run(_run())
    assert rail.used == 300
    assert not ctx._force_finish_called


def test_rail_requests_force_finish_when_budget_exceeded() -> None:
    import asyncio

    rail = _make_rail(budget=150, tokens_per_call=100)
    ctx = _FakeCtx()

    async def _run():
        # First call: 100 tokens (under budget)
        await rail.after_model_call(ctx, response=_FakeResponse())
        # Second call: 200 total (over budget)
        await rail.after_model_call(ctx, response=_FakeResponse())

    asyncio.run(_run())
    assert rail.used == 200
    assert ctx._force_finish_called


def test_budget_tokens_can_be_set_from_rail() -> None:
    """Simulate how the investigator strategy syncs the rail back to Budget."""
    from topspin_review.core.stages.investigate.context import Budget

    budget = Budget(max_tokens=5000)
    assert budget.tokens == 0

    rail = _make_rail(budget=5000, tokens_per_call=250)
    import asyncio

    ctx = _FakeCtx()

    async def _run():
        for _ in range(4):
            await rail.after_model_call(ctx, response=_FakeResponse())

    asyncio.run(_run())
    budget.tokens = rail.used  # this is the line in investigator.py
    assert budget.tokens == 1000
    snapshot = budget.snapshot()
    assert snapshot["tokens"] == 1000
    assert snapshot["max_tokens"] == 5000
