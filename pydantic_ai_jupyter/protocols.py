from typing import Protocol, runtime_checkable


class HTMLRepresentable(Protocol):
    """Objects with a `to_html` method are displayable with ViewModels."""

    def to_html(self) -> str: ...


class MarkdownRepresentable(Protocol):
    """Objects with a `to_markdown` method are displayable with ViewModels."""

    def to_markdown(self) -> str: ...


@runtime_checkable
class Displayable(Protocol):
    def display(self) -> None: ...

    def update(self) -> None: ...

    def _repr_mimebundle_(self, include=None, exclude=None): ...


@runtime_checkable
class SupportsRender(Protocol):
    def render(self) -> str: ...
