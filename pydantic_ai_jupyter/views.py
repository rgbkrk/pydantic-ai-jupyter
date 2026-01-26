"""View classes for rendering pydantic-ai events in Jupyter notebooks."""

from __future__ import annotations

import json
import traceback
from html import escape
from typing import Any

from pydantic import Field
from pydantic_ai.messages import (
    FinalResultEvent,
    PartEndEvent,
    PartStartEvent,
    RetryPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
)

from .models import View


class ToolCallView(View):
    """Renders a tool call with its arguments."""

    tool_name: str
    args: str | dict[str, Any] | None = None
    tool_call_id: str | None = None

    @classmethod
    def from_part(cls, part: ToolCallPart) -> ToolCallView:
        return cls(
            tool_name=part.tool_name, args=part.args, tool_call_id=part.tool_call_id
        )

    def render(self) -> str:
        args_str = (
            json.dumps(self.args, indent=2)
            if isinstance(self.args, dict)
            else str(self.args or "{}")
        )
        return f"""
        <div style="border-left: 3px solid #3b82f6; padding: 8px 12px; margin: 8px 0; background: #eff6ff; border-radius: 4px;">
            <div style="font-weight: 600; color: #1d4ed8; margin-bottom: 4px;">
                🔧 <code style="background: #dbeafe; padding: 2px 6px; border-radius: 3px;">{escape(self.tool_name)}</code>
            </div>
            <pre style="margin: 0; font-size: 12px; background: #f8fafc; padding: 8px; border-radius: 3px; overflow-x: auto;">{escape(args_str)}</pre>
        </div>
        """

    def __repr__(self) -> str:
        args_str = (
            json.dumps(self.args)
            if isinstance(self.args, dict)
            else str(self.args or "{}")
        )
        if len(args_str) > 200:
            args_str = args_str[:200] + "..."
        return f"🔧 {self.tool_name}({args_str})"


class ToolResultView(View):
    """Renders a tool result (success or retry)."""

    tool_name: str
    content: Any
    tool_call_id: str | None = None
    is_retry: bool = False
    max_length: int = 500

    @classmethod
    def from_part(cls, part: ToolReturnPart | RetryPromptPart) -> ToolResultView:
        return cls(
            tool_name=part.tool_name or "unknown",
            content=part.content if hasattr(part, "content") else str(part),
            tool_call_id=part.tool_call_id,
            is_retry=isinstance(part, RetryPromptPart),
        )

    def render(self) -> str:
        content_str = (
            self.content
            if isinstance(self.content, str)
            else json.dumps(self.content, indent=2)
        )
        if len(content_str) > self.max_length:
            content_str = content_str[: self.max_length] + "..."

        if self.is_retry:
            return f"""
            <div style="border-left: 3px solid #f59e0b; padding: 8px 12px; margin: 8px 0; background: #fffbeb; border-radius: 4px;">
                <div style="font-weight: 600; color: #b45309; margin-bottom: 4px;">
                    🔄 Retry: <code style="background: #fef3c7; padding: 2px 6px; border-radius: 3px;">{escape(self.tool_name)}</code>
                </div>
                <pre style="margin: 0; font-size: 12px; background: #fffdf5; padding: 8px; border-radius: 3px; overflow-x: auto; white-space: pre-wrap;">{escape(content_str)}</pre>
            </div>
            """
        else:
            return f"""
            <div style="border-left: 3px solid #10b981; padding: 8px 12px; margin: 8px 0; background: #ecfdf5; border-radius: 4px;">
                <div style="font-weight: 600; color: #047857; margin-bottom: 4px;">
                    ✅ Result: <code style="background: #d1fae5; padding: 2px 6px; border-radius: 3px;">{escape(self.tool_name)}</code>
                </div>
                <pre style="margin: 0; font-size: 12px; background: #f0fdf4; padding: 8px; border-radius: 3px; overflow-x: auto; white-space: pre-wrap;">{escape(content_str)}</pre>
            </div>
            """

    def __repr__(self) -> str:
        content_str = (
            self.content
            if isinstance(self.content, str)
            else json.dumps(self.content, indent=2)
        )
        return f"✅ {self.tool_name} → {content_str}"


class ErrorView(View):
    """Renders an exception with optional traceback."""

    error_type: str
    message: str
    details: str | None = None

    @classmethod
    def from_exception(cls, exc: Exception) -> ErrorView:
        return cls(
            error_type=type(exc).__name__,
            message=str(exc),
            details=traceback.format_exc(),
        )

    def render(self) -> str:
        details_html = ""
        if self.details:
            details = self.details
            if len(details) > 1000:
                details = details[-1000:]
            escaped = escape(details)

            details_html = f"""<details style="margin-top: 8px;">
                <summary style="cursor: pointer; color: #991b1b;">Show traceback</summary>
                <pre style="margin: 4px 0 0 0; font-size: 11px; background: #fef2f2; padding: 8px; border-radius: 3px; overflow-x: auto; white-space: pre-wrap;">{escaped}</pre>
            </details>"""

        return f"""
        <div style="border-left: 3px solid #dc2626; padding: 8px 12px; margin: 8px 0; background: #fef2f2; border-radius: 4px;">
            <div style="font-weight: 600; color: #dc2626; margin-bottom: 4px;">
                ❌ <code style="background: #fee2e2; padding: 2px 6px; border-radius: 3px;">{escape(self.error_type)}</code>
            </div>
            <div style="font-size: 13px; color: #7f1d1d;">{escape(self.message)}</div>
            {details_html}
        </div>
        """

    def __repr__(self) -> str:
        return f"❌ {self.error_type}: {self.message}"


class ThinkingView(View):
    """A live-updating view for model thinking/reasoning content."""

    content: str

    def __init__(self, content: str = ""):
        super().__init__()
        self.content = content

    def render(self) -> str:
        escaped = escape(self.content)

        return f"""
        <details style="margin: 8px 0;" open>
            <summary style="cursor: pointer; font-weight: 600; color: #6b7280; font-size: 12px;">
                💭 Thinking...
            </summary>
            <div style="border-left: 3px solid #9ca3af; padding: 8px 12px; margin: 4px 0; background: #f9fafb; border-radius: 4px;">
                <pre style="margin: 0; font-size: 12px; color: #4b5563; white-space: pre-wrap; font-family: inherit;">{escaped}</pre>
            </div>
        </details>
        """

    def append(self, text: str) -> None:
        """Append text and update the display."""
        self.content += text
        self.update()

    def __repr__(self) -> str:
        preview = (
            self.content[:100] + "..." if len(self.content) > 100 else self.content
        )
        return f"💭 Thinking: {preview}"


class DebugEventView(View):
    """Renders debug/lifecycle events in a muted style."""

    event_type: str
    summary: str
    details: str | None = None

    def __repr__(self) -> str:
        return f"⚙️ {self.event_type}: {self.summary}"

    @classmethod
    def from_event(cls, event: Any) -> DebugEventView:
        """Create a debug view from any event."""
        event_type = type(event).__name__

        if isinstance(event, PartEndEvent):
            part = event.part
            part_type = type(part).__name__
            if isinstance(part, TextPart):
                preview = (
                    part.content[:50] + "..."
                    if len(part.content) > 50
                    else part.content
                )
                summary = f"{part_type} completed"
                details = f"Content: {preview}"
            elif isinstance(part, ThinkingPart):
                summary = f"{part_type} completed"
                details = None
            elif isinstance(part, ToolCallPart):
                summary = f"{part_type} completed: {part.tool_name}"
                details = None
            else:
                summary = f"{part_type} completed"
                details = None
            next_kind = getattr(event, "next_part_kind", None)
            if next_kind:
                summary += f" → {next_kind}"
        elif isinstance(event, PartStartEvent):
            part = event.part
            part_type = type(part).__name__
            if isinstance(part, ToolCallPart):
                summary = f"{part_type}: {part.tool_name}"
                details = (
                    part.args if isinstance(part.args, str) else json.dumps(part.args)
                )
            else:
                summary = f"{part_type} starting"
                details = None
        elif isinstance(event, FinalResultEvent):
            summary = "Agent completed"
            if event.tool_name:
                details = f"via tool: {event.tool_name}"
            else:
                details = "text response"
        else:
            summary = str(event)[:100]
            details = None

        return cls(event_type=event_type, summary=summary, details=details)

    def render(self) -> str:
        details_html = ""
        if self.details:
            details = self.details
            if len(details) > 100:
                escaped = details[:100] + "..."
            escaped = escape(details)
            details_html = f'<span style="color: #9ca3af;"> · {escaped}</span>'

        return f"""
        <div style="padding: 2px 8px; margin: 2px 0; font-size: 11px; color: #6b7280; font-family: monospace;">
            ⚙️ <span style="color: #9ca3af;">{self.event_type}</span>: {escape(self.summary)}{details_html}
        </div>
        """


class StreamingToolCallView(View):
    """A live-updating view for tool call arguments as they stream in."""

    tool_name: str = Field(default="", description="The name of the tool being called.")
    args: str = Field(default="", description="The arguments being passed to the tool.")
    tool_call_id: str | None = Field(
        default=None, description="The ID of the tool call."
    )

    def render(self) -> str:
        args_escaped = escape(self.args)
        cursor = (
            '<span style="animation: blink 1s infinite;">▊</span>'
            if not args_escaped.endswith("}")
            else ""
        )
        return f"""
        <style>@keyframes blink {{ 50% {{ opacity: 0; }} }}</style>
        <div style="border-left: 3px solid #3b82f6; padding: 8px 12px; margin: 8px 0; background: #eff6ff; border-radius: 4px;">
            <div style="font-weight: 600; color: #1d4ed8; margin-bottom: 4px;">
                🔧 <code style="background: #dbeafe; padding: 2px 6px; border-radius: 3px;">{escape(self.tool_name)}</code>
            </div>
            <pre style="margin: 0; font-size: 12px; background: #f8fafc; padding: 8px; border-radius: 3px; overflow-x: auto;">{args_escaped}{cursor}</pre>
        </div>
        """

    def append_args(self, delta: str) -> None:
        """Append to args and update the display."""
        self.args += delta
        self.update()

    def append_tool_name(self, delta: str) -> None:
        """Append to tool name and update the display."""
        self.tool_name += delta
        self.update()

    def __repr__(self) -> str:
        return f"🔧 {self.tool_name}({self.args})"
