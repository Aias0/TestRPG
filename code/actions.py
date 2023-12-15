from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from sprite import Sprite

class Action:
    def perform(self, engine: Engine, sprite: Sprite) -> None:
        """Perform this action with the objects needed to determine its scope.

        `engine` is the scope this action is being performed in.

        `entity` is the object performing the action.

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()

class EscapeAction(Action):
    def perform(self, engine: Engine, sprite: Sprite) -> None:
        raise SystemExit()

class MovementAction(Action):
    def __init__(self, dx: int, dy: int) -> None:
        self.dx = dx
        self.dy = dy
        
    def perform(self, engine: Engine, sprite: Sprite) -> None:
        dest_x = sprite.x + self.dx
        dest_y = sprite.y + self.dy
        
        if not engine.game_map.in_bounds(dest_x, dest_y):
            return # Destination is out of bounds.
        if not engine.game_map.tiles['walkable'][dest_x, dest_y]:
            return ## Destination is blocked by tile.
        
        sprite.move(self.dx, self.dy)