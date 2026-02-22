"""Timing utilities for rhythm game precision."""

import time
from pathlib import Path
from typing import Optional


class TimingManager:
    """Manages high-precision timing for the game."""

    DEFAULT_HIT_TOLERANCE_MS = 150.0

    def __init__(
        self,
        config_dir: Optional[str] = None,
        hit_tolerance_ms: Optional[float] = None,
        calibration_offset_ms: Optional[float] = None
    ):
        """
        Initialize TimingManager.

        Args:
            config_dir: Directory to load/save settings from. If provided,
                        settings are loaded automatically.
            hit_tolerance_ms: Override hit tolerance (uses settings or default if None)
            calibration_offset_ms: Override calibration offset (uses settings or 0 if None)
        """
        self._config_dir = config_dir
        self._start_time: float = 0.0

        # Default values
        self.hit_tolerance_ms = hit_tolerance_ms or self.DEFAULT_HIT_TOLERANCE_MS
        self.calibration_offset_ms = calibration_offset_ms or 0.0

        # Load from settings if config_dir provided
        if config_dir:
            self.reload_settings()

    def reload_settings(self) -> None:
        """
        Reload calibration and tolerance settings from config file.

        Call this after calibration is updated to apply new settings.
        """
        if not self._config_dir:
            return

        # Import here to avoid circular imports
        from ..models.settings import Settings

        settings = Settings.load(self._config_dir)
        self.calibration_offset_ms = settings.calibration_offset_ms
        self.hit_tolerance_ms = settings.hit_tolerance_ms

    def set_config_dir(self, config_dir: str) -> None:
        """
        Set the config directory and reload settings.

        Args:
            config_dir: Directory containing settings.json
        """
        self._config_dir = config_dir
        self.reload_settings()

    def start(self) -> None:
        """Record the start time."""
        self._start_time = time.perf_counter()

    def get_time_ms(self) -> float:
        """Get elapsed time in milliseconds since start."""
        return (time.perf_counter() - self._start_time) * 1000

    def is_hit(
        self,
        input_time_ms: float,
        beat_time_ms: float,
        calibration_offset_ms: Optional[float] = None
    ) -> bool:
        """
        Check if input timing is within tolerance of beat.

        Args:
            input_time_ms: When the user pressed the key
            beat_time_ms: When the beat should occur
            calibration_offset_ms: Override calibration offset (uses stored value if None)

        Returns:
            True if the hit is within tolerance
        """
        offset = calibration_offset_ms if calibration_offset_ms is not None else self.calibration_offset_ms
        adjusted_input = input_time_ms - offset
        return abs(adjusted_input - beat_time_ms) <= self.hit_tolerance_ms

    def get_hit_delta(
        self,
        input_time_ms: float,
        beat_time_ms: float,
        calibration_offset_ms: Optional[float] = None
    ) -> float:
        """
        Get the timing difference (negative = early, positive = late).

        Args:
            input_time_ms: When the user pressed the key
            beat_time_ms: When the beat should occur
            calibration_offset_ms: Override calibration offset (uses stored value if None)

        Returns:
            Timing delta in milliseconds
        """
        offset = calibration_offset_ms if calibration_offset_ms is not None else self.calibration_offset_ms
        adjusted_input = input_time_ms - offset
        return adjusted_input - beat_time_ms


def get_nearest_beat(time_ms: float, bpm: float, offset_ms: float = 0.0) -> float:
    """
    Get the nearest beat time on the BPM grid.

    Args:
        time_ms: The time to snap
        bpm: Beats per minute
        offset_ms: Grid offset from zero

    Returns:
        Nearest beat time in milliseconds
    """
    beat_interval_ms = 60000.0 / bpm
    adjusted_time = time_ms - offset_ms
    beat_index = round(adjusted_time / beat_interval_ms)
    return (beat_index * beat_interval_ms) + offset_ms


def get_beat_times(
    bpm: float,
    duration_ms: float,
    offset_ms: float = 0.0
) -> list[float]:
    """
    Generate all beat times for a given BPM and duration.

    Args:
        bpm: Beats per minute
        duration_ms: Total duration in milliseconds
        offset_ms: Grid offset from zero

    Returns:
        List of beat times in milliseconds
    """
    beat_interval_ms = 60000.0 / bpm
    beats = []
    current = offset_ms
    while current <= duration_ms:
        if current >= 0:
            beats.append(current)
        current += beat_interval_ms
    return beats
