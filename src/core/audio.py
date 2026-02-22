"""Audio management using sounddevice for low-latency playback."""

import threading
import time
from pathlib import Path
from typing import Optional, Callable

import numpy as np
import sounddevice as sd
import soundfile as sf


class AudioManager:
    """Handles audio playback with sample-accurate position tracking."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self._audio_data: Optional[np.ndarray] = None
        self._stream: Optional[sd.OutputStream] = None
        self._playback_frame: int = 0
        self._is_playing: bool = False
        self._is_paused: bool = False
        self._lock = threading.Lock()
        self._loaded_file: Optional[str] = None

    def load(self, file_path: str) -> bool:
        """
        Load an audio file.

        Args:
            file_path: Path to the audio file (MP3, WAV, etc.)

        Returns:
            True if loaded successfully
        """
        try:
            data, sr = sf.read(file_path, dtype='float32')

            # Convert to mono if stereo
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)

            # Resample if needed
            if sr != self.sample_rate:
                # Simple resampling - for production, use librosa or scipy
                ratio = self.sample_rate / sr
                new_length = int(len(data) * ratio)
                indices = np.linspace(0, len(data) - 1, new_length)
                data = np.interp(indices, np.arange(len(data)), data)

            self._audio_data = data.astype(np.float32)
            self._loaded_file = file_path
            self._playback_frame = 0
            return True
        except Exception as e:
            print(f"Error loading audio: {e}")
            return False

    def _audio_callback(
        self,
        outdata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags
    ) -> None:
        """Audio stream callback - fills output buffer."""
        with self._lock:
            if not self._is_playing or self._is_paused or self._audio_data is None:
                outdata.fill(0)
                return

            start = self._playback_frame
            end = start + frames

            if start >= len(self._audio_data):
                outdata.fill(0)
                self._is_playing = False
                return

            if end > len(self._audio_data):
                # Pad with zeros at the end
                valid_frames = len(self._audio_data) - start
                outdata[:valid_frames, 0] = self._audio_data[start:len(self._audio_data)]
                outdata[valid_frames:, 0] = 0
                self._playback_frame = len(self._audio_data)
                self._is_playing = False
            else:
                outdata[:, 0] = self._audio_data[start:end]
                self._playback_frame = end

    def play(self) -> bool:
        """Start playback from the beginning."""
        if self._audio_data is None:
            return False

        self.stop()

        with self._lock:
            self._playback_frame = 0
            self._is_playing = True
            self._is_paused = False

        self._stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=self._audio_callback,
            blocksize=512  # Low latency
        )
        self._stream.start()
        return True

    def stop(self) -> None:
        """Stop playback."""
        with self._lock:
            self._is_playing = False
            self._is_paused = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            self._playback_frame = 0

    def pause(self) -> None:
        """Pause playback."""
        with self._lock:
            self._is_paused = True

    def resume(self) -> None:
        """Resume playback."""
        with self._lock:
            self._is_paused = False

    def get_position_ms(self) -> float:
        """Get current playback position in milliseconds."""
        with self._lock:
            return (self._playback_frame / self.sample_rate) * 1000

    def get_duration_ms(self) -> float:
        """Get total duration in milliseconds."""
        if self._audio_data is None:
            return 0.0
        return (len(self._audio_data) / self.sample_rate) * 1000

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        with self._lock:
            return self._is_playing and not self._is_paused

    def is_finished(self) -> bool:
        """Check if playback has finished."""
        with self._lock:
            if self._audio_data is None:
                return True
            return self._playback_frame >= len(self._audio_data)


class MetronomeGenerator:
    """Generates and plays metronome clicks."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self._click_sound = self._generate_click()
        self._stream: Optional[sd.OutputStream] = None
        self._is_running: bool = False
        self._bpm: float = 120.0
        self._click_times: list[float] = []
        self._next_click_index: int = 0
        self._start_time: float = 0.0
        self._on_click: Optional[Callable[[int], None]] = None

    def _generate_click(
        self,
        frequency: float = 880.0,
        duration_ms: float = 30.0
    ) -> np.ndarray:
        """Generate a short click sound."""
        num_samples = int(self.sample_rate * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, num_samples, dtype=np.float32)

        # Sine wave with exponential decay envelope
        click = np.sin(2 * np.pi * frequency * t)
        envelope = np.exp(-t * 60)

        return (click * envelope * 0.5).astype(np.float32)

    def start(
        self,
        bpm: float = 120.0,
        num_beats: int = 16,
        on_click: Optional[Callable[[int], None]] = None
    ) -> None:
        """
        Start the metronome.

        Args:
            bpm: Beats per minute
            num_beats: Number of beats to play (0 for infinite)
            on_click: Callback when a click plays, receives beat index
        """
        self.stop()

        self._bpm = bpm
        self._on_click = on_click
        beat_interval_ms = 60000.0 / bpm

        # Pre-calculate click times
        self._click_times = [i * beat_interval_ms for i in range(num_beats)]
        self._next_click_index = 0
        self._is_running = True
        self._start_time = time.perf_counter()

        # Start a thread to trigger clicks
        self._thread = threading.Thread(target=self._run_metronome, daemon=True)
        self._thread.start()

    def _run_metronome(self) -> None:
        """Metronome loop running in a separate thread."""
        while self._is_running and self._next_click_index < len(self._click_times):
            current_time = (time.perf_counter() - self._start_time) * 1000

            if self._next_click_index < len(self._click_times):
                next_click_time = self._click_times[self._next_click_index]

                if current_time >= next_click_time:
                    self._play_click()
                    if self._on_click:
                        self._on_click(self._next_click_index)
                    self._next_click_index += 1

            time.sleep(0.001)  # 1ms precision

        self._is_running = False

    def _play_click(self) -> None:
        """Play a single click sound."""
        sd.play(self._click_sound, self.sample_rate)

    def stop(self) -> None:
        """Stop the metronome."""
        self._is_running = False

    def is_running(self) -> bool:
        """Check if metronome is running."""
        return self._is_running

    def get_time_ms(self) -> float:
        """Get elapsed time since metronome started."""
        if not self._is_running:
            return 0.0
        return (time.perf_counter() - self._start_time) * 1000

    def get_expected_beat_time(self, beat_index: int) -> float:
        """Get the expected time for a specific beat."""
        if beat_index < len(self._click_times):
            return self._click_times[beat_index]
        return 0.0
