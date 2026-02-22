"""Beat quantization utilities."""

from typing import Optional


def quantize_beats(
    raw_beats: list[float],
    bpm: float,
    snap_threshold_ms: float = 50.0,
    grid_offset_ms: float = 0.0,
    merge_threshold_ms: float = 50.0
) -> list[float]:
    """
    Quantize raw beat timestamps to a BPM grid.

    Args:
        raw_beats: List of raw timestamps in milliseconds
        bpm: Beats per minute for the grid
        snap_threshold_ms: Max distance to snap to grid (default 50ms)
        grid_offset_ms: Offset for the grid start
        merge_threshold_ms: Merge beats closer than this

    Returns:
        List of quantized beat timestamps
    """
    if not raw_beats:
        return []

    beat_interval_ms = 60000.0 / bpm
    quantized = []

    for raw_time in sorted(raw_beats):
        # Find nearest grid position
        adjusted = raw_time - grid_offset_ms
        nearest_beat_index = round(adjusted / beat_interval_ms)
        nearest_grid_time = (nearest_beat_index * beat_interval_ms) + grid_offset_ms

        # Snap if within threshold
        if abs(raw_time - nearest_grid_time) <= snap_threshold_ms:
            final_time = nearest_grid_time
        else:
            final_time = raw_time

        # Avoid duplicates / merge close beats
        if quantized:
            if abs(final_time - quantized[-1]) < merge_threshold_ms:
                continue  # Skip this beat, too close to previous

        quantized.append(final_time)

    return quantized


def get_grid_times(
    bpm: float,
    duration_ms: float,
    offset_ms: float = 0.0,
    subdivision: int = 1
) -> list[float]:
    """
    Generate grid times for a given BPM and duration.

    Args:
        bpm: Beats per minute
        duration_ms: Total duration
        offset_ms: Grid offset
        subdivision: Beat subdivision (1 = quarter, 2 = eighth, etc.)

    Returns:
        List of grid times
    """
    beat_interval_ms = 60000.0 / (bpm * subdivision)
    times = []
    current = offset_ms

    while current <= duration_ms:
        if current >= 0:
            times.append(current)
        current += beat_interval_ms

    return times


def estimate_bpm(
    tap_times: list[float],
    min_bpm: float = 60.0,
    max_bpm: float = 200.0
) -> Optional[float]:
    """
    Estimate BPM from tap timestamps.

    Args:
        tap_times: List of tap timestamps in milliseconds
        min_bpm: Minimum expected BPM
        max_bpm: Maximum expected BPM

    Returns:
        Estimated BPM or None if unable to determine
    """
    if len(tap_times) < 4:
        return None

    sorted_taps = sorted(tap_times)
    intervals = []

    for i in range(1, len(sorted_taps)):
        interval = sorted_taps[i] - sorted_taps[i - 1]
        # Filter out unreasonable intervals
        min_interval = 60000.0 / max_bpm
        max_interval = 60000.0 / min_bpm

        if min_interval <= interval <= max_interval:
            intervals.append(interval)

    if not intervals:
        return None

    avg_interval = sum(intervals) / len(intervals)
    bpm = 60000.0 / avg_interval

    return round(bpm)
