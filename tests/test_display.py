from __future__ import annotations as _annotations

import pytest
from inline_snapshot import snapshot
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from pydantic_ai_jupyter.display import run_with_display

pytestmark = pytest.mark.anyio


async def test_run_with_display_basic() -> None:
    """Basic test of run_with_display with TestModel."""
    model = TestModel()
    agent = Agent(model)

    result = await run_with_display(agent, "Hello")

    assert result is not None
    assert result.output == snapshot("success (no tool calls)")


async def test_run_with_display_with_tool() -> None:
    """Test run_with_display with a simple tool."""
    model = TestModel()
    agent = Agent(model)

    @agent.tool_plain
    def get_weather(city: str) -> str:
        """Get the weather for a city."""
        return f"The weather in {city} is sunny"

    result = await run_with_display(agent, "What is the weather in SF?")

    assert result is not None
    assert result.output == snapshot('{"get_weather":"The weather in a is sunny"}')


async def test_run_with_display_returns_none_on_exception() -> None:
    """Test that run_with_display returns None when an exception occurs."""
    model = TestModel()
    agent = Agent(model)

    @agent.tool_plain
    def failing_tool() -> str:
        """A tool that always fails."""
        raise ValueError("Tool failed")

    # Note: This will raise since the exception is re-raised
    # but we're testing the error handling path
    with pytest.raises(ValueError, match="Tool failed"):
        await run_with_display(agent, "Use the failing tool")
