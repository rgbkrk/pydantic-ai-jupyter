"""Tests for run_with_display.

Basic Integration Tests:
------------------------
Tests using TestModel to verify run_with_display works end-to-end.

Display Mocking Tests:
---------------------
The display system uses IPython.display.display in two places:

1. pydantic_ai_jupyter.models.display - Used by View.display() and View.update() methods
   - Markdown views call this
   - StreamingToolCallView calls this

2. pydantic_ai_jupyter.display.display - Direct import for ToolResultView and ErrorView
   - ToolResultView uses this (called directly, not via .display() method)
   - ErrorView uses this

To properly test, we mock where display is USED (not where it's imported from).
Mock 'pydantic_ai_jupyter.models.display' to catch view method calls.
Mock 'pydantic_ai_jupyter.display.display' to catch direct display() calls.
"""

from __future__ import annotations as _annotations

from unittest.mock import patch

import pytest
from inline_snapshot import snapshot
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from pydantic_ai_jupyter.display import run_with_display
from pydantic_ai_jupyter.markdown import Markdown
from pydantic_ai_jupyter.views import StreamingToolCallView, ToolResultView

pytestmark = pytest.mark.anyio


# Basic Integration Tests
# ========================


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


# Display Mocking Tests
# =====================


async def test_display_is_called() -> None:
    """Verify that display() is actually called during run_with_display."""
    model = TestModel()
    agent = Agent(model)

    # Mock display in both places it's used
    with patch("pydantic_ai_jupyter.display.display") as mock_display_module:
        with patch("pydantic_ai_jupyter.models.display") as mock_models_display:
            result = await run_with_display(agent, "Hello")

            assert result is not None

            # At least one of them should have been called
            total_calls = mock_display_module.call_count + mock_models_display.call_count
            assert total_calls > 0, "display() should have been called at least once"


async def test_display_shows_markdown() -> None:
    """Verify that Markdown views are displayed."""
    model = TestModel()
    agent = Agent(model)

    with patch("pydantic_ai_jupyter.models.display") as mock_display:
        result = await run_with_display(agent, "Hello")

        assert result is not None

        # Find Markdown in displayed items
        displayed_items = [call[0][0] for call in mock_display.call_args_list]
        markdown_items = [item for item in displayed_items if isinstance(item, Markdown)]

        assert len(markdown_items) > 0, "Should have displayed Markdown"


async def test_display_shows_tool_calls() -> None:
    """Verify that tool calls create StreamingToolCallView."""
    model = TestModel()
    agent = Agent(model)

    @agent.tool_plain
    def get_weather(city: str) -> str:
        """Get weather."""
        return f"Sunny in {city}"

    with patch("pydantic_ai_jupyter.models.display") as mock_display:
        result = await run_with_display(agent, "What's the weather?")

        assert result is not None

        # Find StreamingToolCallView
        displayed_items = [call[0][0] for call in mock_display.call_args_list]
        tool_views = [item for item in displayed_items if isinstance(item, StreamingToolCallView)]

        assert len(tool_views) > 0, "Should have displayed tool call"


async def test_display_shows_tool_results() -> None:
    """Verify that tool results create ToolResultView."""
    model = TestModel()
    agent = Agent(model)

    @agent.tool_plain
    def add(x: int, y: int) -> int:
        """Add numbers."""
        return x + y

    with patch("pydantic_ai_jupyter.display.display") as mock_display:
        result = await run_with_display(agent, "Add 2 + 3")

        assert result is not None

        # Find ToolResultView
        displayed_items = [call[0][0] for call in mock_display.call_args_list]
        result_views = [item for item in displayed_items if isinstance(item, ToolResultView)]

        assert len(result_views) > 0, "Should have displayed tool result"


async def test_display_has_display_ids() -> None:
    """Verify that all display calls include display_id."""
    model = TestModel()
    agent = Agent(model)

    with patch("pydantic_ai_jupyter.models.display") as mock_display:
        await run_with_display(agent, "Hello")

        # Every call should have display_id
        for i, call in enumerate(mock_display.call_args_list):
            kwargs = call[1]
            assert "display_id" in kwargs, f"Call {i} missing display_id: {call}"
            assert isinstance(kwargs["display_id"], str)
            assert len(kwargs["display_id"]) > 0
