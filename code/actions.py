from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple, List

import color, exceptions

if TYPE_CHECKING:
    from engine import Engine
    from sprite import Sprite, Actor
    from entity import Item
    from entity_effect import BaseEffect, ItemEffect

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
    
class PickupAction(Action):
    """ Pickup an item and add it to the inventory. """
    
    def __init__(self, sprite: Actor):
        super().__init__(sprite)
        
    def perform(self) -> None:
        actor_location_x, actor_location_y = self.sprite.x, self.sprite.y
        
        items_at_loc: list[Sprite] = []
        
        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                items_at_loc.append(item)
                
        if not items_at_loc:
            raise exceptions.Impossible("There is nothing here to pick up.")
        
        if len(items_at_loc) > 1:
            from input_handler import MultiPickupHandler
            self.engine.event_handler = MultiPickupHandler(self.engine, items_at_loc, self.sprite)
            return

        result = self.sprite.entity.add_inventory(items_at_loc[0].entity)
        if not result:
            self.engine.game_map.sprites.remove(items_at_loc[0])
            return
        self.engine.message_log.add_message(result.args[0], color.impossible)

class DropItem(Action):
    def __init__(self, sprite: Actor, item: Item | List[Item]):
        super().__init__(sprite)
        if not isinstance(item, List):
            item = [item]
        self.items = item
        
    def perform(self) -> None:
        for item in self.items:
            self.sprite.entity.drop_inventory(item)

class EffectAction(Action):
    def __init__(
        self, sprite: Sprite, effect: BaseEffect, target_xy: Optional[Tuple[int, int]] = None
    ) -> None:
        super().__init__(sprite)
        self.effect = effect
        if not target_xy:
            target_xy = sprite.x, sprite.y
        self.target_xy = target_xy
        
    @property
    def target_actor(self) -> Optional[Actor]:
        """ Returns the actor at this actions destination. """
        return self.engine.game_map.get_actor_at_location(*self.target_xy)
    
    def perform(self) -> None:
        """ Invoke the effect ability, this action will be given to provide context."""
        self.effect.activate(self)
        
class EatAction(EffectAction):
    def __init__(
        self, sprite: Sprite, effect: ItemEffect
    ) -> None:
        super().__init__(sprite, effect, None)
    
    def perform(self) -> None:
        """ Invoke the effect ability, this action will be given to provide context."""
        self.effect: ItemEffect
        from entity_effect import CorpseEffect
        
        if isinstance(self.effect, CorpseEffect):
            if self.sprite.entity.race.name == self.effect.parent.dead_character.race.name:
                self.sprite.entity.tags.add('cannibal')
            if self.effect.parent.dead_character.INT > 7:
                self.sprite.entity.tags.add('sophant eater')
        
        self.effect.eat(self)
        
        self.engine.message_log.add_message(f'{self.sprite.name} ate {self.effect.parent.name}.')

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
            raise exceptions.Impossible('Nothing to attack.')
        attack_desc = f'{self.sprite.entity.name.capitalize()} attacks {target.entity.name}'
        if self.sprite is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk
        
        damage_taken = target.entity.take_damage(self.sprite.entity.phys_atk, attacker=self.sprite.entity)
        if damage_taken is None:
            self.engine.message_log.add_message(
                f'{attack_desc} but misses.', attack_color
            )
        elif damage_taken > 0:
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
            # Destination is out of bounds.
            raise exceptions.Impossible('That way is blocked')
        if not self.engine.game_map.tiles['walkable'][dest_x, dest_y]:
            # Destination is blocked by tile.
            raise exceptions.Impossible('That way is blocked')
        if self.engine.game_map.get_blocking_sprite_at_location(dest_x, dest_y):
            # Destination is blocked by an entity.
            raise exceptions.Impossible('That way is blocked')
        
        self.sprite.move(self.dx, self.dy)
        
class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.sprite, self.dx, self.dy).perform()
        else:
            return MovementAction(self.sprite, self.dx, self.dy).perform()
        