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
"""

from .display import run_in_jupyter
from .markdown import Markdown
from .views import (
    DebugEventView,
    ErrorView,
    StreamingToolCallView,
    ThinkingView,
    ToolCallView,
    ToolResultView,
)

__all__ = [
    "run_in_jupyter",
    "Markdown",
    "ToolCallView",
    "ToolResultView",
    "ErrorView",
    "ThinkingView",
    "DebugEventView",
    "StreamingToolCallView",
]

__version__ = "0.1.2"
