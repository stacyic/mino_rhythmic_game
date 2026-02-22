"""Unit tests for calibration logic."""

import pytest


def calculate_calibration_offset(
    tap_times: list[float],
    beat_times: list[float],
    max_delta_ms: float = 200.0
) -> float:
    """
    Calculate calibration offset from tap and beat times.

    This is the core calibration algorithm extracted for testing.
    Uses closest-beat matching and median for robustness.

    Args:
        tap_times: List of user tap timestamps in ms
        beat_times: List of expected beat times in ms
        max_delta_ms: Maximum acceptable delta to consider a valid tap

    Returns:
        Median offset (positive = user taps late, negative = early)
    """
    if len(tap_times) < 4 or len(beat_times) < 4:
        return 0.0

    # For each tap, find the closest beat (not sequential)
    deltas = []

    for tap in tap_times:
        # Find the closest beat to this tap
        closest_beat = min(beat_times, key=lambda b: abs(tap - b))
        delta = tap - closest_beat

        # Only include taps that are reasonably close to a beat
        if abs(delta) <= max_delta_ms:
            deltas.append(delta)

    if len(deltas) >= 4:
        # Use median for robustness against outliers
        sorted_deltas = sorted(deltas)
        n = len(sorted_deltas)
        if n % 2 == 0:
            return (sorted_deltas[n//2 - 1] + sorted_deltas[n//2]) / 2
        else:
            return sorted_deltas[n//2]
    elif deltas:
        # Fallback to mean if fewer than 4 good taps
        return sum(deltas) / len(deltas)
    return 0.0


class TestCalibrationOffset:
    """Tests for calibration offset calculation."""

    def test_perfect_timing(self):
        """Test when user taps exactly on beat."""
        beat_times = [0.0, 500.0, 1000.0, 1500.0, 2000.0]
        tap_times = [0.0, 500.0, 1000.0, 1500.0, 2000.0]

        offset = calculate_calibration_offset(tap_times, beat_times)
        assert offset == 0.0

    def test_consistent_late_taps(self):
        """Test when user consistently taps late."""
        beat_times = [0.0, 500.0, 1000.0, 1500.0, 2000.0]
        # User taps 50ms late each time
        tap_times = [50.0, 550.0, 1050.0, 1550.0, 2050.0]

        offset = calculate_calibration_offset(tap_times, beat_times)
        assert offset == pytest.approx(50.0)

    def test_consistent_early_taps(self):
        """Test when user consistently taps early."""
        beat_times = [0.0, 500.0, 1000.0, 1500.0, 2000.0]
        # User taps 30ms early each time
        tap_times = [-30.0, 470.0, 970.0, 1470.0, 1970.0]

        offset = calculate_calibration_offset(tap_times, beat_times)
        assert offset == pytest.approx(-30.0)

    def test_variable_timing(self):
        """Test with variable timing (average offset)."""
        beat_times = [0.0, 500.0, 1000.0, 1500.0, 2000.0]
        # User has variable timing: +20, +40, +60, +80, +100
        tap_times = [20.0, 540.0, 1060.0, 1580.0, 2100.0]

        offset = calculate_calibration_offset(tap_times, beat_times)
        # Average of 20, 40, 60, 80, 100 = 60
        assert offset == pytest.approx(60.0)

    def test_insufficient_taps(self):
        """Test with too few taps (should return 0)."""
        beat_times = [0.0, 500.0, 1000.0, 1500.0]
        tap_times = [0.0, 500.0, 1000.0]  # Only 3 taps

        offset = calculate_calibration_offset(tap_times, beat_times)
        assert offset == 0.0

    def test_insufficient_beats(self):
        """Test with too few beats (should return 0)."""
        beat_times = [0.0, 500.0, 1000.0]  # Only 3 beats
        tap_times = [0.0, 500.0, 1000.0, 1500.0]

        offset = calculate_calibration_offset(tap_times, beat_times)
        assert offset == 0.0

    def test_skipped_beats(self):
        """Test when user skips some beats."""
        beat_times = [0.0, 500.0, 1000.0, 1500.0, 2000.0, 2500.0]
        # User skips beat 2 (1000ms)
        tap_times = [50.0, 550.0, 1550.0, 2050.0, 2550.0]

        offset = calculate_calibration_offset(tap_times, beat_times)
        # Should match: 50-0=50, 550-500=50, 1550-1500=50, 2050-2000=50, 2550-2500=50
        assert offset == pytest.approx(50.0)

    def test_extra_taps(self):
        """Test when user taps more than beats exist."""
        beat_times = [0.0, 500.0, 1000.0, 1500.0]
        # User taps extra at the end
        tap_times = [0.0, 500.0, 1000.0, 1500.0, 1800.0, 2000.0]

        offset = calculate_calibration_offset(tap_times, beat_times)
        # Extra taps should match to beats and give 0 offset for matched ones
        assert offset == pytest.approx(0.0, abs=50)

    def test_outlier_tap_ignored(self):
        """Test that outlier taps beyond max_delta are ignored."""
        beat_times = [0.0, 500.0, 1000.0, 1500.0, 2000.0]
        # One tap is way off (500ms delta from any beat)
        tap_times = [50.0, 550.0, 750.0, 1550.0, 2050.0]  # 750 is 250ms from both 500 and 1000

        offset = calculate_calibration_offset(tap_times, beat_times, max_delta_ms=200.0)
        # The 750 tap should be ignored (250ms from nearest beat, outside 200ms threshold)
        # Matches: 50-0=50, 550-500=50, 1550-1500=50, 2050-2000=50
        assert offset == pytest.approx(50.0)

    def test_realistic_calibration(self):
        """Test with realistic human timing variation."""
        # 120 BPM metronome for 8 beats
        beat_times = [i * 500.0 for i in range(8)]
        # Simulated human taps with audio latency of ~45ms and some jitter
        tap_times = [
            47.0,   # +47
            542.0,  # +42
            548.0,  # +48
            1040.0, # +40
            1552.0, # +52
            2043.0, # +43
            2555.0, # +55
            3038.0, # +38
        ]

        offset = calculate_calibration_offset(tap_times, beat_times)
        # Average should be around 45ms
        assert 35.0 <= offset <= 55.0

    def test_negative_tap_times(self):
        """Test handling of negative tap times (tapped before first beat)."""
        beat_times = [0.0, 500.0, 1000.0, 1500.0, 2000.0]
        tap_times = [-20.0, 480.0, 980.0, 1480.0, 1980.0]

        offset = calculate_calibration_offset(tap_times, beat_times)
        assert offset == pytest.approx(-20.0)


class TestCalibrationIntegration:
    """Integration tests for calibration with timing module."""

    def test_calibration_improves_hit_detection(self):
        """Test that applying calibration offset improves hit detection."""
        from src.core.timing import TimingManager

        tm = TimingManager(hit_tolerance_ms=150.0)

        # User taps 80ms late consistently
        beat_time = 1000.0
        user_input = 1080.0

        # Without calibration: still a hit (80ms < 150ms)
        assert tm.is_hit(user_input, beat_time, calibration_offset_ms=0.0) is True

        # With calibration: perfect hit
        delta_without = tm.get_hit_delta(user_input, beat_time, calibration_offset_ms=0.0)
        delta_with = tm.get_hit_delta(user_input, beat_time, calibration_offset_ms=80.0)

        assert abs(delta_with) < abs(delta_without)
        assert delta_with == pytest.approx(0.0)

    def test_calibration_edge_case_converts_miss_to_hit(self):
        """Test edge case where calibration converts a miss to a hit."""
        from src.core.timing import TimingManager

        tm = TimingManager(hit_tolerance_ms=150.0)

        beat_time = 1000.0
        # User taps 200ms late (would be a miss)
        user_input = 1200.0

        # Without calibration: miss
        assert tm.is_hit(user_input, beat_time, calibration_offset_ms=0.0) is False

        # With 100ms calibration: 1200 - 100 = 1100, which is 100ms late = hit
        assert tm.is_hit(user_input, beat_time, calibration_offset_ms=100.0) is True


class TestCalibrationBPM:
    """Tests for calibration at different BPMs."""

    def test_120_bpm(self):
        """Test calibration at 120 BPM (500ms intervals)."""
        beat_interval = 500.0
        beat_times = [i * beat_interval for i in range(8)]
        tap_times = [(i * beat_interval) + 60.0 for i in range(8)]

        offset = calculate_calibration_offset(tap_times, beat_times)
        assert offset == pytest.approx(60.0)

    def test_60_bpm(self):
        """Test calibration at 60 BPM (1000ms intervals)."""
        beat_interval = 1000.0
        beat_times = [i * beat_interval for i in range(8)]
        tap_times = [(i * beat_interval) + 45.0 for i in range(8)]

        offset = calculate_calibration_offset(tap_times, beat_times)
        assert offset == pytest.approx(45.0)

    def test_180_bpm(self):
        """Test calibration at 180 BPM (333ms intervals)."""
        beat_interval = 333.33
        beat_times = [i * beat_interval for i in range(8)]
        tap_times = [(i * beat_interval) + 30.0 for i in range(8)]

        offset = calculate_calibration_offset(tap_times, beat_times)
        assert offset == pytest.approx(30.0, abs=1.0)
