"""Tests for ToolView and DefaultToolView classes."""

from __future__ import annotations as _annotations

import pytest
from inline_snapshot import snapshot

from pydantic_ai_jupyter.tool_views import DefaultToolView, ToolView

pytestmark = pytest.mark.anyio


async def test_default_tool_view_render_call() -> None:
    """DefaultToolView should render a tool call with default styling."""
    view = DefaultToolView()
    html = view.render_call("test_tool", {"key": "value"})

    assert "test_tool" in html
    assert "key" in html
    assert "value" in html
    assert "border-left: 3px solid #3b82f6" in html  # Blue border


async def test_default_tool_view_render_call_with_dict_args() -> None:
    """DefaultToolView render_call takes dict args (complete tool calls have parsed JSON)."""
    view = DefaultToolView()
    html = view.render_call("my_tool", {"x": 1})

    assert "my_tool" in html
    # Should render the dict as formatted JSON
    assert "&quot;x&quot;: 1" in html


async def test_default_tool_view_render_streaming_call() -> None:
    """DefaultToolView should render streaming call with cursor."""
    view = DefaultToolView()
    html = view.render_streaming_call("search", '{"query": "hello')

    assert "search" in html
    assert "hello" in html
    # Should have cursor since args don't end with }
    assert "animation: blink" in html


async def test_default_tool_view_render_streaming_call_complete() -> None:
    """DefaultToolView should not show cursor when args are complete."""
    view = DefaultToolView()
    html = view.render_streaming_call("search", '{"query": "hello"}')

    # Should NOT have cursor since args end with }
    # The cursor character should not be present
    assert "▊" not in html


async def test_default_tool_view_render_result_success() -> None:
    """DefaultToolView should render success results with green styling."""
    view = DefaultToolView()
    html = view.render_result("get_data", "Success!")

    assert "get_data" in html
    assert "Success!" in html
    assert "border-left: 3px solid #10b981" in html  # Green border
    assert "Result:" in html


async def test_default_tool_view_render_result_retry() -> None:
    """DefaultToolView should render retry results with amber styling."""
    view = DefaultToolView()
    html = view.render_result("failing_tool", "Please retry", is_retry=True)

    assert "failing_tool" in html
    assert "Please retry" in html
    assert "border-left: 3px solid #f59e0b" in html  # Amber border
    assert "Retry:" in html


async def test_default_tool_view_render_result_truncates() -> None:
    """DefaultToolView should truncate long content."""
    view = DefaultToolView()
    long_content = "x" * 1000
    html = view.render_result("big_result", long_content, max_length=100)

    assert "..." in html
    # Should be truncated
    assert "x" * 100 in html
    assert "x" * 200 not in html


async def test_default_tool_view_render_result_json_content() -> None:
    """DefaultToolView should JSON-serialize dict content."""
    view = DefaultToolView()
    html = view.render_result("data_tool", {"items": [1, 2, 3]})

    assert "items" in html
    assert "[1, 2, 3]" in html or "[\n" in html  # Pretty-printed


async def test_custom_tool_view_subclass() -> None:
    """Custom ToolView subclass should override render methods."""

    class CustomView(ToolView):
        def render_call(self, tool_name: str, args, tool_call_id=None) -> str:
            return f"<custom-call>{tool_name}</custom-call>"

        def render_result(self, tool_name: str, content, tool_call_id=None, is_retry=False, max_length=500) -> str:
            return f"<custom-result>{content}</custom-result>"

    view = CustomView()

    call_html = view.render_call("my_tool", {})
    assert call_html == "<custom-call>my_tool</custom-call>"

    result_html = view.render_result("my_tool", "data")
    assert result_html == "<custom-result>data</custom-result>"


async def test_custom_tool_view_partial_override() -> None:
    """Custom ToolView can override just some methods."""

    class PartialView(ToolView):
        def render_result(self, tool_name: str, content, tool_call_id=None, is_retry=False, max_length=500) -> str:
            return f"<special>{content}</special>"

    view = PartialView()

    # render_call should use default implementation
    call_html = view.render_call("test", {"a": 1})
    assert "border-left: 3px solid #3b82f6" in call_html

    # render_result should use custom implementation
    result_html = view.render_result("test", "result")
    assert result_html == "<special>result</special>"


async def test_tool_view_escapes_html() -> None:
    """ToolView should escape HTML in tool names and content."""
    view = DefaultToolView()

    html = view.render_call("<script>alert('xss')</script>", {"key": "<b>value</b>"})

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<b>" not in html


async def test_tool_view_render_call_snapshot() -> None:
    """Snapshot test for render_call output."""
    view = DefaultToolView()
    html = view.render_call("calculate", {"x": 5, "y": 10})

    # Just verify the key elements are present
    assert "calculate" in html
    assert "border-left: 3px solid #3b82f6" in html
    assert "&quot;x&quot;: 5" in html
    assert "&quot;y&quot;: 10" in html
