from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Optional

from exceptions import Impossible
from game_types import DamageTypes

if TYPE_CHECKING:
    from entity import Character
    from sprite import Actor

class Spell():
    def __init__(self, name: str, cost: int, damage: int, range: int, activation_time: int) -> None:
        """ `activation_time` turns needed to cast spell. 0 is instant. """
        self.name = name
        self.cost = cost
        self.damage = damage
        self.range = range
        self.activation_time = activation_time
        
    def cast(self, caster: Character, target) -> None:
        raise NotImplementedError()
    
class LightningBolt(Spell):
    def __init__(self) -> None:
        super().__init__(name='Lightning Bolt', cost=10, damage=18, range=6, activation_time=0)
        
    def cast(self, caster: Character, target: Optional[Tuple[int, int]]) -> None:
        if target is None:
            raise Impossible(f'{self.name} not cast. Has not target.')
        target_actor = caster.engine.game_map.get_actor_at_location(*target)
        if target_actor is None:
            raise Impossible(f'{self.name} not cast. No actor at location.')
        if target_actor.distance(caster.parent.x, caster.parent.y) > self.range:
            raise Impossible(f'{self.name} not cast. Target out of range.')
        
        caster.mp-=self.cost
        damage_taken = target_actor.entity.take_damage(self.damage, DamageTypes.MAGC, caster)
        caster.engine.message_log.add_message(f"A lighting bolt strikes the {target_actor.name} with a loud thunder, for {damage_taken} damage!")
            
        
        