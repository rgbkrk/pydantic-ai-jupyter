"""Tests for DisplayAgent wrapper class."""

from __future__ import annotations as _annotations

from unittest.mock import patch

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from pydantic_ai_jupyter.display_agent import DisplayAgent
from pydantic_ai_jupyter.tool_views import DefaultToolView, ToolView
from pydantic_ai_jupyter.views import CustomStreamingToolCallView, CustomToolResultView

pytestmark = pytest.mark.anyio


async def test_display_agent_basic() -> None:
    """DisplayAgent should run an agent and return results."""
    model = TestModel()
    agent = Agent(model)

    display_agent = DisplayAgent(agent=agent)
    result = await display_agent.run("Hello")

    assert result is not None
    assert result.output == "success (no tool calls)"


async def test_display_agent_with_tool() -> None:
    """DisplayAgent should handle tool calls."""
    model = TestModel()
    agent = Agent(model)

    @agent.tool_plain
    def greet(name: str) -> str:
        """Greet someone."""
        return f"Hello, {name}!"

    display_agent = DisplayAgent(agent=agent)
    result = await display_agent.run("Greet Alice")

    assert result is not None


async def test_display_agent_custom_tool_view() -> None:
    """DisplayAgent should use custom tool views."""

    class CustomWeatherView(ToolView):
        def render_result(self, tool_name: str, content, tool_call_id=None, is_retry=False, max_length=500) -> str:
            return f"<weather-card>{content}</weather-card>"

    model = TestModel()
    agent = Agent(model)

    @agent.tool_plain
    def get_weather(city: str) -> str:
        """Get weather."""
        return f"Sunny in {city}"

    display_agent = DisplayAgent(agent=agent, tool_views={"get_weather": CustomWeatherView()})

    with patch("pydantic_ai_jupyter.display.display") as mock_display:
        result = await display_agent.run("What's the weather?")

        assert result is not None

        # Find CustomToolResultView in displayed items
        displayed_items = [call[0][0] for call in mock_display.call_args_list]
        result_views = [item for item in displayed_items if isinstance(item, CustomToolResultView)]

        assert len(result_views) > 0, "Should have displayed CustomToolResultView"

        # Verify custom rendering was used
        html = result_views[0].render()
        assert "<weather-card>" in html


async def test_display_agent_decorator_registration() -> None:
    """DisplayAgent should support @tool_view decorator."""
    model = TestModel()
    agent = Agent(model)

    @agent.tool_plain
    def search(query: str) -> str:
        """Search for something."""
        return f"Results for: {query}"

    display_agent = DisplayAgent(agent=agent)

    @display_agent.tool_view("search")
    class SearchView(ToolView):
        def render_streaming_call(self, tool_name: str, args: str, tool_call_id=None) -> str:
            return "<searching>...</searching>"

        def render_result(self, tool_name: str, content, tool_call_id=None, is_retry=False, max_length=500) -> str:
            return f"<search-results>{content}</search-results>"

    # Verify view is registered
    view = display_agent.get_tool_view("search")
    assert isinstance(view, SearchView)

    # Verify custom rendering
    assert "<search-results>" in view.render_result("search", "data")


async def test_display_agent_view_resolution_priority() -> None:
    """DisplayAgent should resolve views with correct priority."""

    class ExplicitView(ToolView):
        pass

    class DecoratedView(ToolView):
        pass

    model = TestModel()
    agent = Agent(model)

    # Explicit takes priority over decorated
    display_agent = DisplayAgent(agent=agent, tool_views={"my_tool": ExplicitView()})

    @display_agent.tool_view("my_tool")
    class IgnoredView(ToolView):
        pass

    view = display_agent.get_tool_view("my_tool")
    assert isinstance(view, ExplicitView)


async def test_display_agent_fallback_to_default() -> None:
    """DisplayAgent should fall back to DefaultToolView for unregistered tools."""
    model = TestModel()
    agent = Agent(model)

    display_agent = DisplayAgent(agent=agent)

    view = display_agent.get_tool_view("unknown_tool")
    assert isinstance(view, DefaultToolView)


async def test_display_agent_uses_custom_streaming_view() -> None:
    """DisplayAgent should use CustomStreamingToolCallView with resolver."""

    class CustomView(ToolView):
        def render_streaming_call(self, tool_name: str, args: str, tool_call_id=None) -> str:
            return f"<streaming>{tool_name}</streaming>"

    model = TestModel()
    agent = Agent(model)

    @agent.tool_plain
    def slow_tool(x: int) -> int:
        """A tool."""
        return x * 2

    display_agent = DisplayAgent(agent=agent, tool_views={"slow_tool": CustomView()})

    with patch("pydantic_ai_jupyter.models.display") as mock_display:
        await display_agent.run("Use slow_tool")

        # Find CustomStreamingToolCallView
        displayed_items = [call[0][0] for call in mock_display.call_args_list]
        streaming_views = [item for item in displayed_items if isinstance(item, CustomStreamingToolCallView)]

        assert len(streaming_views) > 0, "Should have displayed CustomStreamingToolCallView"

        # Verify it has the custom tool_view
        assert isinstance(streaming_views[0].tool_view, CustomView)


async def test_display_agent_debug_mode() -> None:
    """DisplayAgent should pass debug flag through."""
    model = TestModel()
    agent = Agent(model)

    display_agent = DisplayAgent(agent=agent, debug=True)

    with patch("pydantic_ai_jupyter.display.display") as mock_display:
        await display_agent.run("Hello")

        # Debug mode should show more events
        # Just verify it runs without error
        assert mock_display.called


async def test_display_agent_passes_kwargs() -> None:
    """DisplayAgent.run should pass kwargs to agent."""
    model = TestModel()
    agent = Agent(model)

    display_agent = DisplayAgent(agent=agent)

    # This should work - message_history is a valid kwarg
    result = await display_agent.run("Hello")
    assert result is not None

    # Run with message_history
    result2 = await display_agent.run("Continue", message_history=result.all_messages())
    assert result2 is not None


async def test_display_agent_multiple_tools_different_views() -> None:
    """DisplayAgent should use different views for different tools."""

    class ToolAView(ToolView):
        def render_result(self, tool_name: str, content, **kwargs) -> str:
            return f"<tool-a>{content}</tool-a>"

    class ToolBView(ToolView):
        def render_result(self, tool_name: str, content, **kwargs) -> str:
            return f"<tool-b>{content}</tool-b>"

    model = TestModel()
    agent = Agent(model)

    display_agent = DisplayAgent(
        agent=agent,
        tool_views={
            "tool_a": ToolAView(),
            "tool_b": ToolBView(),
        },
    )

    view_a = display_agent.get_tool_view("tool_a")
    view_b = display_agent.get_tool_view("tool_b")
    view_c = display_agent.get_tool_view("tool_c")  # Not registered

    assert isinstance(view_a, ToolAView)
    assert isinstance(view_b, ToolBView)
    assert isinstance(view_c, DefaultToolView)
