# pydantic-ai-jupyter

[![Tests](https://github.com/rgbkrk/pydantic-ai-jupyter/workflows/Tests/badge.svg)](https://github.com/rgbkrk/pydantic-ai-jupyter/actions)

Experiment with [Pydantic AI](https://github.com/pydantic/pydantic-ai) Agents interactively in Jupyter notebooks.

## Installation

```bash
pip install pydantic-ai-jupyter
```

Or with uv:

```bash
uv add pydantic-ai-jupyter
```

## Usage

```python
from pydantic_ai import Agent
from pydantic_ai_jupyter import run_in_jupyter

agent = Agent("openai:gpt-4o-mini")

@agent.tool_plain
def get_weather(city: str) -> str:
    return f"Sunny, 22°C in {city}"

# Run with rich display
result = await run_in_jupyter(agent, "What's the weather in Tokyo?")
```

### Features

- **Streaming text** - See the model's response as it generates
- **Streaming tool calls** - Watch tool arguments stream in (with providers that support it, like OpenAI)
- **Tool results** - Styled success and retry results
- **Thinking/reasoning** - Collapsible display of model thinking
- **Error handling** - Graceful display of exceptions with tracebacks

### Multi-turn conversations

```python
# First turn
result = await run_in_jupyter(agent, "What's the weather in Tokyo?")

# Continue the conversation
result = await run_in_jupyter(
    agent,
    "What about London?",
    message_history=result.all_messages(),
)
```

### Debug mode

Enable debug mode to see all events:

```python
result = await run_in_jupyter(agent, "Hello!", debug=True)
```

## Supported providers

Tool call argument streaming works best with **OpenAI**, which streams arguments token-by-token. Other providers like Groq and Ollama (via OpenAI-compat) buffer tool calls and send them all at once.

| Provider | Text streaming | Tool call streaming |
|----------|----------------|---------------------|
| OpenAI   | ✅ | ✅ |
| Groq     | ✅ | ❌ (buffered) |
| Ollama   | ✅ | ❌ (buffered) |

## Development

See [TESTING.md](TESTING.md) for testing guidelines and [PUBLISHING.md](PUBLISHING.md) for release instructions.

```bash
# Install dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Run linting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy pydantic_ai_jupyter/
```

## License

BSD 3-Clause
