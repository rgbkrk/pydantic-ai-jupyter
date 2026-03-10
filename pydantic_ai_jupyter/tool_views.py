"""Custom tool view classes for rendering tool calls and results.

This module provides the ToolView base class for creating custom renderers
for specific tools, allowing per-tool customization of how tool calls,
streaming arguments, and results are displayed.

Example:
    ```python
    from pydantic_ai_jupyter import DisplayAgent, ToolView

    class WeatherView(ToolView):
        def render_result(self, tool_name: str, content: Any, **kwargs) -> str:
            return f"<div class='weather'>{content}</div>"

    display_agent = DisplayAgent(agent, tool_views={"get_weather": WeatherView()})
    result = await display_agent.run("What's the weather?")
    ```
"""

from __future__ import annotations

import json
from html import escape
from typing import Any

from pydantic import BaseModel


class ToolView(BaseModel):
    """Base class for custom tool views.

    Subclasses can override any of the render_* methods to customize
    how that particular aspect of the tool is displayed. All methods
    have sensible defaults that match the standard rendering.

    Methods:
        render_call: Render a completed tool call with its arguments
        render_streaming_call: Render a tool call as arguments stream in
        render_result: Render a tool's return value or retry prompt
    """

    model_config = {"arbitrary_types_allowed": True}

    def render_call(
        self,
        tool_name: str,
        args: dict[str, Any],
        tool_call_id: str | None = None,
    ) -> str:
        """Render a completed tool call.

        Args:
            tool_name: The name of the tool being called
            args: The fully parsed arguments dict
            tool_call_id: Optional unique identifier for this tool call

        Returns:
            HTML string to display
        """
        args_str = json.dumps(args, indent=2)
        return f"""
        <div style="border-left: 3px solid #3b82f6; padding: 8px 12px; margin: 8px 0; background: #eff6ff; border-radius: 4px;">
            <div style="font-weight: 600; color: #1d4ed8; margin-bottom: 4px;">
                🔧 <code style="background: #dbeafe; padding: 2px 6px; border-radius: 3px;">{escape(tool_name)}</code>
            </div>
            <pre style="margin: 0; font-size: 12px; background: #f8fafc; padding: 8px; border-radius: 3px; overflow-x: auto;">{escape(args_str)}</pre>
        </div>
        """

    def render_streaming_call(
        self,
        tool_name: str,
        args: str | dict[str, Any],
        tool_call_id: str | None = None,
    ) -> str:
        """Render a tool call as arguments stream in.

        This is called repeatedly as more argument data arrives.
        The default implementation shows a blinking cursor while streaming.

        Args:
            tool_name: The name of the tool being called
            args: The partial arguments - either a dict (parsed partial JSON) or
                  a raw string if parsing failed
            tool_call_id: Optional unique identifier for this tool call

        Returns:
            HTML string to display
        """
        # Convert args to string for display
        if isinstance(args, dict):
            args_str = json.dumps(args, indent=2)
        else:
            args_str = str(args or "{}")
        args_escaped = escape(args_str)
        cursor = '<span style="animation: blink 1s infinite;">▊</span>' if not args_escaped.endswith("}") else ""
        return f"""
        <style>@keyframes blink {{ 50% {{ opacity: 0; }} }}</style>
        <div style="border-left: 3px solid #3b82f6; padding: 8px 12px; margin: 8px 0; background: #eff6ff; border-radius: 4px;">
            <div style="font-weight: 600; color: #1d4ed8; margin-bottom: 4px;">
                🔧 <code style="background: #dbeafe; padding: 2px 6px; border-radius: 3px;">{escape(tool_name)}</code>
            </div>
            <pre style="margin: 0; font-size: 12px; background: #f8fafc; padding: 8px; border-radius: 3px; overflow-x: auto;">{args_escaped}{cursor}</pre>
        </div>
        """

    def render_result(
        self,
        tool_name: str,
        content: Any,
        tool_call_id: str | None = None,
        is_retry: bool = False,
        max_length: int = 500,
    ) -> str:
        """Render a tool result.

        Args:
            tool_name: The name of the tool that produced this result
            content: The result content (any type, will be JSON-serialized if needed)
            tool_call_id: Optional unique identifier for this tool call
            is_retry: True if this is a retry/error prompt rather than success
            max_length: Maximum content length before truncation

        Returns:
            HTML string to display
        """
        content_str = content if isinstance(content, str) else json.dumps(content, indent=2)
        if len(content_str) > max_length:
            content_str = content_str[:max_length] + "..."

        if is_retry:
            return f"""
            <div style="border-left: 3px solid #f59e0b; padding: 8px 12px; margin: 8px 0; background: #fffbeb; border-radius: 4px;">
                <div style="font-weight: 600; color: #b45309; margin-bottom: 4px;">
                    🔄 Retry: <code style="background: #fef3c7; padding: 2px 6px; border-radius: 3px;">{escape(tool_name)}</code>
                </div>
                <pre style="margin: 0; font-size: 12px; background: #fffdf5; padding: 8px; border-radius: 3px; overflow-x: auto; white-space: pre-wrap;">{escape(content_str)}</pre>
            </div>
            """
        else:
            return f"""
            <div style="border-left: 3px solid #10b981; padding: 8px 12px; margin: 8px 0; background: #ecfdf5; border-radius: 4px;">
                <div style="font-weight: 600; color: #047857; margin-bottom: 4px;">
                    ✅ Result: <code style="background: #d1fae5; padding: 2px 6px; border-radius: 3px;">{escape(tool_name)}</code>
                </div>
                <pre style="margin: 0; font-size: 12px; background: #f0fdf4; padding: 8px; border-radius: 3px; overflow-x: auto; white-space: pre-wrap;">{escape(content_str)}</pre>
            </div>
            """


class DefaultToolView(ToolView):
    """The default tool view used when no custom view is registered.

    This class uses all the default render_* implementations from ToolView,
    which produce the standard blue/green/amber styling.
    """

    pass
