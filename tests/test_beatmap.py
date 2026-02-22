"""Unit tests for beatmap model."""

import pytest
import json
import tempfile
from pathlib import Path
from src.models.beatmap import Beatmap, get_beatmap_for_song, list_beatmaps


class TestBeatmap:
    """Tests for Beatmap class."""

    def test_create_basic(self):
        """Test basic beatmap creation."""
        bm = Beatmap(song_file="test.mp3", bpm=120.0)
        assert bm.song_file == "test.mp3"
        assert bm.bpm == 120.0
        assert bm.beats == []
        assert bm.version == 1

    def test_create_with_beats(self):
        """Test creation with beats."""
        bm = Beatmap(
            song_file="test.mp3",
            bpm=120.0,
            beats=[0.0, 500.0, 1000.0]
        )
        assert bm.beats == [0.0, 500.0, 1000.0]

    def test_auto_name_from_song_file(self):
        """Test automatic name generation from song file."""
        bm = Beatmap(song_file="my_cool_song.mp3", bpm=120.0)
        assert bm.name == "my_cool_song"

    def test_custom_name(self):
        """Test custom name."""
        bm = Beatmap(song_file="test.mp3", bpm=120.0, name="Custom Name")
        assert bm.name == "Custom Name"

    def test_auto_created_at(self):
        """Test automatic created_at timestamp."""
        bm = Beatmap(song_file="test.mp3", bpm=120.0)
        assert bm.created_at != ""
        # Should be valid ISO format
        from datetime import datetime
        datetime.fromisoformat(bm.created_at)


class TestBeatmapBeats:
    """Tests for beat manipulation."""

    def test_add_beat(self):
        """Test adding a beat."""
        bm = Beatmap(song_file="test.mp3", bpm=120.0)
        bm.add_beat(500.0)
        assert bm.beats == [500.0]

    def test_add_multiple_beats(self):
        """Test adding multiple beats."""
        bm = Beatmap(song_file="test.mp3", bpm=120.0)
        bm.add_beat(1000.0)
        bm.add_beat(500.0)
        bm.add_beat(1500.0)
        # Should be sorted
        assert bm.beats == [500.0, 1000.0, 1500.0]

    def test_add_beat_maintains_sort(self):
        """Test that beats remain sorted after adding."""
        bm = Beatmap(song_file="test.mp3", bpm=120.0, beats=[0.0, 1000.0])
        bm.add_beat(500.0)
        assert bm.beats == [0.0, 500.0, 1000.0]

    def test_remove_beat_exact(self):
        """Test removing a beat with exact match."""
        bm = Beatmap(
            song_file="test.mp3", bpm=120.0,
            beats=[0.0, 500.0, 1000.0]
        )
        result = bm.remove_beat(500.0)
        assert result is True
        assert bm.beats == [0.0, 1000.0]

    def test_remove_beat_within_tolerance(self):
        """Test removing a beat within tolerance."""
        bm = Beatmap(
            song_file="test.mp3", bpm=120.0,
            beats=[0.0, 500.0, 1000.0]
        )
        result = bm.remove_beat(510.0, tolerance_ms=50.0)
        assert result is True
        assert bm.beats == [0.0, 1000.0]

    def test_remove_beat_outside_tolerance(self):
        """Test that beat outside tolerance is not removed."""
        bm = Beatmap(
            song_file="test.mp3", bpm=120.0,
            beats=[0.0, 500.0, 1000.0]
        )
        result = bm.remove_beat(600.0, tolerance_ms=50.0)
        assert result is False
        assert bm.beats == [0.0, 500.0, 1000.0]

    def test_remove_nonexistent_beat(self):
        """Test removing a beat that doesn't exist."""
        bm = Beatmap(
            song_file="test.mp3", bpm=120.0,
            beats=[0.0, 500.0, 1000.0]
        )
        result = bm.remove_beat(2000.0)
        assert result is False


class TestBeatmapRangeQueries:
    """Tests for beat range queries."""

    def test_get_beats_in_range(self):
        """Test getting beats within a range."""
        bm = Beatmap(
            song_file="test.mp3", bpm=120.0,
            beats=[0.0, 500.0, 1000.0, 1500.0, 2000.0]
        )
        result = bm.get_beats_in_range(400.0, 1100.0)
        assert result == [(1, 500.0), (2, 1000.0)]

    def test_get_beats_in_range_inclusive(self):
        """Test that range is inclusive on both ends."""
        bm = Beatmap(
            song_file="test.mp3", bpm=120.0,
            beats=[500.0, 1000.0, 1500.0]
        )
        result = bm.get_beats_in_range(500.0, 1500.0)
        assert len(result) == 3

    def test_get_beats_in_range_empty(self):
        """Test range with no beats."""
        bm = Beatmap(
            song_file="test.mp3", bpm=120.0,
            beats=[500.0, 2000.0]
        )
        result = bm.get_beats_in_range(600.0, 1900.0)
        assert result == []


class TestBeatmapSerialization:
    """Tests for beatmap serialization."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        bm = Beatmap(
            song_file="test.mp3",
            bpm=120.0,
            beats=[0.0, 500.0, 1000.0],
            name="Test Song",
            version=1
        )
        data = bm.to_dict()

        assert data["song_file"] == "test.mp3"
        assert data["bpm"] == 120.0
        assert data["beats"] == [0.0, 500.0, 1000.0]
        assert data["name"] == "Test Song"
        assert data["version"] == 1
        assert "created_at" in data

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "song_file": "test.mp3",
            "bpm": 120.0,
            "beats": [0.0, 500.0, 1000.0],
            "name": "Test Song",
            "version": 1,
            "created_at": "2024-01-01T00:00:00"
        }
        bm = Beatmap.from_dict(data)

        assert bm.song_file == "test.mp3"
        assert bm.bpm == 120.0
        assert bm.beats == [0.0, 500.0, 1000.0]
        assert bm.name == "Test Song"

    def test_from_dict_minimal(self):
        """Test creation from minimal dictionary."""
        data = {
            "song_file": "test.mp3",
            "bpm": 120.0
        }
        bm = Beatmap.from_dict(data)

        assert bm.song_file == "test.mp3"
        assert bm.bpm == 120.0
        assert bm.beats == []

    def test_roundtrip(self):
        """Test serialization roundtrip."""
        original = Beatmap(
            song_file="test.mp3",
            bpm=120.0,
            beats=[0.0, 500.0, 1000.0, 1500.0]
        )
        data = original.to_dict()
        restored = Beatmap.from_dict(data)

        assert restored.song_file == original.song_file
        assert restored.bpm == original.bpm
        assert restored.beats == original.beats
        assert restored.name == original.name


class TestBeatmapPersistence:
    """Tests for beatmap file persistence."""

    def test_save_and_load(self):
        """Test saving and loading a beatmap."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bm = Beatmap(
                song_file="test.mp3",
                bpm=120.0,
                beats=[0.0, 500.0, 1000.0],
                name="test"
            )

            # Save
            path = bm.save(tmpdir)
            assert Path(path).exists()

            # Load
            loaded = Beatmap.load(path)
            assert loaded is not None
            assert loaded.song_file == bm.song_file
            assert loaded.bpm == bm.bpm
            assert loaded.beats == bm.beats

    def test_save_creates_directory(self):
        """Test that save creates directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "nested" / "path"

            bm = Beatmap(song_file="test.mp3", bpm=120.0, name="test")
            path = bm.save(str(nested_dir))

            assert Path(path).exists()

    def test_load_nonexistent(self):
        """Test loading a nonexistent file."""
        result = Beatmap.load("/nonexistent/path/file.json")
        assert result is None

    def test_load_invalid_json(self):
        """Test loading invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            f.flush()

            result = Beatmap.load(f.name)
            assert result is None

    def test_file_naming(self):
        """Test that files are named correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bm = Beatmap(song_file="test.mp3", bpm=120.0, name="My Song")
            path = bm.save(tmpdir)

            assert "My Song.beatmap.json" in path


class TestBeatmapDiscovery:
    """Tests for beatmap discovery functions."""

    def test_get_beatmap_for_song_found(self):
        """Test finding a beatmap for a song."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bm = Beatmap(song_file="test.mp3", bpm=120.0)
            bm.save(tmpdir)

            result = get_beatmap_for_song("test.mp3", tmpdir)
            assert result is not None
            assert result.song_file == "test.mp3"

    def test_get_beatmap_for_song_not_found(self):
        """Test when no beatmap exists for a song."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_beatmap_for_song("nonexistent.mp3", tmpdir)
            assert result is None

    def test_get_beatmap_for_song_matches_stem(self):
        """Test matching by filename stem."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bm = Beatmap(song_file="test.mp3", bpm=120.0, name="test")
            bm.save(tmpdir)

            # Should match even with different path
            result = get_beatmap_for_song("/some/path/test.mp3", tmpdir)
            assert result is not None

    def test_list_beatmaps_empty(self):
        """Test listing beatmaps in empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = list_beatmaps(tmpdir)
            assert result == []

    def test_list_beatmaps_multiple(self):
        """Test listing multiple beatmaps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bm1 = Beatmap(song_file="song1.mp3", bpm=120.0, name="song1")
            bm2 = Beatmap(song_file="song2.mp3", bpm=140.0, name="song2")
            bm1.save(tmpdir)
            bm2.save(tmpdir)

            result = list_beatmaps(tmpdir)
            assert len(result) == 2

    def test_list_beatmaps_nonexistent_dir(self):
        """Test listing beatmaps in nonexistent directory."""
        result = list_beatmaps("/nonexistent/path")
        assert result == []


class TestBeatmapEdgeCases:
    """Edge case tests for beatmap model."""

    def test_duplicate_beats(self):
        """Test handling of duplicate beats."""
        bm = Beatmap(
            song_file="test.mp3", bpm=120.0,
            beats=[500.0, 500.0, 1000.0]
        )
        # Duplicates are preserved (quantization handles this)
        assert bm.beats == [500.0, 500.0, 1000.0]

    def test_negative_beats(self):
        """Test handling of negative beat times."""
        bm = Beatmap(song_file="test.mp3", bpm=120.0)
        bm.add_beat(-100.0)
        bm.add_beat(500.0)
        assert bm.beats == [-100.0, 500.0]

    def test_very_high_bpm(self):
        """Test with very high BPM."""
        bm = Beatmap(song_file="test.mp3", bpm=300.0)
        assert bm.bpm == 300.0

    def test_very_low_bpm(self):
        """Test with very low BPM."""
        bm = Beatmap(song_file="test.mp3", bpm=30.0)
        assert bm.bpm == 30.0

    def test_many_beats(self):
        """Test with many beats."""
        beats = [i * 100.0 for i in range(1000)]
        bm = Beatmap(song_file="test.mp3", bpm=120.0, beats=beats)
        assert len(bm.beats) == 1000

    def test_unicode_name(self):
        """Test with unicode characters in name."""
        bm = Beatmap(song_file="test.mp3", bpm=120.0, name="Test")
        assert bm.name == "Test"

        with tempfile.TemporaryDirectory() as tmpdir:
            path = bm.save(tmpdir)
            loaded = Beatmap.load(path)
            assert loaded is not None
