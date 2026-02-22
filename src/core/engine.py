"""Game engine managing the main loop and scene transitions."""

import curses
import time
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from .audio import AudioManager, MetronomeGenerator
from .input_handler import InputHandler
from .timing import TimingManager

if TYPE_CHECKING:
    from ..scenes.base import Scene


class GameEngine:
    """Main game engine that manages scenes and the game loop."""

    TARGET_FPS = 60
    FRAME_TIME = 1.0 / TARGET_FPS

    def __init__(self, stdscr: curses.window, base_dir: Optional[str] = None):
        self.stdscr = stdscr
        self.running = False

        # Determine base directory for config/data
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Default to the directory containing main.py
            self.base_dir = Path(__file__).parent.parent.parent

        self.config_dir = str(self.base_dir / "config")
        self.data_dir = str(self.base_dir / "data")

        # Core systems
        self.audio = AudioManager()
        self.metronome = MetronomeGenerator()
        self.input = InputHandler(stdscr)
        self.timing = TimingManager(config_dir=self.config_dir)

        # Scene management
        self._current_scene: Optional['Scene'] = None
        self._next_scene: Optional['Scene'] = None
        self._should_quit = False

        # Frame timing
        self._last_frame_time = 0.0
        self._delta_time = 0.0

        # Screen dimensions
        self.height, self.width = stdscr.getmaxyx()

    def set_scene(self, scene: 'Scene') -> None:
        """
        Set the next scene to transition to.

        Args:
            scene: The scene to switch to
        """
        self._next_scene = scene

    def quit(self) -> None:
        """Signal the engine to quit."""
        self._should_quit = True

    def run(self, initial_scene: 'Scene') -> None:
        """
        Start the game loop with the initial scene.

        Args:
            initial_scene: The first scene to display
        """
        self.running = True
        self._current_scene = initial_scene
        self._current_scene.enter()

        self._last_frame_time = time.perf_counter()

        while self.running and not self._should_quit:
            self._process_frame()

        # Cleanup
        if self._current_scene:
            self._current_scene.exit()

        self.audio.stop()
        self.metronome.stop()

    def _process_frame(self) -> None:
        """Process a single frame."""
        frame_start = time.perf_counter()
        self._delta_time = frame_start - self._last_frame_time
        self._last_frame_time = frame_start

        # Handle scene transition
        if self._next_scene is not None:
            if self._current_scene:
                self._current_scene.exit()
            self._current_scene = self._next_scene
            self._next_scene = None
            self._current_scene.enter()
            self.input.flush()

        # Update screen dimensions (in case of resize)
        self.height, self.width = self.stdscr.getmaxyx()

        # Process input
        key_event = self.input.poll()
        if self._current_scene:
            self._current_scene.handle_input(key_event)

        # Update
        if self._current_scene:
            self._current_scene.update(self._delta_time)

        # Render
        try:
            self.stdscr.clear()
            if self._current_scene:
                self._current_scene.render()
            self.stdscr.refresh()
        except curses.error:
            pass  # Ignore curses errors (usually from small terminal)

        # Frame limiting
        frame_end = time.perf_counter()
        frame_duration = frame_end - frame_start
        sleep_time = self.FRAME_TIME - frame_duration

        if sleep_time > 0:
            time.sleep(sleep_time)

    @property
    def delta_time(self) -> float:
        """Get the time elapsed since the last frame in seconds."""
        return self._delta_time

    @property
    def fps(self) -> float:
        """Get the current FPS."""
        if self._delta_time > 0:
            return 1.0 / self._delta_time
        return 0.0
