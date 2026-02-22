"""ASCII art definitions for game elements."""

from dataclasses import dataclass


@dataclass
class AsciiSprite:
    """An ASCII art sprite with dimensions."""
    lines: list[str]
    width: int
    height: int

    @classmethod
    def from_string(cls, art: str) -> 'AsciiSprite':
        """Create from a multiline string."""
        lines = art.strip('\n').split('\n')
        width = max(len(line) for line in lines) if lines else 0
        height = len(lines)
        # Pad lines to equal width
        lines = [line.ljust(width) for line in lines]
        return cls(lines=lines, width=width, height=height)


class AsciiArt:
    """Collection of ASCII art for the game."""

    # Bunny - stationary, ready to catch
    BUNNY = AsciiSprite.from_string(r"""
(\__/)
(o.o )
 > <
""")

    # Bunny - catching/jumping
    BUNNY_CATCH = AsciiSprite.from_string(r"""
(\__/)
(^.^ )
\> </
""")

    # Carrot
    CARROT = AsciiSprite.from_string(r"""
 ^^
/  \
""")

    # Small carrot (single line for tighter spacing)
    CARROT_SMALL = AsciiSprite.from_string(r"""
 /\
""")

    # Lane borders
    LANE_LEFT = '|'
    LANE_RIGHT = '|'
    LANE_FLOOR = '='

    # Title art
    TITLE = AsciiSprite.from_string(r"""
 __  __ ___ _   _  ___
|  \/  |_ _| \ | |/ _ \
| |\/| || ||  \| | | | |
| |  | || || |\  | |_| |
|_|  |_|___|_| \_|\___/
""")

    # Game over text
    GAME_OVER = AsciiSprite.from_string(r"""
  ____    _    __  __ _____    _____     _______ ____
 / ___|  / \  |  \/  | ____|  / _ \ \   / / ____|  _ \
| |  _  / _ \ | |\/| |  _|   | | | \ \ / /|  _| | |_) |
| |_| |/ ___ \| |  | | |___  | |_| |\ V / | |___|  _ <
 \____/_/   \_\_|  |_|_____|  \___/  \_/  |_____|_| \_\
""")

    # Success/cleared text
    SUCCESS = AsciiSprite.from_string(r"""
 ____  _   _  ____ ____ _____ ____ ____  _
/ ___|| | | |/ ___/ ___| ____/ ___/ ___|| |
\___ \| | | | |  | |   |  _| \___ \___ \| |
 ___) | |_| | |__| |___| |___ ___) |__) |_|
|____/ \___/ \____\____|_____|____/____/(_)
""")

    @classmethod
    def get_bunny(cls, catching: bool = False) -> AsciiSprite:
        """Get bunny sprite based on state."""
        return cls.BUNNY_CATCH if catching else cls.BUNNY

    @classmethod
    def get_carrot(cls, small: bool = False) -> AsciiSprite:
        """Get carrot sprite."""
        return cls.CARROT_SMALL if small else cls.CARROT
