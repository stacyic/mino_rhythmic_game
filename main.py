#!/usr/bin/env python3
"""
Mino - A Terminal Rhythm Game

A rhythm game where you help a bunny catch falling carrots!

Setup:
    # Install system dependencies (macOS)
    brew install libsndfile ffmpeg

    # Create virtual environment and install Python dependencies
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

Usage:
    source venv/bin/activate
    python main.py
"""

import curses
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.engine import GameEngine
from src.scenes.menu import MenuScene


def main(stdscr: curses.window) -> None:
    """Main game entry point."""
    # Setup curses
    curses.curs_set(0)  # Hide cursor

    # Create engine and run
    engine = GameEngine(stdscr)
    initial_scene = MenuScene(engine)

    try:
        engine.run(initial_scene)
    except KeyboardInterrupt:
        pass


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    missing = []

    try:
        import sounddevice
    except ImportError:
        missing.append("sounddevice")

    try:
        import soundfile
    except ImportError:
        missing.append("soundfile")

    try:
        import numpy
    except ImportError:
        missing.append("numpy")

    if missing:
        print("Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall with: pip install -r requirements.txt")
        print("\nAlso ensure system dependencies are installed:")
        print("  brew install libsndfile ffmpeg")
        return False

    return True


if __name__ == "__main__":
    if not check_dependencies():
        sys.exit(1)

    # Ensure config and data directories exist
    base_dir = Path(__file__).parent
    (base_dir / "config").mkdir(exist_ok=True)
    (base_dir / "data").mkdir(exist_ok=True)

    # Run the game
    curses.wrapper(main)
