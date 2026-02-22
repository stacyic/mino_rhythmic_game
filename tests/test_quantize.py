"""Unit tests for beat quantization."""

import pytest
from src.utils.quantize import quantize_beats, get_grid_times, estimate_bpm


class TestQuantizeBeats:
    """Tests for quantize_beats function."""

    def test_empty_list(self):
        """Test with empty beat list."""
        result = quantize_beats([], 120.0)
        assert result == []

    def test_no_quantization_needed(self):
        """Test when beats are already on grid."""
        # 120 BPM = 500ms intervals
        raw_beats = [0.0, 500.0, 1000.0, 1500.0]
        result = quantize_beats(raw_beats, 120.0)
        assert result == [0.0, 500.0, 1000.0, 1500.0]

    def test_snap_within_threshold(self):
        """Test snapping beats within 50ms threshold."""
        # 120 BPM = 500ms intervals
        # Beat at 480ms should snap to 500ms (20ms off)
        raw_beats = [480.0, 1020.0, 1480.0]
        result = quantize_beats(raw_beats, 120.0, snap_threshold_ms=50.0)
        assert result == [500.0, 1000.0, 1500.0]

    def test_no_snap_outside_threshold(self):
        """Test that beats outside threshold are not snapped."""
        # 120 BPM = 500ms intervals
        # Beat at 440ms is 60ms from 500ms, outside 50ms threshold
        raw_beats = [440.0, 1000.0]
        result = quantize_beats(raw_beats, 120.0, snap_threshold_ms=50.0)
        # 440 stays as is, 1000 is already on grid
        assert result == [440.0, 1000.0]

    def test_snap_early_and_late(self):
        """Test snapping both early and late beats."""
        # 120 BPM = 500ms intervals
        raw_beats = [
            480.0,   # 20ms early -> snap to 500
            1030.0,  # 30ms late -> snap to 1000
            1510.0,  # 10ms late -> snap to 1500
        ]
        result = quantize_beats(raw_beats, 120.0, snap_threshold_ms=50.0)
        assert result == [500.0, 1000.0, 1500.0]

    def test_merge_close_beats(self):
        """Test merging beats that are too close together."""
        # User accidentally double-tapped
        raw_beats = [500.0, 520.0, 1000.0, 1010.0]
        result = quantize_beats(
            raw_beats, 120.0,
            snap_threshold_ms=50.0,
            merge_threshold_ms=50.0
        )
        # Should merge 500+520 and 1000+1010
        assert result == [500.0, 1000.0]

    def test_unsorted_input(self):
        """Test that unsorted input is handled correctly."""
        raw_beats = [1000.0, 500.0, 1500.0, 0.0]
        result = quantize_beats(raw_beats, 120.0)
        assert result == sorted(result)
        assert result == [0.0, 500.0, 1000.0, 1500.0]

    def test_grid_offset(self):
        """Test quantization with grid offset."""
        # 120 BPM with 100ms offset -> grid at 100, 600, 1100, etc.
        raw_beats = [90.0, 620.0, 1090.0]
        result = quantize_beats(
            raw_beats, 120.0,
            snap_threshold_ms=50.0,
            grid_offset_ms=100.0
        )
        assert result == [100.0, 600.0, 1100.0]

    def test_different_bpm(self):
        """Test quantization at different BPMs."""
        # 60 BPM = 1000ms intervals
        raw_beats = [980.0, 2020.0, 2990.0]
        result = quantize_beats(raw_beats, 60.0, snap_threshold_ms=50.0)
        assert result == [1000.0, 2000.0, 3000.0]

    def test_high_bpm(self):
        """Test quantization at high BPM."""
        # 180 BPM = 333.33ms intervals
        raw_beats = [320.0, 680.0, 1010.0]
        result = quantize_beats(raw_beats, 180.0, snap_threshold_ms=50.0)
        # Should snap to ~333, ~667, ~1000
        assert len(result) == 3

    def test_realistic_user_input(self):
        """Test with realistic human timing variation."""
        # 120 BPM, user taps with some jitter
        raw_beats = [
            12.0,    # Should snap to 0
            495.0,   # Should snap to 500
            510.0,   # Should snap to 500, then merge
            1005.0,  # Should snap to 1000
            1492.0,  # Should snap to 1500
            2010.0,  # Should snap to 2000
        ]
        result = quantize_beats(
            raw_beats, 120.0,
            snap_threshold_ms=50.0,
            merge_threshold_ms=50.0
        )
        # After snap and merge: 0, 500, 1000, 1500, 2000
        assert result == [0.0, 500.0, 1000.0, 1500.0, 2000.0]

    def test_boundary_snap_threshold(self):
        """Test at exact snap threshold boundary."""
        # 120 BPM = 500ms intervals
        # Beat exactly 50ms off should snap
        raw_beats = [450.0, 550.0]
        result = quantize_beats(raw_beats, 120.0, snap_threshold_ms=50.0)
        assert result == [500.0]  # Both snap to 500 and merge

    def test_boundary_just_outside(self):
        """Test just outside snap threshold."""
        raw_beats = [449.0]  # 51ms from 500
        result = quantize_beats(raw_beats, 120.0, snap_threshold_ms=50.0)
        assert result == [449.0]  # Should not snap


class TestGetGridTimes:
    """Tests for get_grid_times function."""

    def test_basic_grid(self):
        """Test basic grid generation."""
        # 120 BPM for 1000ms
        times = get_grid_times(120.0, 1000.0)
        assert times == [0.0, 500.0, 1000.0]

    def test_with_offset(self):
        """Test grid with offset."""
        times = get_grid_times(120.0, 1100.0, offset_ms=100.0)
        assert times == [100.0, 600.0, 1100.0]

    def test_subdivision(self):
        """Test beat subdivision."""
        # 120 BPM with subdivision 2 (eighth notes) = 250ms intervals
        times = get_grid_times(120.0, 1000.0, subdivision=2)
        assert times == [0.0, 250.0, 500.0, 750.0, 1000.0]

    def test_quarter_note_subdivision(self):
        """Test subdivision 4 (sixteenth notes)."""
        # 120 BPM with subdivision 4 = 125ms intervals
        times = get_grid_times(120.0, 500.0, subdivision=4)
        assert times == [0.0, 125.0, 250.0, 375.0, 500.0]

    def test_60_bpm(self):
        """Test at 60 BPM."""
        times = get_grid_times(60.0, 3000.0)
        assert times == [0.0, 1000.0, 2000.0, 3000.0]


class TestEstimateBPM:
    """Tests for estimate_bpm function."""

    def test_exact_120_bpm(self):
        """Test estimation from exact 120 BPM taps."""
        # 120 BPM = 500ms intervals
        tap_times = [0.0, 500.0, 1000.0, 1500.0, 2000.0]
        bpm = estimate_bpm(tap_times)
        assert bpm == 120

    def test_exact_60_bpm(self):
        """Test estimation from exact 60 BPM taps."""
        tap_times = [0.0, 1000.0, 2000.0, 3000.0, 4000.0]
        bpm = estimate_bpm(tap_times)
        assert bpm == 60

    def test_exact_180_bpm(self):
        """Test estimation from exact 180 BPM taps."""
        tap_times = [0.0, 333.33, 666.66, 1000.0, 1333.33]
        bpm = estimate_bpm(tap_times)
        assert bpm == pytest.approx(180, abs=2)

    def test_with_jitter(self):
        """Test estimation with human timing jitter."""
        # Roughly 120 BPM with some variation
        tap_times = [0.0, 510.0, 990.0, 1520.0, 1980.0]
        bpm = estimate_bpm(tap_times)
        assert 115 <= bpm <= 125

    def test_insufficient_taps(self):
        """Test with too few taps."""
        tap_times = [0.0, 500.0, 1000.0]
        bpm = estimate_bpm(tap_times)
        assert bpm is None

    def test_filters_outliers(self):
        """Test that outlier intervals are filtered."""
        # 120 BPM with one very long gap (should be ignored)
        tap_times = [0.0, 500.0, 1000.0, 3000.0, 3500.0, 4000.0]
        bpm = estimate_bpm(tap_times, min_bpm=60.0, max_bpm=200.0)
        # The 2000ms gap should be filtered out
        assert bpm is not None

    def test_min_max_bpm_filter(self):
        """Test min/max BPM filtering."""
        # Taps at 30 BPM (2000ms intervals) - too slow
        tap_times = [0.0, 2000.0, 4000.0, 6000.0, 8000.0]
        bpm = estimate_bpm(tap_times, min_bpm=60.0, max_bpm=200.0)
        # All intervals filtered out
        assert bpm is None

    def test_unsorted_input(self):
        """Test that unsorted input is handled."""
        tap_times = [1000.0, 500.0, 0.0, 1500.0, 2000.0]
        bpm = estimate_bpm(tap_times)
        assert bpm == 120


class TestQuantizationIntegration:
    """Integration tests for quantization with other modules."""

    def test_quantize_then_check_timing(self):
        """Test that quantized beats work correctly with timing module."""
        from src.core.timing import TimingManager

        tm = TimingManager(hit_tolerance_ms=150.0)

        # Simulate user recording a beatmap
        raw_beats = [25.0, 520.0, 1010.0, 1485.0]

        # Quantize to 120 BPM
        quantized = quantize_beats(raw_beats, 120.0, snap_threshold_ms=50.0)

        # All quantized beats should be on the grid
        for beat in quantized:
            # Beat should be within 1ms of grid (floating point tolerance)
            grid_beat = round(beat / 500.0) * 500.0
            assert abs(beat - grid_beat) < 1.0

    def test_quantized_beats_are_hittable(self):
        """Test that quantized beats are hittable with proper timing."""
        from src.core.timing import TimingManager

        tm = TimingManager(hit_tolerance_ms=150.0)

        raw_beats = [510.0, 1020.0, 1490.0]
        quantized = quantize_beats(raw_beats, 120.0, snap_threshold_ms=50.0)

        # User playing back with good timing
        for beat in quantized:
            # Playing 50ms early should still be a hit
            assert tm.is_hit(beat - 50.0, beat) is True
            # Playing 50ms late should still be a hit
            assert tm.is_hit(beat + 50.0, beat) is True
