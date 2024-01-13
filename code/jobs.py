from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple

import item_data

import magic

import copy

if TYPE_CHECKING:
    from entity import Character, Item
    from magic import Spell

class BaseJob():
    parent: Character
    def __init__(
        self,
        name: str,
        default_color: Tuple[int, int, int],
        starting_equipment: List[Item] = [],
        starting_spells: List[Spell] = [],
        rarity: int = 10
    ) -> None:
        self.name = name
        self.default_color = default_color
        self.starting_equipment = starting_equipment
        self.starting_spells = starting_spells
        self.rarity = rarity

class Mage(BaseJob):
    def __init__(self) -> None:
        super().__init__(
            name='Mage',
            default_color=[0, 0, 255],
            rarity=5,
            starting_equipment = list(map(copy.deepcopy, [item_data.staff, item_data.robes])),
            starting_spells=[magic.FireBolt()]
        )

class Rouge(BaseJob):
    def __init__(self) -> None:
        super().__init__(
            name='Rouge',
            default_color=[0, 255, 0],
            starting_equipment = list(map(copy.deepcopy, [item_data.dagger, item_data.leather_jerkin]))
        )

class Fighter(BaseJob):
    def __init__(self) -> None:
        super().__init__(
            name='Fighter',
            default_color=[255, 0, 0],
            rarity= 15,
            starting_equipment = list(map(copy.deepcopy, [item_data.sword, item_data.chest_plate]))
        )
        
JOBS: List[BaseJob] = [Mage(), Rouge(), Fighter()]