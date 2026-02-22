"""Reusable UI components."""

from typing import Optional
from .renderer import Renderer


class Menu:
    """A selectable menu component."""

    def __init__(
        self,
        items: list[str],
        title: str = "",
        selected_index: int = 0
    ):
        self.items = items
        self.title = title
        self.selected_index = selected_index

    def move_up(self) -> None:
        """Move selection up."""
        if self.selected_index > 0:
            self.selected_index -= 1

    def move_down(self) -> None:
        """Move selection down."""
        if self.selected_index < len(self.items) - 1:
            self.selected_index += 1

    def get_selected(self) -> str:
        """Get the currently selected item."""
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return ""

    def render(
        self,
        renderer: Renderer,
        y: int,
        x: Optional[int] = None,
        center: bool = True
    ) -> int:
        """
        Render the menu.

        Args:
            renderer: The renderer to use
            y: Starting row
            x: Starting column (ignored if center=True)
            center: Whether to center the menu

        Returns:
            Number of rows used
        """
        current_y = y

        # Draw title
        if self.title:
            renderer.draw_text(
                current_y, 0, self.title,
                color_pair=Renderer.COLOR_TITLE,
                bold=True,
                center=center
            )
            current_y += 2

        # Draw items
        for i, item in enumerate(self.items):
            if i == self.selected_index:
                display = f"> {item} <"
                renderer.draw_text(
                    current_y, 0, display,
                    color_pair=Renderer.COLOR_HIGHLIGHT,
                    bold=True,
                    center=center
                )
            else:
                display = f"  {item}  "
                renderer.draw_text(current_y, 0, display, center=center)
            current_y += 1

        return current_y - y


class ProgressBar:
    """A horizontal progress bar."""

    def __init__(
        self,
        width: int = 40,
        fill_char: str = '#',
        empty_char: str = '-'
    ):
        self.width = width
        self.fill_char = fill_char
        self.empty_char = empty_char
        self.progress = 0.0  # 0.0 to 1.0

    def set_progress(self, value: float) -> None:
        """Set progress value (0.0 to 1.0)."""
        self.progress = max(0.0, min(1.0, value))

    def render(
        self,
        renderer: Renderer,
        y: int,
        x: Optional[int] = None,
        center: bool = True,
        label: str = ""
    ) -> None:
        """Render the progress bar."""
        filled = int(self.width * self.progress)
        empty = self.width - filled

        bar = f"[{self.fill_char * filled}{self.empty_char * empty}]"

        if label:
            bar = f"{label} {bar}"

        renderer.draw_text(y, x or 0, bar, center=center)


class MessageBox:
    """A message display box."""

    def __init__(self, message: str = "", title: str = ""):
        self.message = message
        self.title = title
        self.lines: list[str] = []
        if message:
            self.set_message(message)

    def set_message(self, message: str) -> None:
        """Set the message, splitting into lines."""
        self.message = message
        self.lines = message.split('\n')

    def render(
        self,
        renderer: Renderer,
        y: int,
        center: bool = True
    ) -> int:
        """
        Render the message box.

        Returns:
            Number of rows used
        """
        current_y = y

        if self.title:
            renderer.draw_text(
                current_y, 0, self.title,
                color_pair=Renderer.COLOR_TITLE,
                bold=True,
                center=center
            )
            current_y += 1

        for line in self.lines:
            renderer.draw_text(current_y, 0, line, center=center)
            current_y += 1

        return current_y - y
