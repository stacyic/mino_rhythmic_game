"""File scanning utilities for discovering songs."""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class SongInfo:
    """Information about a discovered song."""
    file_path: str
    name: str
    has_beatmap: bool = False
    beatmap_path: Optional[str] = None


def scan_for_songs(
    directory: str,
    data_dir: str,
    extensions: tuple[str, ...] = ('.mp3', '.wav', '.flac', '.ogg'),
    exclude_names: tuple[str, ...] = ('calibration',)
) -> list[SongInfo]:
    """
    Scan a directory for audio files.

    Args:
        directory: Directory to scan
        data_dir: Directory containing beatmaps
        extensions: Audio file extensions to look for
        exclude_names: Song names to exclude (e.g., 'calibration')

    Returns:
        List of SongInfo objects
    """
    dir_path = Path(directory)
    data_path = Path(data_dir)

    if not dir_path.exists():
        return []

    songs = []

    for file_path in dir_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            song_name = file_path.stem

            # Skip excluded songs
            if song_name.lower() in [n.lower() for n in exclude_names]:
                continue

            # Check if beatmap exists
            beatmap_path = data_path / f"{song_name}.beatmap.json"
            has_beatmap = beatmap_path.exists()

            songs.append(SongInfo(
                file_path=str(file_path),
                name=song_name,
                has_beatmap=has_beatmap,
                beatmap_path=str(beatmap_path) if has_beatmap else None
            ))

    # Sort by name
    songs.sort(key=lambda s: s.name.lower())

    return songs


def get_song_display_name(file_path: str) -> str:
    """
    Get a display-friendly name for a song.

    Args:
        file_path: Path to the song file

    Returns:
        Display name
    """
    return Path(file_path).stem.replace('_', ' ').replace('-', ' ').title()
