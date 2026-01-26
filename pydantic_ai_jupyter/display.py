"""Main display runner for pydantic-ai agents in Jupyter notebooks."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from IPython.display import display
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
    DebugEventView,
    ErrorView,
    StreamingToolCallView,
    ThinkingView,
    ToolResultView,
)

if TYPE_CHECKING:
    from pydantic_ai import Agent


async def run_with_display(
    agent: Agent[Any, Any],
    user_prompt: str | None = None,
    *,
    debug: bool = False,
    **kwargs: Any,
) -> Any | None:
    """Run an agent with live Jupyter display of tool calls and streaming text.

    All arguments except `debug` are passed directly to `agent.run_stream_events()`.

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
        result = await run_with_display(agent, "What's the weather?")

        # Multi-turn conversation
        result = await run_with_display(
            agent, "What about London?",
            message_history=result.all_messages(),
        )

        # With dependencies and settings
        result = await run_with_display(
            agent, "Analyze this",
            deps=my_deps,
            model_settings={"temperature": 0.5},
        )
        ```
    """
    current_markdown: Markdown | None = None
    current_thinking: ThinkingView | None = None
    # Track streaming tool calls by part index
    streaming_tool_calls: dict[int, StreamingToolCallView] = {}

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
            if isinstance(event, PartStartEvent) and isinstance(
                event.part, ToolCallPart
            ):
                finish_markdown()
                finish_thinking()
                # Start a new streaming tool call view
                view = StreamingToolCallView(
                    tool_name=event.part.tool_name,
                    args=event.part.args
                    if isinstance(event.part.args, str)
                    else json.dumps(event.part.args),
                    tool_call_id=event.part.tool_call_id,
                )
                view.display()
                view.update()  # Show initial state
                streaming_tool_calls[event.index] = view

            elif isinstance(event, PartDeltaEvent) and isinstance(
                event.delta, ToolCallPartDelta
            ):
                # Append to streaming tool call
                if event.index in streaming_tool_calls:
                    view = streaming_tool_calls[event.index]
                    if event.delta.args_delta:
                        if isinstance(event.delta.args_delta, str):
                            view.append_args(event.delta.args_delta)
                        # TODO: Presumably this is a dict if it's fully parsed JSON already
                        else:  # dict[str, Any]
                            view.append_args(json.dumps(event.delta.args_delta))
                    if event.delta.tool_name_delta:
                        view.append_tool_name(event.delta.tool_name_delta)

            elif isinstance(event, FunctionToolCallEvent):
                # Tool call complete - streaming view already shown, just mark handled
                # Clear the streaming view for this tool (it's now finalized)
                pass

            elif isinstance(event, FunctionToolResultEvent):
                display(ToolResultView.from_part(event.result))

            # Handle thinking parts
            elif isinstance(event, PartStartEvent) and isinstance(
                event.part, ThinkingPart
            ):
                if event.part.content:
                    get_or_create_thinking().append(event.part.content)

            elif isinstance(event, PartDeltaEvent) and isinstance(
                event.delta, ThinkingPartDelta
            ):
                if event.delta.content_delta:
                    get_or_create_thinking().append(event.delta.content_delta)

            # Handle text parts
            elif isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
                finish_thinking()  # Thinking done, now outputting text
                finish_streaming_tool_calls()  # Clear tool call tracking
                if event.part.content:
                    get_or_create_markdown().append(event.part.content)

            elif isinstance(event, PartDeltaEvent) and isinstance(
                event.delta, TextPartDelta
            ):
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
        return None

    return None
