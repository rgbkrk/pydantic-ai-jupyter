from __future__ import annotations as _annotations

import pytest
from inline_snapshot import snapshot
from pydantic_ai.messages import RetryPromptPart, ToolCallPart, ToolReturnPart

from pydantic_ai_jupyter.views import (
    DebugEventView,
    ErrorView,
    StreamingToolCallView,
    ThinkingView,
    ToolCallView,
    ToolResultView,
)

pytestmark = pytest.mark.anyio


async def test_tool_call_view_from_part() -> None:
    """ToolCallView should render from ToolCallPart."""
    part = ToolCallPart(
        tool_name="get_weather",
        args={"city": "San Francisco", "unit": "celsius"},
        tool_call_id="call_123",
    )
    view = ToolCallView.from_part(part)

    assert view.tool_name == "get_weather"
    assert view.args == {"city": "San Francisco", "unit": "celsius"}
    assert view.tool_call_id == "call_123"


async def test_tool_call_view_render() -> None:
    """ToolCallView should render HTML with args."""
    view = ToolCallView(tool_name="calculate", args='{"x": 5, "y": 10}')

    html = view.render()
    assert "calculate" in html
    assert "x" in html
    assert "5" in html


async def test_tool_call_view_repr() -> None:
    """ToolCallView should have concise repr."""
    view = ToolCallView(tool_name="test_tool", args={"key": "value"})

    assert repr(view) == snapshot('🔧 test_tool({"key": "value"})')


async def test_tool_result_view_success() -> None:
    """ToolResultView should render successful results."""
    part = ToolReturnPart(tool_name="get_data", content="Success data", tool_call_id="call_456")
    view = ToolResultView.from_part(part)

    assert view.tool_name == "get_data"
    assert view.content == "Success data"
    assert view.is_retry is False


async def test_tool_result_view_retry() -> None:
    """ToolResultView should handle retry prompts."""
    part = RetryPromptPart(tool_name="failing_tool", content="Please try again", tool_call_id="call_789")
    view = ToolResultView.from_part(part)

    assert view.tool_name == "failing_tool"
    assert view.is_retry is True


async def test_tool_result_view_truncates_long_content() -> None:
    """ToolResultView should truncate content longer than max_length."""
    long_content = "x" * 1000
    view = ToolResultView(tool_name="big_result", content=long_content, max_length=100)

    html = view.render()
    assert "..." in html
    assert len(html) < len(long_content) + 500  # Much shorter than full content


async def test_error_view_from_exception() -> None:
    """ErrorView should capture exception details."""
    try:
        raise ValueError("Something went wrong")
    except ValueError as e:
        view = ErrorView.from_exception(e)

    assert view.error_type == "ValueError"
    assert view.message == "Something went wrong"
    assert view.details is not None
    assert "ValueError" in view.details


async def test_error_view_render() -> None:
    """ErrorView should render error HTML."""
    view = ErrorView(error_type="RuntimeError", message="Test error", details="Traceback here")

    html = view.render()
    assert "RuntimeError" in html
    assert "Test error" in html
    assert "traceback" in html.lower()


async def test_streaming_tool_call_view_append_args() -> None:
    """StreamingToolCallView should accumulate args."""
    view = StreamingToolCallView(tool_name="test", args="{")

    view.append_args('"key": ')
    view.append_args('"value"')
    view.append_args("}")

    assert view.args == snapshot('{"key": "value"}')


async def test_streaming_tool_call_view_append_tool_name() -> None:
    """StreamingToolCallView should accumulate tool name."""
    view = StreamingToolCallView(tool_name="get")

    view.append_tool_name("_weather")

    assert view.tool_name == "get_weather"


async def test_debug_event_view_render() -> None:
    """DebugEventView should render debug information."""
    view = DebugEventView(event_type="PartStartEvent", summary="Text part starting", details="Content: Hello")

    html = view.render()
    assert "PartStartEvent" in html
    assert "Text part starting" in html
