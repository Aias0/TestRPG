from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from engine import Engine
    from sprite import Sprite, Actor
    from entity import Character

class Action:
    def __init__(self, sprite: Sprite) -> None:
        self.sprite = sprite
        
    @property
    def engine(self) -> Engine:
        """ Return the engine this action belongs to. """
        return self.sprite.gamemap.engine
    
    def perform(self) -> None:
        """Perform this action with the objects needed to determine its scope.

        `self.engine` is the scope this action is being performed in.

        `self.entity` is the object performing the action.

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()

class EscapeAction(Action):
    def perform(self) -> None:
        raise SystemExit()
    
class WaitAction(Action):
    def perform(self) -> None:
        pass

class ActionWithDirection(Action):
    def __init__(self, sprite: Sprite, dx: int, dy: int):
        super().__init__(sprite)
        
        self.dx = dx
        self.dy = dy
        
    @property
    def dest_xy(self) -> Tuple[int, int]:
        """ Returns this actions destination. """
        return self.sprite.x + self.dx, self.sprite.y + self.dy
    
    @property
    def blocking_sprite(self) -> Optional[Sprite]:
        """Return the blocking entity at this actions destination."""
        return self.engine.game_map.get_blocking_sprite_at_location(*self.dest_xy)
    
    @property
    def target_actor(self) -> Optional[Actor]:
        """ Return the actor at this actions destination. """
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)
    
    def perform(self) -> None:
        raise NotImplementedError()
    
class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            return # No entity to attack.
        character: Character = target.entity
        print(f"You kick {character.name}, much to {character.pronouns[character.gender][2]} annoyance!")

class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy
        
        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            return # Destination is out of bounds.
        if not self.engine.game_map.tiles['walkable'][dest_x, dest_y]:
            return ## Destination is blocked by tile.
        if self.engine.game_map.get_blocking_sprite_at_location(dest_x, dest_y):
            return # Destination is blocked by an entity.
        
        self.sprite.move(self.dx, self.dy)
        
class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.sprite, self.dx, self.dy).perform()
        else:
            return MovementAction(self.sprite, self.dx, self.dy).perform()
        