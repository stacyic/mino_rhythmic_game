"""Terminal rendering abstraction over curses."""

import curses
from typing import Optional


class Renderer:
    """Abstraction layer for terminal rendering."""

    # Color pair IDs
    COLOR_DEFAULT = 0
    COLOR_TITLE = 1
    COLOR_HIGHLIGHT = 2
    COLOR_SUCCESS = 3
    COLOR_ERROR = 4
    COLOR_CARROT = 5
    COLOR_BUNNY = 6
    COLOR_LANE = 7

    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr
        self._init_colors()

    def _init_colors(self) -> None:
        """Initialize color pairs if terminal supports colors."""
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()

            # Define color pairs
            curses.init_pair(self.COLOR_TITLE, curses.COLOR_CYAN, -1)
            curses.init_pair(self.COLOR_HIGHLIGHT, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(self.COLOR_SUCCESS, curses.COLOR_GREEN, -1)
            curses.init_pair(self.COLOR_ERROR, curses.COLOR_RED, -1)
            curses.init_pair(self.COLOR_CARROT, curses.COLOR_YELLOW, -1)
            curses.init_pair(self.COLOR_BUNNY, curses.COLOR_WHITE, -1)
            curses.init_pair(self.COLOR_LANE, curses.COLOR_BLUE, -1)

    @property
    def height(self) -> int:
        """Get terminal height."""
        return self.stdscr.getmaxyx()[0]

    @property
    def width(self) -> int:
        """Get terminal width."""
        return self.stdscr.getmaxyx()[1]

    def clear(self) -> None:
        """Clear the screen."""
        self.stdscr.clear()

    def refresh(self) -> None:
        """Refresh the screen."""
        self.stdscr.refresh()

    def draw_text(
        self,
        y: int,
        x: int,
        text: str,
        color_pair: int = 0,
        bold: bool = False,
        center: bool = False
    ) -> None:
        """
        Draw text at the specified position.

        Args:
            y: Row position
            x: Column position (ignored if center=True)
            text: Text to draw
            color_pair: Color pair ID
            bold: Whether to use bold
            center: Whether to center horizontally
        """
        if y < 0 or y >= self.height:
            return

        if center:
            x = (self.width - len(text)) // 2

        if x < 0:
            x = 0

        # Truncate text to fit
        max_len = self.width - x - 1
        if max_len <= 0:
            return
        text = text[:max_len]

        try:
            attrs = curses.color_pair(color_pair)
            if bold:
                attrs |= curses.A_BOLD
            self.stdscr.addstr(y, x, text, attrs)
        except curses.error:
            pass

    def draw_box(
        self,
        y: int,
        x: int,
        height: int,
        width: int,
        color_pair: int = 0
    ) -> None:
        """Draw a box outline."""
        try:
            attrs = curses.color_pair(color_pair)

            # Top and bottom
            self.stdscr.addstr(y, x, '+' + '-' * (width - 2) + '+', attrs)
            self.stdscr.addstr(y + height - 1, x, '+' + '-' * (width - 2) + '+', attrs)

            # Sides
            for row in range(1, height - 1):
                self.stdscr.addstr(y + row, x, '|', attrs)
                self.stdscr.addstr(y + row, x + width - 1, '|', attrs)
        except curses.error:
            pass

    def draw_horizontal_line(
        self,
        y: int,
        x: int,
        length: int,
        char: str = '-',
        color_pair: int = 0
    ) -> None:
        """Draw a horizontal line."""
        if y < 0 or y >= self.height:
            return
        line = char * length
        self.draw_text(y, x, line, color_pair)

    def draw_vertical_line(
        self,
        y: int,
        x: int,
        length: int,
        char: str = '|',
        color_pair: int = 0
    ) -> None:
        """Draw a vertical line."""
        if x < 0 or x >= self.width:
            return
        try:
            attrs = curses.color_pair(color_pair)
            for row in range(length):
                if 0 <= y + row < self.height:
                    self.stdscr.addstr(y + row, x, char, attrs)
        except curses.error:
            pass

    def fill_rect(
        self,
        y: int,
        x: int,
        height: int,
        width: int,
        char: str = ' ',
        color_pair: int = 0
    ) -> None:
        """Fill a rectangular area with a character."""
        try:
            attrs = curses.color_pair(color_pair)
            line = char * width
            for row in range(height):
                if 0 <= y + row < self.height:
                    self.stdscr.addstr(y + row, x, line[:self.width - x - 1], attrs)
        except curses.error:
            pass
