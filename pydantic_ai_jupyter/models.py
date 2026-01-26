"""
This module provides a framework for creating dynamic, interactive displays in Jupyter notebooks
and potentially other environments that support HTML rendering. It is designed to facilitate the
creation of rich, live-updating visualizations for data models, leveraging the capabilities of
IPython's display system.

Key Components:

- View: An abstract base class that serves as the foundation for creating view models. These
  view models are designed to encapsulate data and logic for rendering visual representations of
  that data in environments that support HTML, such as Jupyter notebooks. ViewModel provides
  mechanisms for displaying and updating these visual representations dynamically, enhancing
  interactivity and user engagement.

- AutoView: A concrete implementation of ViewModel that automatically updates its display
  whenever its attributes change. This is particularly useful for creating reactive interfaces
  where changes to the underlying data model should be immediately reflected in the display
  without requiring explicit calls to update the view.

Usage:

The module is intended to be used in environments that support HTML rendering and IPython's
display capabilities. Users can extend the ViewModel class to create custom view models tailored
to their specific visualization needs, implementing the `render` method to define how data should
be represented visually. AutoViewModel can be used for more dynamic scenarios where the display
should react to changes in the view model's state automatically.

Example:

Below is a simplified example of how to create a custom ViewModel for displaying a message:

    class MessageViewModel(ViewModel):
        message: str

        def render(self) -> str:
            return f"<h1>{self.message}</h1>"

    msg_view = MessageViewModel(message="Hello, World!")
    msg_view.display()

This example creates a simple view model for displaying a message in a heading element. The
`render` method returns the HTML representation of the message, which is then displayed in the
notebook.

Note:

This module requires an environment that supports the IPython display system and HTML rendering,
such as Jupyter notebooks. It is not intended for use in non-interactive Python scripts or
environments that do not support these capabilities.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Union

from IPython.display import display
from pydantic import BaseModel, Field

from .decorators import auto_update, renderable
from .protocols import HTMLRepresentable, MarkdownRepresentable


@renderable
class View(ABC, BaseModel):
    """
    An abstract base class for view models designed for displaying objects
    within Jupyter notebooks or other environments that support HTML rendering.

    This class provides a structure for creating and updating displays with
    dynamic content, leveraging HTML rendering for rich display capabilities.

    Attributes:
        display_id (str): A unique identifier for the display instance, used to
                          manage updates to the display in a notebook environment.

    Methods:
        display(): Displays the current object in the notebook. If the object is
                   already displayed, this method updates the existing display.
        update(): Updates the existing display with the current state of the object.
        render(): An abstract method that subclasses must implement, returning the
                  content to be displayed as either a string of HTML or an object
                  that implements the HTMLRepresentable protocol.
    """

    display_id: str = Field(default_factory=lambda: str(uuid.uuid4()), exclude=True)

    def display(self) -> None:
        """
        Display or the object in a Jupyter notebook or similar environment.

        This method leverages the display_id to manage the lifecycle of the display,
        allowing for updates to an existing display without creating a new one.
        """
        display(self, display_id=self.display_id)

    def update(self) -> None:
        """
        Update the display with the current state of the object.

        This method is intended to be called after modifications to the object
        to refresh the display in the notebook environment.
        """
        display(self, update=True, display_id=self.display_id)

    @abstractmethod
    def render(self) -> Union[str, HTMLRepresentable, MarkdownRepresentable]:
        """
        Render the object for display.

        This is an abstract method that subclasses must implement to define how
        the object is rendered for display. The method must return either a string
        of HTML or an object that implements the HTMLRepresentable protocol.

        Returns:
            Union[str, HTMLRepresentable]: The content to be displayed, either
                                           directly as HTML or through an object
                                           that can render itself as HTML.
        """
        ...


@auto_update
class AutoUpdate(View):
    """
    An extension of ViewModel that automatically updates its display whenever any of its
    attributes change. This class is designed to facilitate the creation of reactive
    interfaces in Jupyter notebooks or similar environments.

    AutoViewModel leverages the Pydantic BaseModel for attribute validation and management.
    Changes to attributes are detected, and the display is updated automatically to reflect
    these changes without requiring explicit calls to the `update` method.

    Usage:
    Extend AutoViewModel to create custom view models with automatic display updating. This
    is ideal for scenarios where the state of the view model is dynamic and changes in response
    to user interaction or other events.

    Example:
        class CounterViewModel(AutoViewModel):
            count: int = 0

            def render(self) -> str:
                return f"Current count: {self.count}"

        counter = CounterViewModel()
        counter.display()  # Initial display
        counter.count += 1  # Display automatically updates

    Note:
    AutoViewModel only triggers updates for direct attribute changes. Nested changes, such as
    modifications to items within a list attribute, may not automatically trigger an update.
    """
