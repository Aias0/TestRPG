from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Optional

import color

from exceptions import Impossible
from game_types import DamageTypes, MagicFocusTypes, GameTypeNames, ElementTypes

if TYPE_CHECKING:
    from entity import Character
    from sprite import Actor

class Spell():
    def __init__(self, name: str, cost: int, damage: int, range: int, activation_time: int, color: Tuple[int, int, int], req_focus_type: MagicFocusTypes | None = None) -> None:
        """ `activation_time` turns needed to cast spell. 0 is instant."""
        self.name = name
        self.cost = cost
        self.damage = damage
        self.range = range
        self.activation_time = activation_time
        self.color = color
        self.req_focus_type = req_focus_type
        
        self.damage_mult = 1
        
    def check_cast_conditions(self, caster: Character, target: Optional[Tuple[int, int]], scroll_cast: bool = False):
        cost = self.cost
        if scroll_cast:
            cost = int(self.cost*.75)
        else:
            if self.req_focus_type and not [item for item in caster.equipment.values() if self.req_focus_type in item.itemsubtypes]:
                raise Impossible(f'{self.name} not cast. {caster.name} does not have correct focus[{GameTypeNames.magicfocustypes_to_name[self.req_focus_type]}].')
            elif any(map(lambda x: isinstance(x, MagicFocusTypes), caster.equipment[caster.dominant_hand].itemsubtypes)):
                if MagicFocusTypes.EFFICIENCY in caster.equipment[caster.dominant_hand].itemsubtypes:
                    cost = int(self.cost*.75)
                    self.damage_mult = .75
                if MagicFocusTypes.POWER in caster.equipment[caster.dominant_hand].itemsubtypes:
                    cost = int(self.cost*1.25)
                    self.damage_mult = 1.25
            else:
                for item in caster.equipment.values():
                    if any(map(lambda x: isinstance(x, MagicFocusTypes), item.itemsubtypes)):
                        if MagicFocusTypes.EFFICIENCY in caster.equipment[caster.dominant_hand].itemsubtypes:
                            cost = int(self.cost*.75)
                        if MagicFocusTypes.POWER in caster.equipment[caster.dominant_hand].itemsubtypes:
                            cost = int(self.cost*1.25)
                        break
                
            
        if target is None:
            raise Impossible(f'{self.name} not cast. Has no target.')
        if caster.parent.distance(*target) > self.range:
            raise Impossible(f'{self.name} not cast. Target out of range.')
        if not caster.engine.game_map.visible[target]:
            raise Impossible("You cannot target an area that you cannot see.")
        
        target_actor = caster.engine.game_map.get_actor_at_location(*target)
        if target_actor is None:
            raise Impossible(f'{self.name} not cast. No actor at location.')
        
        if caster.mp - cost < 0:
            raise Impossible(f'Not enough mana to cast. [{cost}>{caster.mp}]')
        
    def cast(self, caster: Character, target: Optional[Tuple[int, int]], scroll_cast: bool = False) -> None:
        raise NotImplementedError()
    
    def similar(self, other) -> bool:
        if isinstance(other, self.__class__):
            for i, pair in enumerate(zip([_[1] for _ in vars(self).items() if _[0] != 'parent' and _[0] != 'dead_character'], [_[1] for _ in vars(other).items() if _[0] != 'parent' and _[0] != 'dead_character'])):
                if hasattr(pair[0], 'similar') and not pair[0].similar(pair[1]):
                    return False
                elif not hasattr(pair[0], 'similar') and pair[0] != pair[1]:
                    return False
            return True
        return False

class AOESpell(Spell):
    def __init__(self, name: str, cost: int, damage: int, range: int, radius: int, activation_time: int, color: Tuple[int, int, int]) -> None:
        """ `activation_time` turns needed to cast spell. 0 is instant. """
        super().__init__(
            name = name,
            cost = cost,
            damage = damage,
            range = range,
            activation_time = activation_time,
            color=color
        )
        self.radius = radius
    
    def check_cast_conditions(self, caster: Character, target: Tuple[int, int] | None, scroll_cast: bool = False):
        cost = self.cost
        if scroll_cast:
            cost = int(self.cost*.75)
        else:
            if self.req_focus_type and not [item for item in caster.equipment.values() if self.req_focus_type in item.itemsubtypes]:
                raise Impossible(f'{self.name} not cast. {caster.name} does not have correct focus[{GameTypeNames.magicfocustypes_to_name[self.req_focus_type]}].')
            elif any(map(lambda x: isinstance(x, MagicFocusTypes), caster.equipment[caster.dominant_hand].itemsubtypes)):
                if MagicFocusTypes.EFFICIENCY in caster.equipment[caster.dominant_hand].itemsubtypes:
                    cost = int(self.cost*.75)
                    self.damage_mult = .75
                if MagicFocusTypes.POWER in caster.equipment[caster.dominant_hand].itemsubtypes:
                    cost = int(self.cost*1.25)
                    self.damage_mult = 1.25
            else:
                for item in caster.equipment.values():
                    if any(map(lambda x: isinstance(x, MagicFocusTypes), item.itemsubtypes)):
                        if MagicFocusTypes.EFFICIENCY in caster.equipment[caster.dominant_hand].itemsubtypes:
                            cost = int(self.cost*.75)
                        if MagicFocusTypes.POWER in caster.equipment[caster.dominant_hand].itemsubtypes:
                            cost = int(self.cost*1.25)
                        break
        
        target_actors = caster.engine.game_map.get_actors_in_range(*target, self.radius)
        if not target_actors:
            raise Impossible(f'{self.name} not cast. No actors at location.')
        
        if caster.mp - self.cost < 0:
            raise Impossible(f'Not enough mana to cast. [{self.cost}>{caster.mp}]')
    
class LightningBolt(Spell):
    def __init__(self) -> None:
        super().__init__(name='Lightning Bolt', cost=5, damage=18, range=15, activation_time=0, color=[0, 0, 255])
        
    def cast(self, caster: Character, target: Optional[Tuple[int, int]], scroll_cast: bool = False) -> None:
        self.check_cast_conditions(caster=caster, target=target, scroll_cast=scroll_cast)
        target_actor = caster.engine.game_map.get_actor_at_location(*target)
        
        caster.mp-=self.cost
        
        damage_taken = target_actor.entity.take_damage(int(self.damage*self.damage_mult), DamageTypes.MAGC, ElementTypes.LIGHTNING, caster)
        if damage_taken is None:
                caster.engine.message_log.add_message(f"{target_actor.name.capitalize()} dodges the lighting bolt!")
        else:
            caster.engine.message_log.add_message(f"A lighting bolt strikes the {target_actor.name} with a loud thunder, for {damage_taken} damage!")
        
class FireBall(AOESpell):
    def __init__(self) -> None:
        super().__init__(name='Fire Ball', cost=10, damage=18, range=15, radius= 3, activation_time=0, color=[255, 0, 0])
        
    def cast(self, caster: Character, target: Optional[Tuple[int, int]], scroll_cast: bool = False) -> None:
        self.check_cast_conditions(caster=caster, target=target, scroll_cast=scroll_cast)
        target_actors: list[Actor] = caster.engine.game_map.get_actors_in_range(*target, self.radius)
        
        caster.mp -= self.cost
        
        for actor in target_actors:
            damage_taken = actor.entity.take_damage(int(self.damage*self.damage_mult), DamageTypes.MAGC, ElementTypes.FIRE, caster)
            if damage_taken is None:
                caster.engine.message_log.add_message(f"{actor.name.capitalize()} dodges the fire ball!")
            else:
                caster.engine.message_log.add_message(f"A fire ball strikes the {actor.name} with a roaring blast, for {damage_taken} damage!")