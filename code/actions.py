from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

import random, color

if TYPE_CHECKING:
    from engine import Engine
    from sprite import Sprite, Actor
    from entity import Character

class Action:
    def __init__(self, sprite: Actor) -> None:
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
    def __init__(self, sprite: Actor, dx: int, dy: int):
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
        attack_desc = f'{self.sprite.entity.name.capitalize()} attacks {target.entity.name}'
        if self.sprite is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk
        
        dodge_chance = target.entity.dodge_chance
        if target.entity.DEX < self.sprite.entity.DEX - 2:
            dodge_chance /= 2
        elif target.entity.DEX > self.sprite.entity.DEX + 2:
            dodge_chance *= 2

        damage = self.sprite.entity.phys_atk * (1 - target.entity.phys_negation) - target.entity.phys_defense
        rand = random.random()+self.sprite.entity.LCK/100
        if rand < dodge_chance/2:
            print(f'{attack_desc} but misses.')
            return
        elif rand < dodge_chance:
            damage //= 2
        damage_taken = target.entity.take_damage(damage)
        if damage_taken > 0:
            self.engine.message_log.add_message(
                f'{attack_desc} for {damage_taken} hit points.', attack_color
                )
        else:
            self.engine.message_log.add_message(
                f'{attack_desc} but does no damage.', attack_color
                )
        

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
        