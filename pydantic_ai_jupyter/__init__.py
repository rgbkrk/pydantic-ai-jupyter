"""Rich Jupyter display for pydantic-ai agents.

This package provides live-updating displays for pydantic-ai agent runs
in Jupyter notebooks, including streaming text, tool calls, and results.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_jupyter import run_in_jupyter

    agent = Agent("openai:gpt-4o-mini")

    @agent.tool_plain
    def get_weather(city: str) -> str:
        return f"Sunny in {city}"

    result = await run_in_jupyter(agent, "What's the weather in Tokyo?")
    ```

For custom per-tool rendering, use DisplayAgent:
    ```python
    from pydantic_ai_jupyter import DisplayAgent, ToolView

    class WeatherView(ToolView):
        def render_result(self, tool_name, content, **kwargs):
            return f"<div class='weather'>{content}</div>"

    display_agent = DisplayAgent(agent, tool_views={"get_weather": WeatherView()})
    result = await display_agent.run("What's the weather?")
    ```
"""

from .display import run_in_jupyter
from .display_agent import DisplayAgent
from .markdown import Markdown
from .tool_views import DefaultToolView, ToolView
from .views import (
    CustomStreamingToolCallView,
    CustomToolResultView,
    DebugEventView,
    ErrorView,
    StreamingToolCallView,
    ThinkingView,
    ToolCallView,
    ToolResultView,
)

__all__ = [
    # Main API
    "run_in_jupyter",
    "DisplayAgent",
    # Custom tool rendering
    "ToolView",
    "DefaultToolView",
    # View classes
    "Markdown",
    "ToolCallView",
    "ToolResultView",
    "ErrorView",
    "ThinkingView",
    "DebugEventView",
    "StreamingToolCallView",
    "CustomStreamingToolCallView",
    "CustomToolResultView",
]

__version__ = "0.1.0"
