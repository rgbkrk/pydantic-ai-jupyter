"""Live-updating Markdown display for Jupyter notebooks."""

from __future__ import annotations

import uuid

from IPython.display import Markdown as IPyMarkdown
from IPython.display import display
from .views import AutoView


class Markdown(AutoView):
    """A live-updating Markdown display for Jupyter notebooks.

    This class manages its own display_id internally and provides
    methods to append content and update the display in place.

    Example:
        md = Markdown("# Hello")
        md.display()
        md.append(" World!")  # Updates in place
    """

    def __init__(self, content: str = ""):
        super().__init__()
        self.content = content

    def _display_content_(self) -> str:
        return IPyMarkdown(self.content)

    def append(self, text: str) -> None:
        """Append text and update the display."""
        self.content += text
        self.update()

    def __repr__(self) -> str:
        preview = self.content[:100] + "..." if len(self.content) > 100 else self.content
        return f"Markdown({preview!r})"
