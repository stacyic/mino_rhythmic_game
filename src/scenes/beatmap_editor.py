"""Beatmap editor/creation scene."""

import curses
from typing import Optional
from pathlib import Path

from .base import Scene
from ..core.input_handler import KeyEvent, InputHandler
from ..ui.renderer import Renderer
from ..ui.components import ProgressBar
from ..models.beatmap import Beatmap, get_beatmap_for_song
from ..utils.file_scanner import SongInfo
from ..utils.quantize import quantize_beats


class BeatmapEditorScene(Scene):
    """Scene for creating/editing beatmaps by tapping along to music."""

    DEFAULT_BPM = 120.0

    def __init__(self, engine, song: SongInfo):
        super().__init__(engine)
        self._song = song
        self._base_dir = Path(__file__).parent.parent.parent
        self._state = "setup"  # setup, recording, review, saved
        self._bpm = self.DEFAULT_BPM
        self._bpm_input = ""  # Start empty, show default as placeholder
        self._raw_beats: list[float] = []
        self._quantized_beats: list[float] = []
        self._progress_bar = ProgressBar(width=50)
        self._existing_beatmap: Optional[Beatmap] = None

    def enter(self) -> None:
        """Initialize editor."""
        self._state = "setup"
        self._raw_beats = []
        self._quantized_beats = []

        # Check for existing beatmap
        data_dir = str(self._base_dir / "data")
        self._existing_beatmap = get_beatmap_for_song(self._song.name, data_dir)

        if self._existing_beatmap:
            self._bpm = self._existing_beatmap.bpm

        # Reset input field (will use _bpm as default if empty)
        self._bpm_input = ""

        # Load the song
        self.engine.audio.load(self._song.file_path)

    def exit(self) -> None:
        """Cleanup."""
        self.engine.audio.stop()

    def update(self, dt: float) -> None:
        """Update progress bar during recording."""
        if self._state == "recording":
            duration = self.engine.audio.get_duration_ms()
            if duration > 0:
                position = self.engine.audio.get_position_ms()
                self._progress_bar.set_progress(position / duration)

            # Check if song finished
            if self.engine.audio.is_finished():
                self._finish_recording()

    def render(self) -> None:
        """Render based on state."""
        r = self.renderer

        if self._state == "setup":
            self._render_setup(r)
        elif self._state == "recording":
            self._render_recording(r)
        elif self._state == "review":
            self._render_review(r)
        elif self._state == "saved":
            self._render_saved(r)

    def _render_setup(self, r: Renderer) -> None:
        """Render setup screen."""
        center_y = r.height // 2 - 6

        r.draw_text(
            center_y, 0, "BEATMAP EDITOR",
            color_pair=Renderer.COLOR_TITLE,
            bold=True,
            center=True
        )

        r.draw_text(center_y + 2, 0, f"Song: {self._song.name}", center=True)

        if self._existing_beatmap:
            r.draw_text(
                center_y + 3, 0,
                f"(Existing beatmap with {len(self._existing_beatmap.beats)} beats)",
                center=True
            )

        r.draw_text(center_y + 5, 0, "Enter BPM for quantization:", center=True)

        # Show input field with placeholder if empty
        if self._bpm_input:
            display_bpm = self._bpm_input
        else:
            display_bpm = str(int(self._bpm))

        r.draw_text(
            center_y + 6, 0,
            f"BPM: [ {display_bpm}_ ]",
            color_pair=Renderer.COLOR_HIGHLIGHT,
            center=True
        )

        if not self._bpm_input:
            r.draw_text(center_y + 7, 0, "(default - type to change, C to clear)", center=True)

        r.draw_text(center_y + 9, 0, "Instructions:", center=True)
        r.draw_text(center_y + 10, 0, "- Type digits to set BPM (C to clear)", center=True)
        r.draw_text(center_y + 11, 0, "- The song will play, tap ANY KEY for beats", center=True)
        r.draw_text(center_y + 12, 0, "- Beats within 50ms of BPM grid will snap", center=True)

        r.draw_text(
            r.height - 4, 0,
            "Press ENTER to start recording",
            color_pair=Renderer.COLOR_SUCCESS,
            center=True
        )
        r.draw_text(r.height - 2, 0, "Press ESC to go back", center=True)

    def _render_recording(self, r: Renderer) -> None:
        """Render recording screen."""
        center_y = r.height // 2 - 4

        r.draw_text(
            center_y, 0, "RECORDING",
            color_pair=Renderer.COLOR_ERROR,
            bold=True,
            center=True
        )

        r.draw_text(center_y + 2, 0, f"Song: {self._song.name}", center=True)
        r.draw_text(center_y + 3, 0, f"Beats recorded: {len(self._raw_beats)}", center=True)

        # Progress bar
        self._progress_bar.render(r, center_y + 5, center=True, label="Progress:")

        # Current time
        pos = self.engine.audio.get_position_ms()
        dur = self.engine.audio.get_duration_ms()
        time_str = f"{pos/1000:.1f}s / {dur/1000:.1f}s"
        r.draw_text(center_y + 7, 0, time_str, center=True)

        r.draw_text(
            r.height - 2, 0,
            "TAP any key to record beats | ESC to cancel",
            center=True
        )

    def _render_review(self, r: Renderer) -> None:
        """Render review screen."""
        center_y = r.height // 2 - 5

        r.draw_text(
            center_y, 0, "RECORDING COMPLETE",
            color_pair=Renderer.COLOR_SUCCESS,
            bold=True,
            center=True
        )

        r.draw_text(center_y + 2, 0, f"Song: {self._song.name}", center=True)
        r.draw_text(center_y + 3, 0, f"BPM: {self._bpm}", center=True)
        r.draw_text(center_y + 4, 0, f"Raw beats: {len(self._raw_beats)}", center=True)
        r.draw_text(
            center_y + 5, 0,
            f"After quantization: {len(self._quantized_beats)}",
            center=True
        )

        # Show first few beats
        if self._quantized_beats:
            preview = self._quantized_beats[:5]
            preview_str = ", ".join([f"{b:.0f}ms" for b in preview])
            if len(self._quantized_beats) > 5:
                preview_str += "..."
            r.draw_text(center_y + 7, 0, f"Preview: {preview_str}", center=True)

        r.draw_text(
            r.height - 4, 0,
            "Press ENTER to save | R to re-record",
            color_pair=Renderer.COLOR_SUCCESS,
            center=True
        )
        r.draw_text(r.height - 2, 0, "Press ESC to discard and go back", center=True)

    def _render_saved(self, r: Renderer) -> None:
        """Render saved confirmation."""
        center_y = r.height // 2 - 2

        r.draw_text(
            center_y, 0, "BEATMAP SAVED!",
            color_pair=Renderer.COLOR_SUCCESS,
            bold=True,
            center=True
        )

        r.draw_text(center_y + 2, 0, f"{len(self._quantized_beats)} beats saved", center=True)
        r.draw_text(r.height - 2, 0, "Press any key to continue", center=True)

    def handle_input(self, key_event: Optional[KeyEvent]) -> None:
        """Handle input based on state."""
        if key_event is None:
            return

        key = key_event.key

        if self._state == "setup":
            self._handle_setup_input(key, key_event.char)
        elif self._state == "recording":
            self._handle_recording_input(key, key_event.timestamp_ms)
        elif self._state == "review":
            self._handle_review_input(key)
        elif self._state == "saved":
            self._go_back()

    def _handle_setup_input(self, key: int, char: str) -> None:
        """Handle setup screen input."""
        # ESC to go back (but not 'q' since we need keyboard for input)
        if key == InputHandler.KEY_ESCAPE:
            self._go_back()
        elif key == InputHandler.KEY_ENTER:
            self._start_recording()
        elif key == InputHandler.KEY_BACKSPACE or key == 8:  # 8 is backspace on some terminals
            if self._bpm_input:
                self._bpm_input = self._bpm_input[:-1]
        elif char.lower() == 'c':
            # Clear the input
            self._bpm_input = ""
        elif char.isdigit():
            # Add digit to BPM input (max 3 digits)
            if len(self._bpm_input) < 3:
                self._bpm_input += char
            # Update BPM value
            if self._bpm_input:
                try:
                    self._bpm = float(self._bpm_input)
                except ValueError:
                    pass

    def _handle_recording_input(self, key: int, timestamp_ms: float) -> None:
        """Handle recording input."""
        if self.engine.input.is_quit_key(key):
            self.engine.audio.stop()
            self._state = "setup"
        elif self.engine.input.is_any_gameplay_key(key):
            # Record the beat at current audio position
            audio_pos = self.engine.audio.get_position_ms()
            self._raw_beats.append(audio_pos)

    def _handle_review_input(self, key: int) -> None:
        """Handle review screen input."""
        if self.engine.input.is_quit_key(key):
            self._go_back()
        elif key == InputHandler.KEY_ENTER:
            self._save_beatmap()
        elif key == ord('r') or key == ord('R'):
            self._state = "setup"
            self._raw_beats = []
            self._quantized_beats = []

    def _start_recording(self) -> None:
        """Start recording beats."""
        if not self._bpm_input:
            self._bpm = self.DEFAULT_BPM
        else:
            try:
                self._bpm = float(self._bpm_input)
                if self._bpm < 30 or self._bpm > 300:
                    self._bpm = self.DEFAULT_BPM
            except ValueError:
                self._bpm = self.DEFAULT_BPM

        self._raw_beats = []
        self._state = "recording"
        self.engine.input.reset_timer()
        self.engine.audio.play()

    def _finish_recording(self) -> None:
        """Finish recording and quantize beats."""
        self.engine.audio.stop()

        # Quantize beats
        self._quantized_beats = quantize_beats(
            self._raw_beats,
            self._bpm,
            snap_threshold_ms=50.0
        )

        self._state = "review"

    def _save_beatmap(self) -> None:
        """Save the beatmap to file."""
        beatmap = Beatmap(
            song_file=Path(self._song.file_path).name,
            bpm=self._bpm,
            beats=self._quantized_beats,
            name=self._song.name
        )

        data_dir = str(self._base_dir / "data")
        beatmap.save(data_dir)

        self._state = "saved"

    def _go_back(self) -> None:
        """Return to song select."""
        from .song_select import SongSelectScene
        self.engine.set_scene(SongSelectScene(self.engine, mode="create"))
