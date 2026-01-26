# pydantic-ai-jupyter

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
from pydantic_ai_jupyter import run_with_display

agent = Agent("openai:gpt-4o-mini")

@agent.tool_plain
def get_weather(city: str) -> str:
    return f"Sunny, 22°C in {city}"

# Run with rich display
result = await run_with_display(agent, "What's the weather in Tokyo?")
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
result = await run_with_display(agent, "What's the weather in Tokyo?")

# Continue the conversation
result = await run_with_display(
    agent,
    "What about London?",
    message_history=result.all_messages(),
)
```

### Debug mode

Enable debug mode to see all events:

```python
result = await run_with_display(agent, "Hello!", debug=True)
```

## Supported providers

Tool call argument streaming works best with **OpenAI**, which streams arguments token-by-token. Other providers like Groq and Ollama (via OpenAI-compat) buffer tool calls and send them all at once.

| Provider | Text streaming | Tool call streaming |
|----------|----------------|---------------------|
| OpenAI   | ✅ | ✅ |
| Groq     | ✅ | ❌ (buffered) |
| Ollama   | ✅ | ❌ (buffered) |

## License

BSD 3-Clause
