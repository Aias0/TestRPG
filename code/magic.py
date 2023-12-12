from __future__ import annotations
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from entity import Character

class Spell():
    def __init__(self, name: str, cost: int, activation_time: int) -> None:
        """ `activation_time` turns needed to cast spell. 0 is instant. """
        self.name = name
        self.cost = cost
        self.activation_time = activation_time
        
    def cast(self, caster: Character, target) -> None:
        raise NotImplementedError()
    
class LightningBolt(Spell):
    def __init__(self) -> None:
        super().__init__(name='Lightning Bolt', cost=10, activation_time=0)
        
    def cast(self, caster: Character, target: Tuple[int, int]) -> None:
        caster.mp-=self.cost