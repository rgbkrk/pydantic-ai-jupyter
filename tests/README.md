# Tests

Test suite for pydantic-ai-jupyter using pytest, inline-snapshot, and TestModel.

## Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_display.py -v

# Run with coverage
uv run pytest tests/ --cov=pydantic_ai_jupyter

# Update snapshots
uv run pytest tests/ --inline-snapshot=fix
```

## Structure

- `test_display.py` - Tests for `run_with_display` using TestModel
- `test_views.py` - Tests for view components (ToolCallView, ErrorView, etc.)
- `test_markdown.py` - Tests for Markdown rendering and streaming

## Key Patterns

### Using TestModel

```python
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

async def test_basic_agent() -> None:
    model = TestModel()
    agent = Agent(model)
    
    result = await run_with_display(agent, "Hello")
    assert result is not None
    assert result.output == snapshot("success (no tool calls)")
```

### Inline Snapshots

Snapshots capture expected values inline:

```python
from inline_snapshot import snapshot

async def test_output() -> None:
    result = get_result()
    assert result == snapshot("expected value")
```

First run with `--inline-snapshot=fix` to create snapshots. They'll be updated in your test files.

### Testing Tools

```python
@agent.tool_plain
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny"

result = await run_with_display(agent, "What's the weather in SF?")
```

### Testing Error Handling

```python
with pytest.raises(ValueError, match="Tool failed"):
    await run_with_display(agent, "Use the failing tool")
```

## Configuration

Test config in `pyproject.toml`:

```toml
[tool.inline-snapshot]
format-command = "ruff format"

[tool.ruff]
line-length = 120
target-version = "py310"
```

## Notes

- All tests use async/await since `run_with_display` is async
- `pytestmark = pytest.mark.anyio` enables async test support
- TestModel provides deterministic responses for testing
- Snapshots commit with the code - they're part of the test