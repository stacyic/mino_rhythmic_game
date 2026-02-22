"""Base scene class and scene manager."""

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.engine import GameEngine
    from ..core.input_handler import KeyEvent
    from ..ui.renderer import Renderer


class Scene(ABC):
    """Abstract base class for game scenes."""

    def __init__(self, engine: 'GameEngine'):
        self.engine = engine
        self._renderer: Optional['Renderer'] = None

    @property
    def renderer(self) -> 'Renderer':
        """Get the renderer, creating it if needed."""
        if self._renderer is None:
            from ..ui.renderer import Renderer
            self._renderer = Renderer(self.engine.stdscr)
        return self._renderer

    def enter(self) -> None:
        """Called when the scene becomes active."""
        pass

    def exit(self) -> None:
        """Called when leaving the scene."""
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Update scene logic.

        Args:
            dt: Delta time since last frame in seconds
        """
        pass

    @abstractmethod
    def render(self) -> None:
        """Render the scene."""
        pass

    @abstractmethod
    def handle_input(self, key_event: Optional['KeyEvent']) -> None:
        """
        Handle input events.

        Args:
            key_event: The key event or None if no input
        """
        pass


class SceneManager:
    """Manages scene transitions (alternative to engine-based management)."""

    def __init__(self):
        self._scenes: dict[str, Scene] = {}
        self._current_scene: Optional[Scene] = None
        self._current_name: str = ""

    def register(self, name: str, scene: Scene) -> None:
        """Register a scene with a name."""
        self._scenes[name] = scene

    def switch_to(self, name: str) -> bool:
        """
        Switch to a registered scene.

        Returns:
            True if switch was successful
        """
        if name not in self._scenes:
            return False

        if self._current_scene:
            self._current_scene.exit()

        self._current_scene = self._scenes[name]
        self._current_name = name
        self._current_scene.enter()
        return True

    @property
    def current(self) -> Optional[Scene]:
        """Get the current scene."""
        return self._current_scene
