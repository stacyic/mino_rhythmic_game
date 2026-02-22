"""Beatmap data model and persistence."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Beatmap:
    """Represents a beatmap for a song."""

    song_file: str
    bpm: float
    beats: list[float] = field(default_factory=list)  # Timestamps in ms
    name: str = ""
    version: int = 1
    created_at: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = Path(self.song_file).stem
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def add_beat(self, timestamp_ms: float) -> None:
        """Add a beat at the specified timestamp."""
        self.beats.append(timestamp_ms)
        self.beats.sort()

    def remove_beat(self, timestamp_ms: float, tolerance_ms: float = 50.0) -> bool:
        """
        Remove a beat near the specified timestamp.

        Returns:
            True if a beat was removed
        """
        for i, beat in enumerate(self.beats):
            if abs(beat - timestamp_ms) <= tolerance_ms:
                self.beats.pop(i)
                return True
        return False

    def get_beats_in_range(
        self,
        start_ms: float,
        end_ms: float
    ) -> list[tuple[int, float]]:
        """
        Get all beats within a time range.

        Returns:
            List of (index, timestamp) tuples
        """
        result = []
        for i, beat in enumerate(self.beats):
            if start_ms <= beat <= end_ms:
                result.append((i, beat))
        return result

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "song_file": self.song_file,
            "bpm": self.bpm,
            "beats": self.beats,
            "name": self.name,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Beatmap':
        """Create from dictionary."""
        return cls(
            version=data.get("version", 1),
            song_file=data["song_file"],
            bpm=data["bpm"],
            beats=data.get("beats", []),
            name=data.get("name", ""),
            created_at=data.get("created_at", ""),
        )

    def save(self, directory: str) -> str:
        """
        Save beatmap to a JSON file.

        Args:
            directory: Directory to save to

        Returns:
            Path to the saved file
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)

        filename = f"{self.name}.beatmap.json"
        file_path = dir_path / filename

        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

        return str(file_path)

    @classmethod
    def load(cls, file_path: str) -> Optional['Beatmap']:
        """
        Load beatmap from a JSON file.

        Args:
            file_path: Path to the beatmap file

        Returns:
            Beatmap instance or None if failed
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"Error loading beatmap: {e}")
            return None


def get_beatmap_for_song(song_file: str, data_dir: str) -> Optional[Beatmap]:
    """
    Find a beatmap for a specific song file.

    Args:
        song_file: Name of the song file
        data_dir: Directory containing beatmaps

    Returns:
        Beatmap if found, None otherwise
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        return None

    song_name = Path(song_file).stem

    # Look for matching beatmap
    for beatmap_file in data_path.glob("*.beatmap.json"):
        beatmap = Beatmap.load(str(beatmap_file))
        if beatmap and (
            beatmap.song_file == song_file or
            Path(beatmap.song_file).stem == song_name
        ):
            return beatmap

    return None


def list_beatmaps(data_dir: str) -> list[Beatmap]:
    """
    List all beatmaps in a directory.

    Args:
        data_dir: Directory containing beatmaps

    Returns:
        List of Beatmap instances
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        return []

    beatmaps = []
    for beatmap_file in data_path.glob("*.beatmap.json"):
        beatmap = Beatmap.load(str(beatmap_file))
        if beatmap:
            beatmaps.append(beatmap)

    return beatmaps
