"""Settings data model and persistence."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Settings:
    """Game settings including calibration."""

    calibration_offset_ms: float = 0.0
    hit_tolerance_ms: float = 150.0

    def save(self, config_dir: str) -> str:
        """
        Save settings to a JSON file.

        Args:
            config_dir: Directory to save to

        Returns:
            Path to the saved file
        """
        dir_path = Path(config_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / "settings.json"

        with open(file_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

        return str(file_path)

    @classmethod
    def load(cls, config_dir: str) -> 'Settings':
        """
        Load settings from a JSON file.

        Args:
            config_dir: Directory containing settings

        Returns:
            Settings instance (defaults if file not found)
        """
        file_path = Path(config_dir) / "settings.json"

        if not file_path.exists():
            return cls()

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return cls(
                calibration_offset_ms=data.get("calibration_offset_ms", 0.0),
                hit_tolerance_ms=data.get("hit_tolerance_ms", 150.0),
            )
        except Exception:
            return cls()
