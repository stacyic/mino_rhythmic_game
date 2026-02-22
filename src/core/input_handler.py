"""Non-blocking keyboard input handling using curses."""

import curses
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class KeyEvent:
    """Represents a key press event with timing information."""
    key: int
    char: str
    timestamp_ms: float


class InputHandler:
    """Handles non-blocking keyboard input with precise timestamps."""

    # Special key constants
    KEY_ESCAPE = 27
    KEY_ENTER = 10
    KEY_SPACE = 32
    KEY_BACKSPACE = 127
    KEY_UP = curses.KEY_UP
    KEY_DOWN = curses.KEY_DOWN
    KEY_LEFT = curses.KEY_LEFT
    KEY_RIGHT = curses.KEY_RIGHT

    def __init__(self, stdscr: curses.window):
        self._stdscr = stdscr
        self._start_time = time.perf_counter()

        # Configure for non-blocking input
        stdscr.nodelay(True)
        stdscr.keypad(True)
        curses.cbreak()
        curses.noecho()

    def reset_timer(self) -> None:
        """Reset the input timestamp timer."""
        self._start_time = time.perf_counter()

    def get_time_ms(self) -> float:
        """Get current time in milliseconds since timer start."""
        return (time.perf_counter() - self._start_time) * 1000

    def poll(self) -> Optional[KeyEvent]:
        """
        Poll for a key press (non-blocking).

        Returns:
            KeyEvent if a key was pressed, None otherwise
        """
        try:
            key = self._stdscr.getch()
            if key == -1:
                return None

            timestamp = self.get_time_ms()
            char = chr(key) if 32 <= key <= 126 else ''

            return KeyEvent(key=key, char=char, timestamp_ms=timestamp)
        except Exception:
            return None

    def wait_for_key(self, timeout_ms: Optional[float] = None) -> Optional[KeyEvent]:
        """
        Wait for a key press (blocking with optional timeout).

        Args:
            timeout_ms: Maximum time to wait, None for indefinite

        Returns:
            KeyEvent if a key was pressed, None if timeout
        """
        start = time.perf_counter()

        while True:
            event = self.poll()
            if event is not None:
                return event

            if timeout_ms is not None:
                elapsed = (time.perf_counter() - start) * 1000
                if elapsed >= timeout_ms:
                    return None

            time.sleep(0.001)  # 1ms sleep to avoid busy waiting

    def is_quit_key(self, key: int) -> bool:
        """Check if the key is a quit key (ESC or 'q')."""
        return key == self.KEY_ESCAPE or key == ord('q')

    def is_confirm_key(self, key: int) -> bool:
        """Check if the key is a confirm key (Enter or Space)."""
        return key == self.KEY_ENTER or key == self.KEY_SPACE

    def is_any_gameplay_key(self, key: int) -> bool:
        """Check if the key is valid for gameplay (any printable key or space)."""
        return 32 <= key <= 126 or key == self.KEY_SPACE

    def flush(self) -> None:
        """Flush any pending input."""
        curses.flushinp()
