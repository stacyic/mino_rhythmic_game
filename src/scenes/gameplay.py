"""Main gameplay scene with bunny catching carrots."""

from typing import Optional
from pathlib import Path
from dataclasses import dataclass

from .base import Scene
from ..core.input_handler import KeyEvent, InputHandler
from ..ui.renderer import Renderer
from ..ui.ascii_art import AsciiArt
from ..models.beatmap import Beatmap
from ..utils.file_scanner import SongInfo


@dataclass
class FallingCarrot:
    """A carrot falling down the lane."""
    beat_time_ms: float  # When the carrot should reach the bunny
    y_position: float    # Current visual Y position (0 = top, 1 = bunny)
    hit: bool = False    # Whether this carrot was caught


class GameplayScene(Scene):
    """Main gameplay - bunny catches falling carrots."""

    # Visual constants
    LANE_WIDTH = 12
    APPROACH_TIME_MS = 1500.0  # How long carrot takes to fall

    def __init__(self, engine, song: SongInfo):
        super().__init__(engine)
        self._song = song
        self._base_dir = Path(__file__).parent.parent.parent

        # Game state
        self._state = "countdown"  # countdown, playing, gameover, success
        self._countdown = 3
        self._countdown_timer = 0.0

        self._score = 0
        self._carrots: list[FallingCarrot] = []
        self._next_carrot_idx = 0
        self._bunny_catching = False
        self._catch_timer = 0.0

        # Visual feedback
        self._last_hit_delta_ms: Optional[float] = None  # Last hit timing offset
        self._hit_feedback_timer = 0.0  # Timer for hit feedback display

        # Beatmap
        self._beatmap: Optional[Beatmap] = None

    def enter(self) -> None:
        """Initialize gameplay."""
        # Stop any existing audio first
        self.engine.audio.stop()

        # Reset game state
        self._state = "countdown"
        self._countdown = 3
        self._countdown_timer = 0.0
        self._score = 0
        self._carrots = []
        self._next_carrot_idx = 0
        self._bunny_catching = False
        self._catch_timer = 0.0
        self._last_hit_delta_ms = None
        self._hit_feedback_timer = 0.0

        # Flush any pending input (important for retry)
        self.engine.input.flush()

        # Ensure TimingManager has latest settings
        self.engine.timing.reload_settings()

        # Load beatmap
        data_dir = self.engine.data_dir
        self._beatmap = Beatmap.load(
            str(Path(data_dir) / f"{self._song.name}.beatmap.json")
        )

        # Load song
        self.engine.audio.load(self._song.file_path)
        self.engine.input.reset_timer()

    def exit(self) -> None:
        """Cleanup."""
        self.engine.audio.stop()

    def update(self, dt: float) -> None:
        """Update game state."""
        if self._state == "countdown":
            self._update_countdown(dt)
        elif self._state == "playing":
            self._update_playing(dt)

        # Update catch animation
        if self._bunny_catching:
            self._catch_timer -= dt
            if self._catch_timer <= 0:
                self._bunny_catching = False

        # Update hit feedback timer
        if self._hit_feedback_timer > 0:
            self._hit_feedback_timer -= dt

    def _update_countdown(self, dt: float) -> None:
        """Update countdown state."""
        self._countdown_timer += dt

        if self._countdown_timer >= 1.0:
            self._countdown_timer = 0.0
            self._countdown -= 1

            if self._countdown <= 0:
                self._start_playing()

    def _start_playing(self) -> None:
        """Start the actual gameplay."""
        self._state = "playing"
        self.engine.audio.play()
        self.engine.input.reset_timer()

    def _update_playing(self, dt: float) -> None:
        """Update gameplay."""
        if self._beatmap is None:
            return

        current_time = self.engine.audio.get_position_ms()
        timing = self.engine.timing

        # Spawn new carrots
        while self._next_carrot_idx < len(self._beatmap.beats):
            next_beat = self._beatmap.beats[self._next_carrot_idx]

            # Spawn carrot when it should start falling
            spawn_time = next_beat - self.APPROACH_TIME_MS

            if current_time >= spawn_time:
                self._carrots.append(FallingCarrot(
                    beat_time_ms=next_beat,
                    y_position=0.0
                ))
                self._next_carrot_idx += 1
            else:
                break

        # Update carrot positions
        for carrot in self._carrots:
            if not carrot.hit:
                time_until_hit = carrot.beat_time_ms - current_time
                carrot.y_position = 1.0 - (time_until_hit / self.APPROACH_TIME_MS)

        # Check for missed carrots
        for carrot in self._carrots:
            if carrot.hit:
                continue

            # If carrot is past the hit window, it's a miss
            # Use TimingManager's calibration and tolerance
            adjusted_time = current_time - timing.calibration_offset_ms
            if adjusted_time > carrot.beat_time_ms + timing.hit_tolerance_ms:
                self._game_over()
                return

        # Check for success (all carrots caught and song finished)
        if self.engine.audio.is_finished():
            all_caught = all(c.hit for c in self._carrots)
            if all_caught or not self._carrots:
                self._success()
            else:
                self._game_over()

    def render(self) -> None:
        """Render game."""
        r = self.renderer

        if self._state == "countdown":
            self._render_countdown(r)
        elif self._state == "playing":
            self._render_playing(r)
        elif self._state == "gameover":
            self._render_gameover(r)
        elif self._state == "success":
            self._render_success(r)

    def _render_countdown(self, r: Renderer) -> None:
        """Render countdown."""
        center_y = r.height // 2 - 2

        r.draw_text(center_y, 0, f"GET READY!", bold=True, center=True)
        r.draw_text(center_y + 2, 0, f"{self._song.name}", center=True)

        if self._countdown > 0:
            r.draw_text(
                center_y + 5, 0,
                str(self._countdown),
                color_pair=Renderer.COLOR_TITLE,
                bold=True,
                center=True
            )

    def _render_playing(self, r: Renderer) -> None:
        """Render main gameplay."""
        # Calculate lane position (centered)
        lane_x = (r.width - self.LANE_WIDTH) // 2
        lane_height = r.height - 8  # Leave room for bunny and score

        # Draw lane borders
        for y in range(2, 2 + lane_height):
            r.draw_text(y, lane_x, '|', color_pair=Renderer.COLOR_LANE)
            r.draw_text(y, lane_x + self.LANE_WIDTH - 1, '|', color_pair=Renderer.COLOR_LANE)

        # Draw floor
        floor_y = 2 + lane_height
        floor = '=' * self.LANE_WIDTH
        r.draw_text(floor_y, lane_x, floor, color_pair=Renderer.COLOR_LANE)

        # Draw falling carrots
        carrot = AsciiArt.get_carrot()
        for c in self._carrots:
            if c.hit or c.y_position < 0 or c.y_position > 1:
                continue

            carrot_y = int(2 + (c.y_position * (lane_height - carrot.height)))
            carrot_x = lane_x + (self.LANE_WIDTH - carrot.width) // 2

            for i, line in enumerate(carrot.lines):
                if 0 <= carrot_y + i < r.height:
                    r.draw_text(
                        carrot_y + i, carrot_x, line,
                        color_pair=Renderer.COLOR_CARROT
                    )

        # Draw bunny at bottom
        bunny = AsciiArt.get_bunny(catching=self._bunny_catching)
        bunny_y = floor_y + 1
        bunny_x = lane_x + (self.LANE_WIDTH - bunny.width) // 2

        for i, line in enumerate(bunny.lines):
            if 0 <= bunny_y + i < r.height:
                r.draw_text(
                    bunny_y + i, bunny_x, line,
                    color_pair=Renderer.COLOR_BUNNY
                )

        # Draw score (centered at top)
        r.draw_text(0, 0, f"SCORE: {self._score}", bold=True, center=True)

        # Draw timing offset in top left
        if self._last_hit_delta_ms is not None and self._hit_feedback_timer > 0:
            delta = self._last_hit_delta_ms
            if delta > 0:
                timing_text = f"+{delta:.0f}ms"
                color = Renderer.COLOR_ERROR if abs(delta) > 100 else Renderer.COLOR_CARROT
            elif delta < 0:
                timing_text = f"{delta:.0f}ms"
                color = Renderer.COLOR_ERROR if abs(delta) > 100 else Renderer.COLOR_CARROT
            else:
                timing_text = "PERFECT!"
                color = Renderer.COLOR_SUCCESS

            r.draw_text(0, 1, timing_text, color_pair=color, bold=True)

            # Show visual feedback text
            if abs(delta) <= 30:
                feedback = "PERFECT!"
            elif abs(delta) <= 80:
                feedback = "GREAT!"
            elif abs(delta) <= 120:
                feedback = "GOOD"
            else:
                feedback = "OK"

            r.draw_text(1, 1, feedback, color_pair=color)

        # Draw hit indicator at bunny level
        hit_line_y = floor_y
        r.draw_text(hit_line_y, lane_x - 3, ">>>", color_pair=Renderer.COLOR_SUCCESS)
        r.draw_text(
            hit_line_y, lane_x + self.LANE_WIDTH,
            "<<<",
            color_pair=Renderer.COLOR_SUCCESS
        )

    def _render_gameover(self, r: Renderer) -> None:
        """Render game over screen."""
        center_y = r.height // 2 - 4

        r.draw_text(
            center_y, 0, "GAME OVER",
            color_pair=Renderer.COLOR_ERROR,
            bold=True,
            center=True
        )

        r.draw_text(center_y + 2, 0, "You missed a carrot!", center=True)
        r.draw_text(center_y + 4, 0, f"Final Score: {self._score}", center=True)

        r.draw_text(
            r.height - 4, 0,
            "Press R to retry",
            center=True
        )
        r.draw_text(r.height - 2, 0, "Press ESC to return to menu", center=True)

    def _render_success(self, r: Renderer) -> None:
        """Render success screen."""
        center_y = r.height // 2 - 4

        r.draw_text(
            center_y, 0, "SUCCESS!",
            color_pair=Renderer.COLOR_SUCCESS,
            bold=True,
            center=True
        )

        r.draw_text(center_y + 2, 0, "You caught all the carrots!", center=True)
        r.draw_text(center_y + 4, 0, f"Final Score: {self._score}", center=True)

        r.draw_text(
            r.height - 4, 0,
            "Press R to play again",
            center=True
        )
        r.draw_text(r.height - 2, 0, "Press ESC to return to menu", center=True)

    def handle_input(self, key_event: Optional[KeyEvent]) -> None:
        """Handle gameplay input."""
        if key_event is None:
            return

        key = key_event.key

        if self._state == "playing":
            self._handle_playing_input(key)
        elif self._state in ("gameover", "success"):
            self._handle_end_input(key)
        elif self._state == "countdown":
            if self.engine.input.is_quit_key(key):
                self._go_back()

    def _handle_playing_input(self, key: int) -> None:
        """Handle input during gameplay."""
        if self.engine.input.is_quit_key(key):
            self.engine.audio.stop()
            self._go_back()
            return

        if not self.engine.input.is_any_gameplay_key(key):
            return

        # Try to catch a carrot using TimingManager
        current_time = self.engine.audio.get_position_ms()
        timing = self.engine.timing

        # Find closest unhit carrot within tolerance
        best_carrot = None
        best_delta = float('inf')

        for carrot in self._carrots:
            if carrot.hit:
                continue

            # Use TimingManager's is_hit method for consistent hit detection
            if timing.is_hit(current_time, carrot.beat_time_ms):
                delta = abs(timing.get_hit_delta(current_time, carrot.beat_time_ms))
                if delta < best_delta:
                    best_delta = delta
                    best_carrot = carrot

        if best_carrot:
            best_carrot.hit = True
            self._score += 1
            self._bunny_catching = True
            self._catch_timer = 0.15
            # Record timing delta for visual feedback
            self._last_hit_delta_ms = timing.get_hit_delta(current_time, best_carrot.beat_time_ms)
            self._hit_feedback_timer = 0.5  # Show feedback for 0.5 seconds
        else:
            # Key pressed but no carrot in range - show "MISS" feedback
            # Find closest upcoming carrot to show how early/late they were
            closest_delta = None
            for carrot in self._carrots:
                if carrot.hit:
                    continue
                delta = timing.get_hit_delta(current_time, carrot.beat_time_ms)
                if closest_delta is None or abs(delta) < abs(closest_delta):
                    closest_delta = delta

            if closest_delta is not None:
                self._last_hit_delta_ms = closest_delta
                self._hit_feedback_timer = 0.3  # Shorter feedback for miss

            # Still animate bunny trying to catch
            self._bunny_catching = True
            self._catch_timer = 0.1

    def _handle_end_input(self, key: int) -> None:
        """Handle input on end screens."""
        if self.engine.input.is_quit_key(key):
            self._go_back()
        elif key == ord('r') or key == ord('R'):
            # Retry
            self.enter()

    def _game_over(self) -> None:
        """Transition to game over state."""
        self._state = "gameover"
        self.engine.audio.stop()

    def _success(self) -> None:
        """Transition to success state."""
        self._state = "success"
        self.engine.audio.stop()

    def _go_back(self) -> None:
        """Return to song select."""
        from .song_select import SongSelectScene
        self.engine.set_scene(SongSelectScene(self.engine, mode="play"))
