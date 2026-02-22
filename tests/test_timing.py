"""Unit tests for timing module."""

import pytest
import time
from src.core.timing import (
    TimingManager,
    get_nearest_beat,
    get_beat_times,
)


class TestTimingManager:
    """Tests for TimingManager class."""

    def test_init_default_tolerance(self):
        """Test default hit tolerance is 150ms."""
        tm = TimingManager()
        assert tm.hit_tolerance_ms == 150.0

    def test_init_custom_tolerance(self):
        """Test custom hit tolerance."""
        tm = TimingManager(hit_tolerance_ms=100.0)
        assert tm.hit_tolerance_ms == 100.0

    def test_is_hit_exact(self):
        """Test hit detection with exact timing."""
        tm = TimingManager(hit_tolerance_ms=150.0)
        assert tm.is_hit(1000.0, 1000.0) is True

    def test_is_hit_within_tolerance_early(self):
        """Test hit detection when input is early but within tolerance."""
        tm = TimingManager(hit_tolerance_ms=150.0)
        # Input 100ms early
        assert tm.is_hit(900.0, 1000.0) is True

    def test_is_hit_within_tolerance_late(self):
        """Test hit detection when input is late but within tolerance."""
        tm = TimingManager(hit_tolerance_ms=150.0)
        # Input 100ms late
        assert tm.is_hit(1100.0, 1000.0) is True

    def test_is_hit_at_tolerance_boundary(self):
        """Test hit detection at exact tolerance boundary."""
        tm = TimingManager(hit_tolerance_ms=150.0)
        # Exactly 150ms early - should be a hit
        assert tm.is_hit(850.0, 1000.0) is True
        # Exactly 150ms late - should be a hit
        assert tm.is_hit(1150.0, 1000.0) is True

    def test_is_hit_outside_tolerance(self):
        """Test hit detection when outside tolerance."""
        tm = TimingManager(hit_tolerance_ms=150.0)
        # 200ms early
        assert tm.is_hit(800.0, 1000.0) is False
        # 200ms late
        assert tm.is_hit(1200.0, 1000.0) is False

    def test_is_hit_with_calibration_offset_positive(self):
        """Test hit detection with positive calibration offset (user taps late)."""
        tm = TimingManager(hit_tolerance_ms=150.0)
        # User consistently taps 50ms late, so we subtract 50ms from their input
        # Input at 1050ms with offset 50ms -> adjusted to 1000ms
        assert tm.is_hit(1050.0, 1000.0, calibration_offset_ms=50.0) is True

    def test_is_hit_with_calibration_offset_negative(self):
        """Test hit detection with negative calibration offset (user taps early)."""
        tm = TimingManager(hit_tolerance_ms=150.0)
        # User consistently taps 30ms early, so we add 30ms to their input
        # Input at 970ms with offset -30ms -> adjusted to 1000ms
        assert tm.is_hit(970.0, 1000.0, calibration_offset_ms=-30.0) is True

    def test_is_hit_calibration_makes_miss_into_hit(self):
        """Test that calibration can turn a miss into a hit."""
        tm = TimingManager(hit_tolerance_ms=150.0)
        # Without calibration: 1200ms vs 1000ms = 200ms off = miss
        assert tm.is_hit(1200.0, 1000.0, calibration_offset_ms=0.0) is False
        # With calibration of 100ms: 1200 - 100 = 1100ms vs 1000ms = 100ms off = hit
        assert tm.is_hit(1200.0, 1000.0, calibration_offset_ms=100.0) is True

    def test_get_hit_delta_exact(self):
        """Test hit delta calculation for exact hit."""
        tm = TimingManager()
        assert tm.get_hit_delta(1000.0, 1000.0) == 0.0

    def test_get_hit_delta_early(self):
        """Test hit delta calculation for early hit (negative)."""
        tm = TimingManager()
        assert tm.get_hit_delta(900.0, 1000.0) == -100.0

    def test_get_hit_delta_late(self):
        """Test hit delta calculation for late hit (positive)."""
        tm = TimingManager()
        assert tm.get_hit_delta(1100.0, 1000.0) == 100.0

    def test_get_hit_delta_with_calibration(self):
        """Test hit delta with calibration offset."""
        tm = TimingManager()
        # Input at 1050, beat at 1000, offset 50
        # Adjusted input = 1050 - 50 = 1000
        # Delta = 1000 - 1000 = 0
        assert tm.get_hit_delta(1050.0, 1000.0, calibration_offset_ms=50.0) == 0.0

    def test_get_time_ms_increases(self):
        """Test that get_time_ms increases over time."""
        tm = TimingManager()
        tm.start()
        time1 = tm.get_time_ms()
        time.sleep(0.01)  # 10ms
        time2 = tm.get_time_ms()
        assert time2 > time1
        assert time2 - time1 >= 10  # At least 10ms passed


class TestGetNearestBeat:
    """Tests for get_nearest_beat function."""

    def test_exact_beat(self):
        """Test when time is exactly on a beat."""
        # 120 BPM = 500ms per beat
        # Beat 0 at 0ms, beat 1 at 500ms, beat 2 at 1000ms
        assert get_nearest_beat(500.0, 120.0) == 500.0
        assert get_nearest_beat(1000.0, 120.0) == 1000.0

    def test_between_beats_snap_to_earlier(self):
        """Test snapping to earlier beat when closer."""
        # 120 BPM = 500ms per beat
        # 200ms is closer to beat at 0ms than beat at 500ms
        assert get_nearest_beat(200.0, 120.0) == 0.0

    def test_between_beats_snap_to_later(self):
        """Test snapping to later beat when closer."""
        # 120 BPM = 500ms per beat
        # 300ms is closer to beat at 500ms than beat at 0ms
        assert get_nearest_beat(300.0, 120.0) == 500.0

    def test_exactly_halfway(self):
        """Test behavior when exactly between beats."""
        # 120 BPM = 500ms per beat
        # 250ms is exactly halfway between 0 and 500
        # round() should round to nearest even (0)
        result = get_nearest_beat(250.0, 120.0)
        assert result in [0.0, 500.0]  # Either is acceptable

    def test_with_offset(self):
        """Test beat grid with offset."""
        # 120 BPM with 100ms offset
        # Beats at 100ms, 600ms, 1100ms, etc.
        assert get_nearest_beat(150.0, 120.0, offset_ms=100.0) == 100.0
        assert get_nearest_beat(400.0, 120.0, offset_ms=100.0) == 600.0

    def test_different_bpm(self):
        """Test with different BPM values."""
        # 60 BPM = 1000ms per beat
        assert get_nearest_beat(400.0, 60.0) == 0.0
        assert get_nearest_beat(600.0, 60.0) == 1000.0

        # 180 BPM = 333.33ms per beat
        assert get_nearest_beat(100.0, 180.0) == 0.0


class TestGetBeatTimes:
    """Tests for get_beat_times function."""

    def test_basic_beats(self):
        """Test basic beat time generation."""
        # 120 BPM for 1000ms = beats at 0, 500, 1000
        beats = get_beat_times(120.0, 1000.0)
        assert beats == [0.0, 500.0, 1000.0]

    def test_with_offset(self):
        """Test beat times with offset."""
        # 120 BPM with 100ms offset for 1100ms
        # Beats at 100, 600, 1100
        beats = get_beat_times(120.0, 1100.0, offset_ms=100.0)
        assert beats == [100.0, 600.0, 1100.0]

    def test_60_bpm(self):
        """Test 60 BPM (1 beat per second)."""
        beats = get_beat_times(60.0, 2000.0)
        assert beats == [0.0, 1000.0, 2000.0]

    def test_empty_duration(self):
        """Test with zero duration."""
        beats = get_beat_times(120.0, 0.0)
        assert beats == [0.0]

    def test_short_duration(self):
        """Test duration shorter than one beat."""
        # 120 BPM = 500ms per beat, duration 400ms
        beats = get_beat_times(120.0, 400.0)
        assert beats == [0.0]


class TestTimingEdgeCases:
    """Edge case tests for timing functions."""

    def test_very_high_bpm(self):
        """Test with very high BPM (240)."""
        # 240 BPM = 250ms per beat
        beats = get_beat_times(240.0, 1000.0)
        assert len(beats) == 5  # 0, 250, 500, 750, 1000

    def test_very_low_bpm(self):
        """Test with very low BPM (30)."""
        # 30 BPM = 2000ms per beat
        beats = get_beat_times(30.0, 4000.0)
        assert beats == [0.0, 2000.0, 4000.0]

    def test_fractional_bpm(self):
        """Test with fractional BPM."""
        # 123.5 BPM
        beats = get_beat_times(123.5, 1000.0)
        assert len(beats) >= 2

    def test_timing_precision(self):
        """Test that timing calculations maintain precision."""
        tm = TimingManager(hit_tolerance_ms=150.0)
        # Test with precise millisecond values
        assert tm.is_hit(1000.123, 1000.0) is True
        assert tm.is_hit(1150.001, 1000.0) is False


class TestTimingManagerCalibration:
    """Tests for TimingManager calibration integration."""

    def test_init_with_calibration_offset(self):
        """Test initialization with calibration offset."""
        tm = TimingManager(calibration_offset_ms=50.0)
        assert tm.calibration_offset_ms == 50.0

    def test_default_calibration_is_zero(self):
        """Test that default calibration offset is zero."""
        tm = TimingManager()
        assert tm.calibration_offset_ms == 0.0

    def test_stored_calibration_used_by_default(self):
        """Test that is_hit uses stored calibration when not overridden."""
        tm = TimingManager(hit_tolerance_ms=150.0, calibration_offset_ms=50.0)

        # Input at 1050ms with stored calibration of 50ms
        # Adjusted = 1050 - 50 = 1000ms, beat at 1000ms = exact hit
        assert tm.is_hit(1050.0, 1000.0) is True

        # Without the stored calibration, this would be +50ms late
        # but still within 150ms tolerance, so also a hit
        assert tm.is_hit(1050.0, 1000.0, calibration_offset_ms=0.0) is True

    def test_override_calibration_in_is_hit(self):
        """Test that calibration can be overridden per-call."""
        tm = TimingManager(hit_tolerance_ms=150.0, calibration_offset_ms=50.0)

        # With stored calibration (50ms): 1200 - 50 = 1150, within 150ms = hit
        assert tm.is_hit(1200.0, 1000.0) is True

        # Override with 0ms: 1200 - 0 = 1200, 200ms late = miss
        assert tm.is_hit(1200.0, 1000.0, calibration_offset_ms=0.0) is False

    def test_stored_calibration_used_in_get_hit_delta(self):
        """Test that get_hit_delta uses stored calibration."""
        tm = TimingManager(calibration_offset_ms=50.0)

        # Input at 1050ms with stored calibration of 50ms
        # Adjusted = 1050 - 50 = 1000ms, delta = 1000 - 1000 = 0
        assert tm.get_hit_delta(1050.0, 1000.0) == 0.0

    def test_override_calibration_in_get_hit_delta(self):
        """Test that calibration can be overridden in get_hit_delta."""
        tm = TimingManager(calibration_offset_ms=50.0)

        # Override with 0ms: delta = 1050 - 1000 = 50
        assert tm.get_hit_delta(1050.0, 1000.0, calibration_offset_ms=0.0) == 50.0


class TestTimingManagerSettingsPersistence:
    """Tests for TimingManager settings loading from files."""

    def test_load_settings_from_config_dir(self):
        """Test loading settings from a config directory."""
        import tempfile
        from src.models.settings import Settings

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create settings file with custom values
            settings = Settings(
                calibration_offset_ms=75.0,
                hit_tolerance_ms=100.0
            )
            settings.save(tmpdir)

            # Create TimingManager with config_dir
            tm = TimingManager(config_dir=tmpdir)

            assert tm.calibration_offset_ms == 75.0
            assert tm.hit_tolerance_ms == 100.0

    def test_reload_settings_updates_values(self):
        """Test that reload_settings updates the values."""
        import tempfile
        from src.models.settings import Settings

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial settings
            settings = Settings(calibration_offset_ms=50.0)
            settings.save(tmpdir)

            tm = TimingManager(config_dir=tmpdir)
            assert tm.calibration_offset_ms == 50.0

            # Update settings file
            settings.calibration_offset_ms = 100.0
            settings.save(tmpdir)

            # Reload should pick up new value
            tm.reload_settings()
            assert tm.calibration_offset_ms == 100.0

    def test_set_config_dir_loads_settings(self):
        """Test that set_config_dir loads settings immediately."""
        import tempfile
        from src.models.settings import Settings

        with tempfile.TemporaryDirectory() as tmpdir:
            settings = Settings(calibration_offset_ms=80.0)
            settings.save(tmpdir)

            tm = TimingManager()
            assert tm.calibration_offset_ms == 0.0  # Default

            tm.set_config_dir(tmpdir)
            assert tm.calibration_offset_ms == 80.0

    def test_reload_without_config_dir_does_nothing(self):
        """Test that reload_settings is safe without config_dir."""
        tm = TimingManager(calibration_offset_ms=50.0)

        # Should not raise and should not change value
        tm.reload_settings()
        assert tm.calibration_offset_ms == 50.0

    def test_missing_settings_file_uses_defaults(self):
        """Test that missing settings file results in defaults."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Empty directory, no settings file
            tm = TimingManager(config_dir=tmpdir)

            assert tm.calibration_offset_ms == 0.0
            assert tm.hit_tolerance_ms == 150.0


class TestTimingManagerCalibrationScenarios:
    """Real-world scenarios for calibration integration."""

    def test_late_tapper_calibration(self):
        """Test scenario: user consistently taps 60ms late."""
        tm = TimingManager(
            hit_tolerance_ms=150.0,
            calibration_offset_ms=60.0  # User taps 60ms late
        )

        # Beat at 1000ms, user taps at 1060ms
        # Without calibration: 60ms late but still a hit
        # With calibration: adjusted to 1000ms = perfect

        # Both should be hits, but calibrated has smaller delta
        assert tm.is_hit(1060.0, 1000.0) is True

        delta_calibrated = tm.get_hit_delta(1060.0, 1000.0)
        delta_uncalibrated = tm.get_hit_delta(1060.0, 1000.0, calibration_offset_ms=0.0)

        assert delta_calibrated == 0.0
        assert delta_uncalibrated == 60.0

    def test_early_tapper_calibration(self):
        """Test scenario: user consistently taps 40ms early."""
        tm = TimingManager(
            hit_tolerance_ms=150.0,
            calibration_offset_ms=-40.0  # User taps 40ms early
        )

        # Beat at 1000ms, user taps at 960ms
        # With calibration: 960 - (-40) = 1000ms = perfect
        assert tm.is_hit(960.0, 1000.0) is True
        assert tm.get_hit_delta(960.0, 1000.0) == 0.0

    def test_calibration_saves_borderline_hit(self):
        """Test that calibration can save a borderline miss."""
        tm = TimingManager(hit_tolerance_ms=150.0)

        # Without calibration: 1180ms vs 1000ms = 180ms late = MISS
        assert tm.is_hit(1180.0, 1000.0, calibration_offset_ms=0.0) is False

        # With 50ms calibration: 1180 - 50 = 1130ms vs 1000ms = 130ms late = HIT
        tm.calibration_offset_ms = 50.0
        assert tm.is_hit(1180.0, 1000.0) is True

    def test_sequential_beats_with_calibration(self):
        """Test hitting multiple beats with calibration applied."""
        tm = TimingManager(
            hit_tolerance_ms=150.0,
            calibration_offset_ms=45.0  # Realistic audio latency
        )

        # Simulate hitting beats at 0, 500, 1000, 1500ms
        # User inputs arrive ~45ms late due to audio latency
        beats = [0.0, 500.0, 1000.0, 1500.0]
        user_inputs = [48.0, 542.0, 1048.0, 1540.0]  # ~45ms late with jitter

        for beat, input_time in zip(beats, user_inputs):
            assert tm.is_hit(input_time, beat) is True
            delta = tm.get_hit_delta(input_time, beat)
            # After calibration, delta should be small (within ±10ms)
            assert abs(delta) < 10.0
