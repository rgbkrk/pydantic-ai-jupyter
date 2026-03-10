"""Main display runner for pydantic-ai agents in Jupyter notebooks."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable

from IPython.display import display
from pydantic_ai import AgentRunResult
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ThinkingPart,
    ThinkingPartDelta,
    ToolCallPart,
    ToolCallPartDelta,
)
from pydantic_ai.run import AgentRunResultEvent

from .markdown import Markdown
from .views import (
    CustomStreamingToolCallView,
    CustomToolResultView,
    DebugEventView,
    ErrorView,
    StreamingToolCallView,
    ThinkingView,
    ToolResultView,
)

if TYPE_CHECKING:
    from pydantic_ai import Agent

    from .tool_views import ToolView


async def run_in_jupyter_with_views(
    agent: Agent[Any, Any],
    user_prompt: str | None = None,
    *,
    tool_view_resolver: Callable[[str], ToolView] | None = None,
    debug: bool = False,
    **kwargs: Any,
) -> AgentRunResult[Any] | None:
    """Run an agent with live Jupyter display and custom tool views.

    This is the internal implementation used by both run_in_jupyter and
    DisplayAgent.run(). It supports custom per-tool rendering via the
    tool_view_resolver parameter.

    Args:
        agent: The pydantic-ai Agent to run
        user_prompt: The user's prompt/question
        tool_view_resolver: Optional function that takes a tool name and returns
            a ToolView instance for custom rendering. If None, uses default views.
        debug: If True, display unhandled lifecycle events
        **kwargs: Passed to agent.run_stream_events() - includes deps, message_history,
                  model_settings, usage_limits, toolsets, etc.

    Returns:
        The agent result, or None if an exception occurred
    """
    current_markdown: Markdown | None = None
    current_thinking: ThinkingView | None = None

    # Choose view types based on whether we have custom rendering
    use_custom_views = tool_view_resolver is not None

    # Track streaming tool calls by part index
    streaming_tool_calls: dict[int, StreamingToolCallView | CustomStreamingToolCallView] = {}

    def get_or_create_markdown() -> Markdown:
        nonlocal current_markdown
        if current_markdown is None:
            current_markdown = Markdown(content="")
            current_markdown.display()
        return current_markdown

    def finish_markdown() -> None:
        nonlocal current_markdown
        current_markdown = None

    def get_or_create_thinking() -> ThinkingView:
        nonlocal current_thinking
        if current_thinking is None:
            current_thinking = ThinkingView(content="")
            current_thinking.display()
        return current_thinking

    def finish_thinking() -> None:
        nonlocal current_thinking
        current_thinking = None

    def finish_streaming_tool_calls() -> None:
        nonlocal streaming_tool_calls
        streaming_tool_calls = {}

    try:
        async for event in agent.run_stream_events(user_prompt, **kwargs):
            # Handle streaming tool call parts (args streaming in)
            if isinstance(event, PartStartEvent) and isinstance(event.part, ToolCallPart):
                finish_markdown()
                finish_thinking()

                # Start a new streaming tool call view
                # Convert args to string, handling None case (json.dumps(None) returns "null")
                if event.part.args is None:
                    initial_args = ""
                elif isinstance(event.part.args, str):
                    initial_args = event.part.args
                else:
                    initial_args = json.dumps(event.part.args)

                if use_custom_views and tool_view_resolver is not None:
                    tool_view = tool_view_resolver(event.part.tool_name)
                    view: StreamingToolCallView | CustomStreamingToolCallView = CustomStreamingToolCallView(
                        tool_name=event.part.tool_name,
                        args=initial_args,
                        tool_call_id=event.part.tool_call_id,
                        tool_view=tool_view,
                    )
                else:
                    view = StreamingToolCallView(
                        tool_name=event.part.tool_name,
                        args=initial_args,
                        tool_call_id=event.part.tool_call_id,
                    )
                view.display()
                view.update()
                streaming_tool_calls[event.index] = view

            elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, ToolCallPartDelta):
                if event.index in streaming_tool_calls:
                    view = streaming_tool_calls[event.index]
                    if event.delta.args_delta:
                        if isinstance(event.delta.args_delta, str):
                            view.append_args(event.delta.args_delta)
                        # TODO(rgbkrk): Determine if this dict is fully parsed JSON from the args at this point
                        else:  # dict[str, Any]
                            view.append_args(json.dumps(event.delta.args_delta))
                    if event.delta.tool_name_delta:
                        view.append_tool_name(event.delta.tool_name_delta)

            elif isinstance(event, FunctionToolCallEvent):
                # Tool call is complete (about to execute) - mark the streaming view as complete
                # Find the matching streaming view by tool_call_id
                for view in streaming_tool_calls.values():
                    if hasattr(view, "mark_complete") and view.tool_call_id == event.part.tool_call_id:
                        view.mark_complete()
                        break

            elif isinstance(event, FunctionToolResultEvent):
                if use_custom_views and tool_view_resolver is not None:
                    tool_view = tool_view_resolver(event.result.tool_name or "unknown")
                    display(CustomToolResultView.from_part(event.result, tool_view))
                else:
                    display(ToolResultView.from_part(event.result))

            elif isinstance(event, PartStartEvent) and isinstance(event.part, ThinkingPart):
                if event.part.content:
                    get_or_create_thinking().append(event.part.content)

            elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, ThinkingPartDelta):
                if event.delta.content_delta:
                    get_or_create_thinking().append(event.delta.content_delta)

            elif isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
                finish_thinking()
                finish_streaming_tool_calls()
                if event.part.content:
                    get_or_create_markdown().append(event.part.content)

            elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                if event.delta.content_delta:
                    get_or_create_markdown().append(event.delta.content_delta)

            elif isinstance(event, AgentRunResultEvent):
                return event.result
            else:
                if debug:
                    display(DebugEventView.from_event(event))

    except Exception as e:
        finish_markdown()
        finish_thinking()
        display(ErrorView.from_exception(e))
        raise

    # Never got a result
    return None


async def run_in_jupyter(
    agent: Agent[Any, Any],
    user_prompt: str | None = None,
    *,
    debug: bool = False,
    **kwargs: Any,
) -> AgentRunResult[str] | None:
    """Run an agent with live Jupyter display of tool calls and streaming text.

    All arguments except `debug` are passed directly to `agent.run_stream_events()`.

    For custom per-tool rendering, use DisplayAgent instead.

    Args:
        agent: The pydantic-ai Agent to run
        user_prompt: The user's prompt/question
        debug: If True, display unhandled lifecycle events
        **kwargs: Passed to agent.run_stream_events() - includes deps, message_history,
                  model_settings, usage_limits, toolsets, etc.

    Returns:
        The agent result, or None if an exception occurred

    Example:
        ```python
        result = await run_in_jupyter(agent, "What's the weather?")

        # Multi-turn conversation
        result = await run_in_jupyter(
            agent, "What about London?",
            message_history=result.all_messages(),
        )

        # With dependencies and settings
        result = await run_in_jupyter(
            agent, "Analyze this",
            deps=my_deps,
            model_settings={"temperature": 0.5},
        )
        ```
    """
    return await run_in_jupyter_with_views(
        agent,
        user_prompt,
        tool_view_resolver=None,
        debug=debug,
        **kwargs,
    )
