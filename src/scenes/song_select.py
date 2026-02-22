"""Song selection scene."""

import curses
from typing import Optional
from pathlib import Path

from .base import Scene
from ..core.input_handler import KeyEvent, InputHandler
from ..ui.components import Menu
from ..ui.renderer import Renderer
from ..utils.file_scanner import scan_for_songs, SongInfo


class SongSelectScene(Scene):
    """Song selection scene for play or beatmap creation."""

    def __init__(self, engine, mode: str = "play"):
        """
        Args:
            engine: Game engine
            mode: "play" or "create"
        """
        super().__init__(engine)
        self._mode = mode
        self._songs: list[SongInfo] = []
        self._menu: Optional[Menu] = None
        self._base_dir = Path(__file__).parent.parent.parent
        self._message = ""

    def enter(self) -> None:
        """Scan for songs and build menu."""
        self._scan_songs()
        self._message = ""

    def exit(self) -> None:
        pass

    def _scan_songs(self) -> None:
        """Scan directory for songs."""
        song_dir = str(self._base_dir)
        data_dir = str(self._base_dir / "data")

        self._songs = scan_for_songs(song_dir, data_dir)

        if self._songs:
            # Build menu items
            items = []
            for song in self._songs:
                status = ""
                if self._mode == "play":
                    status = " [HAS BEATMAP]" if song.has_beatmap else " [NO BEATMAP]"
                elif self._mode == "create":
                    status = " [EDIT]" if song.has_beatmap else " [NEW]"
                items.append(f"{song.name}{status}")

            self._menu = Menu(items, title="")
        else:
            self._menu = None

    def update(self, dt: float) -> None:
        pass

    def render(self) -> None:
        """Render song selection."""
        r = self.renderer

        # Title
        title = "SELECT SONG TO PLAY" if self._mode == "play" else "SELECT SONG FOR BEATMAP"
        r.draw_text(
            2, 0, title,
            color_pair=Renderer.COLOR_TITLE,
            bold=True,
            center=True
        )

        if self._menu is None:
            r.draw_text(
                r.height // 2, 0,
                "No songs found! Add .mp3 files to the game folder.",
                color_pair=Renderer.COLOR_ERROR,
                center=True
            )
        else:
            self._menu.render(r, 5)

            # Show message if any
            if self._message:
                r.draw_text(
                    r.height - 4, 0,
                    self._message,
                    color_pair=Renderer.COLOR_ERROR,
                    center=True
                )

        r.draw_text(
            r.height - 2, 0,
            "UP/DOWN to select, ENTER to confirm, ESC to go back",
            center=True
        )

    def handle_input(self, key_event: Optional[KeyEvent]) -> None:
        """Handle song selection input."""
        if key_event is None:
            return

        key = key_event.key

        if self.engine.input.is_quit_key(key):
            self._go_back()
            return

        if self._menu is None:
            return

        if key == curses.KEY_UP:
            self._menu.move_up()
        elif key == curses.KEY_DOWN:
            self._menu.move_down()
        elif key == InputHandler.KEY_ENTER:
            self._select_song()

    def _select_song(self) -> None:
        """Handle song selection."""
        if self._menu is None or not self._songs:
            return

        idx = self._menu.selected_index
        if idx < 0 or idx >= len(self._songs):
            return

        song = self._songs[idx]

        if self._mode == "play":
            if not song.has_beatmap:
                self._message = "This song has no beatmap! Create one first."
                return

            from .gameplay import GameplayScene
            self.engine.set_scene(GameplayScene(self.engine, song))

        elif self._mode == "create":
            from .beatmap_editor import BeatmapEditorScene
            self.engine.set_scene(BeatmapEditorScene(self.engine, song))

    def _go_back(self) -> None:
        """Return to main menu."""
        from .menu import MenuScene
        self.engine.set_scene(MenuScene(self.engine))
