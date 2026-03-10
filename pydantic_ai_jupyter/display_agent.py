"""DisplayAgent wrapper for pydantic-ai agents with custom tool rendering.

This module provides the DisplayAgent class, which wraps a pydantic-ai Agent
to enable custom per-tool rendering in Jupyter notebooks.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_jupyter import DisplayAgent, ToolView

    agent = Agent("openai:gpt-4o-mini")

    @agent.tool_plain
    def get_weather(city: str) -> str:
        return f"Sunny in {city}"

    class WeatherView(ToolView):
        def render_result(self, tool_name, content, **kwargs):
            return f"<div class='weather'>{content}</div>"

    display_agent = DisplayAgent(agent, tool_views={"get_weather": WeatherView()})
    result = await display_agent.run("What's the weather in Tokyo?")
    ```
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, TypeVar

from .tool_views import DefaultToolView, ToolView

if TYPE_CHECKING:
    from pydantic_ai import Agent, AgentRunResult

T = TypeVar("T", bound=ToolView)


class DisplayAgent:
    """Wrapper for pydantic-ai Agent with custom tool rendering in Jupyter.

    Provides the same streaming display as run_in_jupyter but allows per-tool
    custom views for tool calls and results.

    Args:
        agent: The pydantic-ai Agent to wrap
        tool_views: Dict mapping tool names to ToolView instances for custom rendering
        debug: If True, display unhandled lifecycle events

    Example:
        ```python
        # Basic usage with custom view
        display_agent = DisplayAgent(agent, tool_views={"get_weather": WeatherView()})
        result = await display_agent.run("What's the weather?")

        # Using decorator to register views
        display_agent = DisplayAgent(agent)

        @display_agent.tool_view("get_weather")
        class WeatherView(ToolView):
            def render_result(self, tool_name, content, **kwargs):
                return f"<div>{content}</div>"

        result = await display_agent.run("What's the weather?")
        ```
    """

    def __init__(
        self,
        agent: Agent[Any, Any],
        tool_views: dict[str, ToolView] | None = None,
        *,
        debug: bool = False,
    ) -> None:
        """Initialize the DisplayAgent.

        Args:
            agent: The pydantic-ai Agent to wrap
            tool_views: Dict mapping tool names to ToolView instances for custom rendering
            debug: If True, display unhandled lifecycle events
        """
        self.agent = agent
        self.tool_views = tool_views or {}
        self.debug = debug
        self._decorated_views: dict[str, ToolView] = {}

    def tool_view(self, tool_name: str) -> Callable[[type[T]], type[T]]:
        """Decorator to register a tool view for this DisplayAgent instance.

        Args:
            tool_name: The name of the tool to customize rendering for

        Returns:
            A decorator that registers the class and returns it unchanged

        Example:
            ```python
            display_agent = DisplayAgent(agent)

            @display_agent.tool_view("search")
            class SearchView(ToolView):
                def render_streaming_call(self, tool_name, args, **kwargs):
                    return "<div>Searching...</div>"

                def render_result(self, tool_name, content, **kwargs):
                    return f"<div>Found: {content}</div>"
            ```
        """

        def decorator(cls: type[T]) -> type[T]:
            self._decorated_views[tool_name] = cls()
            return cls

        return decorator

    def get_tool_view(self, tool_name: str) -> ToolView:
        """Get the appropriate view for a tool.

        Resolution order:
        1. Instance tool_views (explicit config in constructor)
        2. Decorator-registered views (@display_agent.tool_view)
        3. DefaultToolView (built-in fallback)

        Args:
            tool_name: The name of the tool to get a view for

        Returns:
            The ToolView instance to use for rendering
        """
        # 1. Explicit instance config takes priority
        if tool_name in self.tool_views:
            return self.tool_views[tool_name]

        # 2. Decorator-registered views
        if tool_name in self._decorated_views:
            return self._decorated_views[tool_name]

        # 3. Default fallback
        return DefaultToolView()

    async def run(
        self,
        user_prompt: str | None = None,
        **kwargs: Any,
    ) -> AgentRunResult[Any] | None:
        """Run the agent with custom tool views and live Jupyter display.

        All arguments except those handled by DisplayAgent are passed directly
        to agent.run_stream_events().

        Args:
            user_prompt: The user's prompt/question
            **kwargs: Passed to agent.run_stream_events() - includes deps,
                      message_history, model_settings, usage_limits, toolsets, etc.

        Returns:
            The agent result, or None if an exception occurred

        Example:
            ```python
            # Basic run
            result = await display_agent.run("What's the weather?")

            # Multi-turn conversation
            result = await display_agent.run(
                "What about London?",
                message_history=result.all_messages(),
            )

            # With dependencies
            result = await display_agent.run(
                "Analyze this",
                deps=my_deps,
            )
            ```
        """
        from .display import run_in_jupyter_with_views

        return await run_in_jupyter_with_views(
            self.agent,
            user_prompt,
            tool_view_resolver=self.get_tool_view,
            debug=self.debug,
            **kwargs,
        )
