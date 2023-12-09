from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple
from sprite import Actor

import exceptions

import random

if TYPE_CHECKING:
    from sprite import Actor
    from entity import Item

class Action:
    def __init__(self, sprite: Actor) -> None:
        super().__init__()
        self.sprite = sprite
        
    
    def perform(self) -> None:
        """Perform this action with the objects needed to determine its scope.

           `self.engine` is the scope this action is being performed in.

           `self.entity` is the object performing the action.

           This method must be overridden by Action subclasses. """
           
        raise NotImplementedError()
    

class PickupAction(Action):
    def __init__(self, sprite: Actor) -> None:
        super().__init__(sprite)
        
class ItemAction(Action):
    def __init__(
        self, sprite: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ) -> None:
        super().__init__(sprite)
        self.item = item
        if not target_xy:
            target_xy = sprite.x, sprite.y
        self.target_xy = target_xy
    
    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        if self.item.effect.consumable:
            self.item.effect.activate(self)
        
class DropItem(ItemAction):
    def __init__(self, sprite: Actor) -> None:
        super().__init__(sprite)
        
    def perform(self) -> None:
        self.sprite.entity.drop_inventory(self.item)
        
class EquipAction(Action):
    def __init__(self, sprite: Actor, item: Item):
        super().__init__(sprite)

        self.item = item

    def perform(self) -> None:
        self.sprite.entity.toggle_equip(self.item)
        
class WaitAction(Action):
    def perform(self) -> None:
        pass
    
class TakeStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs, if any exist at the entity's location.
        """
        pass

class ActionWithDirection(Action):
    def __init__(self, sprite: Actor, dx: int, dy: int):
        super().__init__(sprite)

        self.dx = dx
        self.dy = dy
        
    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this actions destination."""
        return NotImplementedError()

    @property
    def blocking_sprite(self) -> Optional[Actor]:
        """Return the blocking sprite at this actions destination."""
        return NotImplementedError()

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return NotImplementedError()
        
    def perform(self) -> None:
        raise NotImplementedError()

class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack.")
        
        dodge_chance = target.entity.dodge_chance
        if target.entity.DEX < self.sprite.entity.DEX - 2:
            dodge_chance /= 2
        elif target.entity.DEX > self.sprite.entity.DEX + 2:
            dodge_chance *= 2
            
        if random.random() > dodge_chance:
            damage = self.sprite.entity.phys_atk * (1 - target.entity.phys_negation) - target.entity.phys_defense
            
            attack_desc = f"{self.sprite.entity.name.capitalize()} attacks {target.entity.name}"
            
            if damage > 0:
                # TODO message: f"{attack_desc} for {damage} hit points."
                target.entity.take_damage(damage)
            else:
                # TODO message: f"{attack_desc} but does no damage."
                pass
            
class RangedAction(Action):
    def __init__(self, sprite: Actor, x, y) -> None:
        super().__init__(sprite)
        pass
            
class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy
            
        # Check for out of bounds.
        # Check for blocked by a tile.
        # Check for blocked by an entity.
        
        self.sprite.move(self.dx, self.dy)
        
class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.sprite, self.dx, self.dy).perform()
        else:
            return MovementAction(self.sprite, self.dx, self.dy).perform()