from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Optional

import color, actions

from exceptions import Impossible
from game_types import DamageTypes, MagicFocusTypes, GameTypeNames, ElementTypes, ItemTypes

from input_handler import RangedAttackHandler

from values import LockValues

if TYPE_CHECKING:
    from entity import Character
    from sprite import Actor
    from engine import Engine

class Spell():
    def __init__(self, name: str, cost: int, range: int, activation_time: int, color: Tuple[int, int, int], duration: int = 0, element: ElementTypes = ElementTypes.NONE, req_focus_type: MagicFocusTypes | None = None) -> None:
        """ `activation_time` turns needed to cast spell. 0 is instant.\n\n`duration` turns spell is active for. 0 is forever"""
        self.name = name
        self.cost = cost
        self.range = range
        self.element = element
        self.activation_time = activation_time
        self.duration = duration
        self.color = color
        self.req_focus_type = req_focus_type
        
        self.damage_mult = 1
        
    def check_cast_conditions(self, caster: Character, target: Optional[Tuple[int, int]], scroll_cast: bool = False) -> None:
        cost = self.cost
        if scroll_cast:
            cost = int(self.cost*.75)
        else:
            equip_in_dom_hand_itemtypes = None
            if caster.dominant_hand == 'ambidextrous':
                if caster.equipment['Right Hand']:
                    equip_in_dom_hand_itemtypes = caster.equipment['Right Hand'].itemsubtypes
                if caster.equipment['Left Hand'] and equip_in_dom_hand_itemtypes is None and not any(map(lambda x: isinstance(x, MagicFocusTypes), equip_in_dom_hand_itemtypes)):
                    equip_in_dom_hand_itemtypes = caster.equipment['Left Hand'].itemsubtypes
            elif caster.equipment[f'{caster.dominant_hand.capitalize()} Hand']:
                equip_in_dom_hand_itemtypes = caster.equipment[f'{caster.dominant_hand.capitalize()} Hand'].itemsubtypes
            if self.req_focus_type and not [item for item in caster.equipment.values() if self.req_focus_type in item.itemsubtypes]:
                raise Impossible(f'{self.name} not cast. {caster.name} does not have correct focus[{GameTypeNames.magicfocustypes_to_name[self.req_focus_type]}].')
            elif equip_in_dom_hand_itemtypes and any(map(lambda x: isinstance(x, MagicFocusTypes), equip_in_dom_hand_itemtypes)):
                if MagicFocusTypes.EFFICIENCY in equip_in_dom_hand_itemtypes:
                    cost = int(self.cost*.75)
                    self.damage_mult = .75
                if MagicFocusTypes.POWER in equip_in_dom_hand_itemtypes:
                    cost = int(self.cost*1.25)
                    self.damage_mult = 1.25
            else:
                for item in caster.equipment.values():
                    if item is None:
                        continue
                    if item.itemsubtypes and any(map(lambda x: isinstance(x, MagicFocusTypes), item.itemsubtypes)):
                        if equip_in_dom_hand_itemtypes and MagicFocusTypes.EFFICIENCY in equip_in_dom_hand_itemtypes:
                            cost = int(self.cost*.75)
                        if equip_in_dom_hand_itemtypes and  MagicFocusTypes.POWER in equip_in_dom_hand_itemtypes:
                            cost = int(self.cost*1.25)
                        break
        
        if caster.mp - cost < 0:
            raise Impossible(f'Not enough mana to cast. [{cost}>{caster.mp}]')
        
        return cost
    
    def cast(self, caster: Character, target: Optional[Tuple[int, int]], scroll_cast: bool = False, message: str = None) -> None:
        cost = self.check_cast_conditions(caster=caster, target=target, scroll_cast=scroll_cast)
        caster.mp-=cost
        caster.engine.message_log.add_message(message)
    
    def get_action(self, engine: Engine) -> actions.Action:
        engine.message_log.add_message(
            "Select a target location.", color.prompt_player
        )
        engine.event_handler = RangedAttackHandler(
            engine,
            callback=lambda xy: actions.MagicAction(engine.player, self, xy),
            spell=self
        )
        return None
        
        
    def similar(self, other) -> bool:
        if isinstance(other, self.__class__):
            for i, pair in enumerate(zip([_[1] for _ in vars(self).items() if _[0] != 'parent' and _[0] != 'dead_character'], [_[1] for _ in vars(other).items() if _[0] != 'parent' and _[0] != 'dead_character'])):
                if hasattr(pair[0], 'similar') and not pair[0].similar(pair[1]):
                    return False
                elif not hasattr(pair[0], 'similar') and pair[0] != pair[1]:
                    return False
            return True
        return False

class AttackSpell(Spell):
    def __init__(self, name: str, cost: int, damage: int, range: int, element: ElementTypes, activation_time: int, color: Tuple[int, int, int], req_focus_type: MagicFocusTypes | None = None) -> None:
        """ `activation_time` turns needed to cast spell. 0 is instant."""
        super().__init__(
            name=name,
            cost=cost,
            range=range,
            element=element,
            activation_time=activation_time,
            color=color,
            req_focus_type=req_focus_type,
        )
        
        self.damage = damage
        
    def check_cast_conditions(self, caster: Character, target: Optional[Tuple[int, int]], scroll_cast: bool = False) -> None:
        cost = super().check_cast_conditions(caster, target, scroll_cast)
        
        if target is None:
            raise Impossible(f'{self.name} not cast. Has no target.')
        if caster.parent.distance(*target) > self.range:
            raise Impossible(f'{self.name} not cast. Target out of range.')
        if not caster.engine.game_map.visible[target]:
            raise Impossible("You cannot target an area that you cannot see.")
        
        target_actor = caster.engine.game_map.get_actor_at_location(*target)
        if target_actor is None:
            raise Impossible(f'{self.name} not cast. No actor at location.')
        
        return cost
        
    def cast(self, caster: Character, target: Optional[Tuple[int, int]], scroll_cast: bool = False, hit_message: str = None, miss_message: str = None) -> None:
        cost = self.check_cast_conditions(caster=caster, target=target, scroll_cast=scroll_cast)
        target_actor = caster.engine.game_map.get_actor_at_location(*target)
        
        caster.mp-=cost
        
        damage_taken = target_actor.entity.take_damage(int(self.damage*self.damage_mult), DamageTypes.MAGC, self.element, caster)
        if damage_taken is None:
            caster.engine.message_log.add_message(miss_message.replace('ACTOR', str(target_actor.name)).replace('DAMAGE', str(damage_taken)), color.red)
        else:
            caster.engine.message_log.add_message(hit_message.replace('ACTOR', str(target_actor.name)).replace('DAMAGE', str(damage_taken)), color.player_atk)

class AOESpell(AttackSpell):
    def __init__(self, name: str, cost: int, damage: int, range: int, radius: int, element: ElementTypes, activation_time: int, color: Tuple[int, int, int]) -> None:
        """ `activation_time` turns needed to cast spell. 0 is instant. """
        super().__init__(
            name = name,
            cost = cost,
            damage = damage,
            range = range,
            element=element,
            activation_time = activation_time,
            color=color
        )
        self.radius = radius
    
    def check_cast_conditions(self, caster: Character, target: Tuple[int, int] | None, scroll_cast: bool = False) -> int:
        """ Returns spell cost. """
        cost = self.cost
        if scroll_cast:
            cost = int(self.cost*.75)
        else:
            equip_in_dom_hand_itemtypes = None
            if caster.dominant_hand == 'ambidextrous':
                if caster.equipment['Right Hand']:
                    equip_in_dom_hand_itemtypes = caster.equipment['Right Hand'].itemsubtypes
                if caster.equipment['Left Hand'] and equip_in_dom_hand_itemtypes is None and not any(map(lambda x: isinstance(x, MagicFocusTypes), equip_in_dom_hand_itemtypes)):
                    equip_in_dom_hand_itemtypes = caster.equipment['Left Hand'].itemsubtypes
            elif caster.equipment[f'{caster.dominant_hand.capitalize()} Hand']:
                equip_in_dom_hand_itemtypes = caster.equipment[f'{caster.dominant_hand.capitalize()} Hand'].itemsubtypes
            if self.req_focus_type and not [item for item in caster.equipment.values() if self.req_focus_type in item.itemsubtypes]:
                raise Impossible(f'{self.name} not cast. {caster.name} does not have correct focus[{GameTypeNames.magicfocustypes_to_name[self.req_focus_type]}].')
            elif any(map(lambda x: isinstance(x, MagicFocusTypes), equip_in_dom_hand_itemtypes)):
                if MagicFocusTypes.EFFICIENCY in equip_in_dom_hand_itemtypes:
                    cost = int(self.cost*.75)
                    self.damage_mult = .75
                if MagicFocusTypes.POWER in equip_in_dom_hand_itemtypes:
                    cost = int(self.cost*1.25)
                    self.damage_mult = 1.25
            else:
                for item in caster.equipment.values():
                    if item is None:
                        continue
                    if item.itemsubtypes and any(map(lambda x: isinstance(x, MagicFocusTypes), item.itemsubtypes)):
                        if equip_in_dom_hand_itemtypes and MagicFocusTypes.EFFICIENCY in equip_in_dom_hand_itemtypes:
                            cost = int(self.cost*.75)
                        if equip_in_dom_hand_itemtypes and MagicFocusTypes.POWER in equip_in_dom_hand_itemtypes:
                            cost = int(self.cost*1.25)
                        break
        
        target_actors = caster.engine.game_map.get_actors_in_range(*target, self.radius)
        if not target_actors:
            raise Impossible(f'{self.name} not cast. No actors at location.')
        
        if caster.mp - cost < 0:
            raise Impossible(f'Not enough mana to cast. [{cost}>{caster.mp}]')
        
        return cost
        
    def cast(self, caster: Character, target: Tuple[int, int] | None, scroll_cast: bool = False, hit_message: str = None, miss_message: str = None) -> None:
        cost = self.check_cast_conditions(caster=caster, target=target, scroll_cast=scroll_cast)
        target_actors: list[Actor] = caster.engine.game_map.get_actors_in_range(*target, self.radius)
        
        caster.mp -= cost
        
        for actor in target_actors:
            damage_taken = actor.entity.take_damage(int(self.damage*self.damage_mult), DamageTypes.MAGC, self.element, caster)
            if damage_taken is None:
                caster.engine.message_log.add_message(miss_message.replace('ACTOR', str(actor.name)).replace('DAMAGE', str(damage_taken)), color.red)
            else:
                caster.engine.message_log.add_message(hit_message.replace('ACTOR', str(actor.name)).replace('DAMAGE', str(damage_taken)), color.player_atk)
    
class LightningBolt(AttackSpell):
    def __init__(self) -> None:
        super().__init__(name='Lightning Bolt', cost=5, damage=18, range=15, element=ElementTypes.LIGHTNING, activation_time=0, color=[0, 0, 255])
        
    def cast(self, caster: Character, target: Optional[Tuple[int, int]], scroll_cast: bool = False) -> None:
        super().cast(
            caster=caster,
            target=target,
            scroll_cast=scroll_cast,
            hit_message=f"A lighting bolt strikes the ACTOR with a loud thunder, for DAMAGE damage!",
            miss_message=f"ACTOR dodges the lighting bolt!"
        )
        
class FireBall(AOESpell):
    def __init__(self) -> None:
        super().__init__(name='Fire Ball', cost=10, damage=18, range=15, element=ElementTypes.FIRE, radius= 3, activation_time=0, color=[255, 0, 0])
        
    def cast(self, caster: Character, target: Optional[Tuple[int, int]], scroll_cast: bool = False) -> None:
        super().cast(
            caster=caster,
            target=target,
            scroll_cast=scroll_cast,
            hit_message=f"A fire ball strikes the ACTOR with a roaring blast, for DAMAGE damage!",
            miss_message=f"ACTOR dodges the fire ball!"
        )
        
class FireBolt(AttackSpell):
    def __init__(self) -> None:
        super().__init__(name='Fire Bolt', cost=2, damage=10, range=15, element=ElementTypes.FIRE, activation_time=0, color=[255, 0, 0])
        
    def cast(self, caster: Character, target: Optional[Tuple[int, int]], scroll_cast: bool = False) -> None:
        super().cast(
            caster=caster,
            target=target,
            scroll_cast=scroll_cast,
            hit_message=f"A fire bolt strikes the ACTOR with a loud blast, for DAMAGE damage!",
            miss_message=f"ACTOR dodges the fire bolt!"
        )

class ArcaneLock(Spell):
    def __init__(self) -> None:
        super().__init__(name='Arcane Lock', cost=4, range=5, activation_time=0, color=(80, 201, 217))
        
    def cast(self, caster: Character, target: Optional[Tuple[int, int]], scroll_cast: bool = False) -> None:
        from entity import Door, Item
        from entity_effect import KeyEffect
        cost = self.check_cast_conditions(caster=caster, target=target, scroll_cast=scroll_cast)
        
        target_sprite = caster.engine.game_map.get_sprite_at_location(*target)
        
        
        if not target_sprite:
            raise Impossible(f'{self.name} not cast. Has no target.')
        door = target_sprite.entity
        if not isinstance(door, Door):
            raise Impossible(f'{self.name} not cast. Target is not a door.')
        
        caster.mp-=cost
        try:
            door.lock(LockValues.lock_vals['ARCANE_LOCK'])
        except Impossible as e:
            if str(e) == 'Door already locked':
                caster.engine.message_log.add_message('Arcane Lock failed as the door was already locked.')
            else:
                raise Exception('Error occurred in arcane lock spell while trying to lock door.')
        caster.add_inventory(
            Item(
                'Arcane Key',
                0,
                0,
                description='Crafted from ethereal energies and adorned with intricate arcane patterns, this key emits a subtle glow.\n\nThis can be used to open an Arcane Lock.',
                itemtype=ItemTypes.KEY,
                effect=KeyEffect(LockValues.lock_vals['ARCANE_LOCK'], True),
                color=self.color,
            ),
            True
        )
        
        caster.engine.message_log.add_message('Door locked with Arcane Lock.')

SPELLS = [LightningBolt(), FireBall(), FireBolt(), ArcaneLock()]