from __future__ import annotations as _annotations

import pytest
from inline_snapshot import snapshot

from pydantic_ai_jupyter.markdown import Markdown

pytestmark = pytest.mark.anyio


async def test_markdown_basic_instantiation() -> None:
    """Markdown should initialize with content."""
    md = Markdown(content="# Hello World")

    assert md.content == snapshot("# Hello World")


async def test_markdown_render() -> None:
    """Markdown should render its content."""
    md = Markdown(content="## Test\n\nThis is **bold** text.")

    rendered = md.render()
    assert rendered == snapshot("## Test\n\nThis is **bold** text.")


async def test_markdown_append() -> None:
    """Markdown should accumulate content via append."""
    md = Markdown(content="# Title")

    md.append("\n\n")
    md.append("First paragraph.")
    md.append(" More text.")

    assert md.content == snapshot("# Title\n\nFirst paragraph. More text.")


async def test_markdown_empty_default() -> None:
    """Markdown should default to empty content."""
    md = Markdown()

    assert md.content == ""


async def test_markdown_multiline_content() -> None:
    """Markdown should handle multiline content."""
    content = """# Heading

- Item 1
- Item 2
- Item 3

> Quote text
"""
    md = Markdown(content=content)

    assert md.render() == snapshot(
        """# Heading

- Item 1
- Item 2
- Item 3

> Quote text
"""
    )


async def test_markdown_streaming_simulation() -> None:
    """Markdown should accumulate streaming text."""
    md = Markdown()

    # Simulate streaming words
    words = ["The", " quick", " brown", " fox"]
    for word in words:
        md.append(word)

    assert md.content == snapshot("The quick brown fox")
