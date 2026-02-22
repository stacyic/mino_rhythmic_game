"""Main menu scene."""

import curses
from typing import Optional

from .base import Scene
from ..core.input_handler import KeyEvent, InputHandler
from ..ui.components import Menu
from ..ui.ascii_art import AsciiArt
from ..ui.renderer import Renderer


class MenuScene(Scene):
    """Main menu scene."""

    MENU_ITEMS = [
        "Play",
        "Create Beatmap",
        "Calibration",
        "Quit"
    ]

    def __init__(self, engine):
        super().__init__(engine)
        self._menu = Menu(self.MENU_ITEMS, title="")

    def enter(self) -> None:
        """Reset menu state on enter."""
        self._menu.selected_index = 0

    def exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self) -> None:
        """Render the main menu."""
        r = self.renderer
        center_y = r.height // 2 - 8

        # Draw title
        title = AsciiArt.TITLE
        title_y = max(1, center_y - title.height)
        for i, line in enumerate(title.lines):
            r.draw_text(
                title_y + i, 0, line,
                color_pair=Renderer.COLOR_TITLE,
                bold=True,
                center=True
            )

        # Draw bunny mascot
        bunny = AsciiArt.BUNNY
        bunny_y = title_y + title.height + 1
        for i, line in enumerate(bunny.lines):
            r.draw_text(bunny_y + i, 0, line, center=True)

        # Draw menu
        menu_y = bunny_y + bunny.height + 2
        self._menu.render(r, menu_y)

        # Draw instructions
        r.draw_text(
            r.height - 2, 0,
            "Use UP/DOWN to select, ENTER to confirm",
            center=True
        )

    def handle_input(self, key_event: Optional[KeyEvent]) -> None:
        """Handle menu navigation."""
        if key_event is None:
            return

        key = key_event.key

        if key == curses.KEY_UP:
            self._menu.move_up()
        elif key == curses.KEY_DOWN:
            self._menu.move_down()
        elif key == InputHandler.KEY_ENTER or key == InputHandler.KEY_SPACE:
            self._select_item()
        elif self.engine.input.is_quit_key(key):
            self.engine.quit()

    def _select_item(self) -> None:
        """Handle menu item selection."""
        selected = self._menu.get_selected()

        if selected == "Play":
            from .song_select import SongSelectScene
            self.engine.set_scene(SongSelectScene(self.engine, mode="play"))

        elif selected == "Create Beatmap":
            from .song_select import SongSelectScene
            self.engine.set_scene(SongSelectScene(self.engine, mode="create"))

        elif selected == "Calibration":
            from .calibration import CalibrationScene
            self.engine.set_scene(CalibrationScene(self.engine))

        elif selected == "Quit":
            self.engine.quit()
