from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List
from jobs import JOBS

if TYPE_CHECKING:
    from entity import Character

class BaseRace():
    parent: Character
    _bonus_dict = {'CON': 0, 'STR': 0, 'END': 0, 'DEX': 0, 'FOC': 0, 'INT': 0, 'WIL': 0, 'WGT': 0, 'LCK': 0}
    def __init__(
        self,
        name: str,
        attribute_bonuses: dict[str, int] = {},
        heal_effectiveness: float = 1,
        job_chance: Optional[dict[str, int]] = None,
        default_corpse_val: int = 10,
        vision_acuity: int = 8,
        dark_vision: int = 0,
        ) -> None:
        
        self.name = name
        self.attribute_bonuses = self._bonus_dict | attribute_bonuses
        self.heal_effectiveness = heal_effectiveness
        
        self.default_corpse_val = default_corpse_val
        
        self.vision_acuity = vision_acuity
        self.dark_vision = dark_vision
        
        self.job_chance = job_chance
        for job in JOBS:
            if [job for job in JOBS if job.__class__.__name__ in self.job_chance.keys()]:
                continue
            self.job_chance[job] = job.base_chance

class Human(BaseRace):
    def __init__(self) -> None:
        super().__init__(
            name='Human',
            attribute_bonuses={'DEX': 2, 'END': 1, 'CON': 1, 'FOC': 1},
            job_chance={'Rouge': 15}
            )

class Elf(BaseRace):
    def __init__(self) -> None:
        super().__init__(
            name='Elf',
            attribute_bonuses={'FOC': 2, 'INT': 1},
            job_chance={'Mage': 20, 'Fighter': 5},
            vision_acuity=10,
            dark_vision=50,
            )

class Dwarf(BaseRace):
    def __init__(self) -> None:
        super().__init__(
            name='Dwarf',
            attribute_bonuses={'CON': 2, 'STR': 1},
            job_chance={'Fighter': 20, 'Mage': 5},
            dark_vision=75,
            )

RACES: List[BaseRace] = [Human(), Elf(), Dwarf()]

RACES_PLURAL = {'Human': 'human', 'Elf': 'elven', 'Dwarf': 'dwarven'}