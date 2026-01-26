"""Live-updating Markdown display for Jupyter notebooks."""

from __future__ import annotations

from pydantic import Field

from .decorators import markdown
from .models import View


@markdown
class Markdown(View):
    """A live-updating Markdown display for Jupyter notebooks.

    This class manages its own display_id internally and provides
    methods to append content and update the display in place.

    Example:
        md = Markdown("# Hello")
        md.display()
        md.append(" World!")  # Updates in place
    """

    content: str = Field(default="", description="The content of the Markdown display.")

    def render(self) -> str:
        return self.content

    def append(self, text: str) -> None:
        """Append text and update the display."""
        self.content += text
        self.update()
