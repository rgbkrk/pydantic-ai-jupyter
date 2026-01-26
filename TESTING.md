# Testing Guide

Quick reference for testing pydantic-ai-jupyter with `TestModel` and inline snapshots.

## Overview

Tests use:
- **pytest** with async support (`pytest.mark.anyio`)
- **TestModel** from pydantic-ai for deterministic agent behavior
- **inline-snapshot** for capturing expected values
- **dirty-equals** for flexible assertions (not yet heavily used)

## Quick Start

```bash
# Run all tests
uv run pytest tests/ -v

# Update snapshots after changes
uv run pytest tests/ --inline-snapshot=fix

# Run specific test file
uv run pytest tests/test_display.py -v

# Watch mode (requires pytest-watch)
uv run ptw tests/
```

## Test Files

- `tests/test_display.py` - Core `run_in_jupyter` functionality with TestModel
- `tests/test_views.py` - View components (ToolCallView, ErrorView, StreamingToolCallView, etc.)
- `tests/test_markdown.py` - Markdown rendering and accumulation
- `tests/README.md` - Detailed patterns and examples

## Example Test Pattern

```python
from __future__ import annotations as _annotations

import pytest
from inline_snapshot import snapshot
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from pydantic_ai_jupyter.display import run_in_jupyter

pytestmark = pytest.mark.anyio


async def test_agent_with_tool() -> None:
    """Test agent with a custom tool."""
    model = TestModel()
    agent = Agent(model)

    @agent.tool_plain
    def calculate(x: int, y: int) -> int:
        """Add two numbers."""
        return x + y

    result = await run_in_jupyter(agent, "What is 2 + 2?")

    assert result is not None
    # Snapshot will be auto-generated on first run with --inline-snapshot=fix
    assert result.output == snapshot("expected output here")
```

## Key Points

1. **TestModel is deterministic** - Same input = same output, perfect for testing
2. **Snapshots live in test files** - No separate snapshot directories
3. **Async required** - All tests use `async def` since display runner is async
4. **Type hints everywhere** - Follow Pydantic AI style guide
5. **No test classes** - Use module-level test functions

## Snapshot Workflow

```bash
# 1. Write test with snapshot() placeholder
assert result == snapshot("placeholder")

# 2. Run with --inline-snapshot=fix
uv run pytest tests/test_myfeature.py --inline-snapshot=fix

# 3. Snapshot gets written to test file
assert result == snapshot("actual value from test")

# 4. Commit test with snapshot
git add tests/test_myfeature.py
```

## Adding More Tests

```python
# Test error handling
with pytest.raises(ValueError, match="Expected error message"):
    await some_operation()

# Test view rendering
view = ToolCallView(tool_name="test", args={"key": "value"})
html = view.render()
assert "test" in html
assert "key" in html

# Test accumulation (streaming)
md = Markdown()
md.append("Hello")
md.append(" World")
assert md.content == snapshot("Hello World")
```

## Next Steps

Consider adding tests for:
- Different event types in `run_in_jupyter`
- Edge cases in views (very long content, special characters)
- Different display modes (debug=True vs debug=False)
- Message history handling
- Custom model settings
- Multiple tool calls in sequence
- Streaming vs non-streaming behavior

## Configuration

See `pyproject.toml` for:
- Test dependencies
- Ruff formatting integration
- Inline-snapshot configuration

## Resources

- [Pydantic AI Testing Guide](https://ai.pydantic.dev/testing/)
- [inline-snapshot docs](https://github.com/15r10nk/inline-snapshot)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)