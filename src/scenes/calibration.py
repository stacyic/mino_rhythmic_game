"""Calibration scene for timing offset using actual audio playback."""

from typing import Optional
from pathlib import Path

from .base import Scene
from ..core.input_handler import KeyEvent, InputHandler
from ..ui.renderer import Renderer
from ..ui.components import ProgressBar
from ..models.settings import Settings
from ..models.beatmap import Beatmap


class CalibrationScene(Scene):
    """Calibration scene using actual audio file playback.

    Uses calibration.mp3 to accurately measure the audio output
    latency of the system.
    """

    CALIBRATION_FILE = "calibration.mp3"
    CALIBRATION_BEATMAP = "calibration.beatmap.json"
    NUM_BEATS_TO_USE = 30  # Only use first N beats for calibration

    def __init__(self, engine):
        super().__init__(engine)
        self._state = "intro"  # intro, running, result
        self._tap_times: list[float] = []
        self._beat_times: list[float] = []
        self._beats_passed = 0
        self._calculated_offset = 0.0
        self._progress_bar = ProgressBar(width=40)
        self._last_tap_delta: Optional[float] = None
        self._bpm: float = 120.0
        self._beat_interval_ms: float = 500.0
        self._tap_feedback_timer = 0.0

    def enter(self) -> None:
        """Initialize calibration."""
        self._state = "intro"
        self._tap_times = []
        self._beat_times = []
        self._beats_passed = 0
        self._calculated_offset = 0.0
        self._last_tap_delta = None
        self._tap_feedback_timer = 0.0

        # Load calibration audio and beatmap
        base_dir = self.engine.base_dir
        calibration_audio = base_dir / self.CALIBRATION_FILE
        calibration_beatmap = base_dir / "data" / self.CALIBRATION_BEATMAP

        if calibration_audio.exists():
            self.engine.audio.load(str(calibration_audio))

        if calibration_beatmap.exists():
            beatmap = Beatmap.load(str(calibration_beatmap))
            if beatmap:
                # Only use first N beats
                self._beat_times = beatmap.beats[:self.NUM_BEATS_TO_USE]
                # Read BPM from beatmap
                self._bpm = beatmap.bpm
                self._beat_interval_ms = 60000.0 / self._bpm

        self.engine.input.flush()

    def exit(self) -> None:
        """Cleanup."""
        self.engine.audio.stop()

    def update(self, dt: float) -> None:
        """Update calibration state."""
        if self._state == "running":
            current_time = self.engine.audio.get_position_ms()

            # Count how many beats have passed
            self._beats_passed = 0
            for beat in self._beat_times:
                if current_time >= beat:
                    self._beats_passed += 1

            # Update progress
            if self._beat_times:
                last_beat_time = self._beat_times[-1]
                self._progress_bar.set_progress(current_time / (last_beat_time + 500))

            # Check if calibration is complete (past last beat + buffer)
            if self._beat_times and current_time > self._beat_times[-1] + 1000:
                self._finish_calibration()

        # Update tap feedback timer
        if self._tap_feedback_timer > 0:
            self._tap_feedback_timer -= dt

    def render(self) -> None:
        """Render calibration UI."""
        r = self.renderer

        if self._state == "intro":
            self._render_intro(r)
        elif self._state == "running":
            self._render_running(r)
        elif self._state == "result":
            self._render_result(r)

    def _render_intro(self, r: Renderer) -> None:
        """Render intro instructions."""
        center_y = r.height // 2 - 5

        r.draw_text(
            center_y, 0, "CALIBRATION",
            color_pair=Renderer.COLOR_TITLE,
            bold=True,
            center=True
        )

        r.draw_text(center_y + 2, 0, "You will hear a 120 BPM metronome.", center=True)
        r.draw_text(center_y + 3, 0, "Tap ANY KEY in time with each beat.", center=True)
        r.draw_text(center_y + 4, 0, f"Listen to {self.NUM_BEATS_TO_USE} beats.", center=True)
        r.draw_text(center_y + 6, 0, "This calibrates for your audio latency.", center=True)

        r.draw_text(
            center_y + 9, 0,
            "Press ENTER to start",
            color_pair=Renderer.COLOR_SUCCESS,
            bold=True,
            center=True
        )

        r.draw_text(r.height - 2, 0, "Press ESC to go back", center=True)

    def _render_running(self, r: Renderer) -> None:
        """Render running calibration."""
        center_y = r.height // 2 - 4

        r.draw_text(
            center_y, 0, "LISTEN AND TAP",
            color_pair=Renderer.COLOR_TITLE,
            bold=True,
            center=True
        )

        # Progress
        progress = f"Beat: {self._beats_passed} / {len(self._beat_times)}"
        r.draw_text(center_y + 2, 0, progress, center=True)

        # Progress bar
        self._progress_bar.render(r, center_y + 3, center=True)

        # Taps received
        taps = f"Taps: {len(self._tap_times)}"
        r.draw_text(center_y + 5, 0, taps, center=True)

        # Visual beat indicator
        current_time = self.engine.audio.get_position_ms()
        time_in_beat = current_time % self._beat_interval_ms
        if time_in_beat < 100:  # Flash for first 100ms of each beat
            beat_indicator = "[ * ]"
            r.draw_text(center_y + 7, 0, beat_indicator, bold=True, center=True,
                       color_pair=Renderer.COLOR_SUCCESS)
        else:
            beat_indicator = "[   ]"
            r.draw_text(center_y + 7, 0, beat_indicator, center=True)

        # Show last tap feedback
        if self._tap_feedback_timer > 0 and self._last_tap_delta is not None:
            delta = self._last_tap_delta
            if delta >= 0:
                delta_text = f"+{delta:.0f}ms"
            else:
                delta_text = f"{delta:.0f}ms"
            r.draw_text(center_y + 9, 0, delta_text, center=True,
                       color_pair=Renderer.COLOR_CARROT)

        r.draw_text(r.height - 2, 0, "Press ESC to cancel", center=True)

    def _render_result(self, r: Renderer) -> None:
        """Render calibration results."""
        center_y = r.height // 2 - 5

        r.draw_text(
            center_y, 0, "CALIBRATION COMPLETE",
            color_pair=Renderer.COLOR_SUCCESS,
            bold=True,
            center=True
        )

        r.draw_text(center_y + 2, 0, f"Taps recorded: {len(self._tap_times)}", center=True)
        r.draw_text(
            center_y + 3, 0,
            f"Calculated offset: {self._calculated_offset:.1f} ms",
            center=True
        )

        if self._calculated_offset > 0:
            r.draw_text(center_y + 5, 0, "(Audio plays late - your taps were adjusted)", center=True)
        elif self._calculated_offset < 0:
            r.draw_text(center_y + 5, 0, "(Audio plays early - your taps were adjusted)", center=True)
        else:
            r.draw_text(center_y + 5, 0, "(No adjustment needed)", center=True)

        r.draw_text(
            center_y + 8, 0,
            "Press ENTER to save and return",
            color_pair=Renderer.COLOR_SUCCESS,
            center=True
        )

        r.draw_text(center_y + 9, 0, "Press R to retry", center=True)
        r.draw_text(r.height - 2, 0, "Press ESC to discard and return", center=True)

    def handle_input(self, key_event: Optional[KeyEvent]) -> None:
        """Handle input based on state."""
        if key_event is None:
            return

        key = key_event.key

        if self._state == "intro":
            if key == InputHandler.KEY_ENTER:
                self._start_calibration()
            elif self.engine.input.is_quit_key(key):
                self._go_back()

        elif self._state == "running":
            if self.engine.input.is_any_gameplay_key(key):
                self._record_tap()
            elif self.engine.input.is_quit_key(key):
                self.engine.audio.stop()
                self._state = "intro"

        elif self._state == "result":
            if key == InputHandler.KEY_ENTER:
                self._save_and_return()
            elif key == ord('r') or key == ord('R'):
                self._state = "intro"
                self._tap_times = []
            elif self.engine.input.is_quit_key(key):
                self._go_back()

    def _start_calibration(self) -> None:
        """Start audio playback for calibration."""
        self._state = "running"
        self._tap_times = []
        self._beats_passed = 0
        self._last_tap_delta = None

        # Start playing the calibration audio
        self.engine.audio.play()
        self.engine.input.reset_timer()

    def _record_tap(self) -> None:
        """Record a tap at current audio position."""
        current_time = self.engine.audio.get_position_ms()
        self._tap_times.append(current_time)

        # Calculate delta from nearest beat for feedback
        if self._beat_times:
            nearest_beat = min(self._beat_times, key=lambda b: abs(current_time - b))
            self._last_tap_delta = current_time - nearest_beat
            self._tap_feedback_timer = 0.3

    def _finish_calibration(self) -> None:
        """Finish calibration and calculate offset."""
        self.engine.audio.stop()
        self._calculate_offset()
        self._state = "result"

    def _calculate_offset(self) -> None:
        """Calculate the average timing offset.

        For each tap, finds the CLOSEST beat (not sequential).
        This handles missed beats correctly - if user misses beat 0
        and taps on beat 1, it matches to beat 1 (not beat 0).
        """
        if len(self._tap_times) < 4 or len(self._beat_times) < 4:
            self._calculated_offset = 0.0
            return

        # For each tap, find the closest beat and calculate delta
        deltas = []

        for tap in self._tap_times:
            # Find the closest beat to this tap
            closest_beat = min(self._beat_times, key=lambda b: abs(tap - b))
            delta = tap - closest_beat

            # Only include taps that are reasonably close to a beat
            # (within 200ms - anything further is likely a random tap or miss)
            if abs(delta) <= 200:
                deltas.append(delta)

        if len(deltas) >= 4:
            # Use median for robustness against outliers
            sorted_deltas = sorted(deltas)
            n = len(sorted_deltas)
            if n % 2 == 0:
                self._calculated_offset = (sorted_deltas[n//2 - 1] + sorted_deltas[n//2]) / 2
            else:
                self._calculated_offset = sorted_deltas[n//2]
        elif deltas:
            # Fallback to mean if we have some but fewer than 4 good taps
            self._calculated_offset = sum(deltas) / len(deltas)
        else:
            self._calculated_offset = 0.0

    def _save_and_return(self) -> None:
        """Save calibration and return to menu."""
        config_dir = str(self.engine.base_dir / "config")
        settings = Settings.load(config_dir)
        settings.calibration_offset_ms = self._calculated_offset
        settings.save(config_dir)

        # Reload TimingManager settings so new calibration takes effect immediately
        self.engine.timing.reload_settings()

        self._go_back()

    def _go_back(self) -> None:
        """Return to main menu."""
        from .menu import MenuScene
        self.engine.set_scene(MenuScene(self.engine))
