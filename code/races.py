from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List
from jobs import JOBS

import game_types

if TYPE_CHECKING:
    from entity import Character

class BaseRace():
    parent: Character
    _bonus_dict = {'CON': 0, 'STR': 0, 'END': 0, 'DEX': 0, 'FOC': 0, 'INT': 0, 'WIL': 0, 'WGT': 0, 'LCK': 0}
    def __init__(
        self,
        name: str,
        name_adj: str,
        default_char: str,
        attribute_bonuses: dict[str, int] = {},
        standard_weight: int = 100,
        heal_effectiveness: float = 1,
        job_chance: Optional[dict[str, int]] = None,
        default_corpse_val: int = 10,
        vision_acuity: int = 8,
        dark_vision: int = 0,
        rarity: int = 10,
        average_lifespan: int = 90,
        adult_age: int = 18,
        elderly_age: int = 65,
        resistances: dict = {},
        ) -> None:
        
        self.name = name
        self.name_adj = name_adj
        self.default_char = default_char
        
        self.attribute_bonuses = self._bonus_dict | attribute_bonuses
        self.heal_effectiveness = heal_effectiveness
        
        self.default_corpse_val = default_corpse_val
        self.standard_weight = standard_weight
        
        self.vision_acuity = vision_acuity
        self.dark_vision = dark_vision
        
        self.rarity = rarity
        
        self.job_chance = job_chance
        if self.job_chance is None:
            self.job_chance = {}
        for job in JOBS:
            if [job for job in JOBS if job.__class__.__name__ in self.job_chance.keys()]:
                continue
            self.job_chance[job] = job.rarity
            
        self.average_lifespan = average_lifespan
        self.adult_age = adult_age
        self.elderly_age = elderly_age
        
        self.resistances = {elem: 0 for elem in game_types.ElementTypes.elements()} | resistances

class Human(BaseRace):
    def __init__(self) -> None:
        super().__init__(
            name='Human',
            name_adj='human',
            default_char='h',
            attribute_bonuses={'DEX': 2, 'END': 1, 'CON': 1, 'FOC': 1},
            job_chance={'Rouge': 15},
            rarity=15,
            average_lifespan = 90,
            adult_age=18,
            elderly_age=65
            )

class Elf(BaseRace):
    def __init__(self) -> None:
        super().__init__(
            name='Elf',
            name_adj='elven',
            default_char='e',
            attribute_bonuses={'FOC': 2, 'INT': 1},
            job_chance={'Mage': 20, 'Fighter': 5},
            vision_acuity=10,
            dark_vision=50,
            rarity=5,
            average_lifespan = 750,
            adult_age=100,
            elderly_age=650,
            )

class Dwarf(BaseRace):
    def __init__(self) -> None:
        super().__init__(
            name='Dwarf',
            name_adj='dwarven',
            default_char='d',
            attribute_bonuses={'CON': 2, 'STR': 1},
            job_chance={'Fighter': 20, 'Mage': 5},
            dark_vision=75,
            average_lifespan = 350,
            adult_age=20,
            elderly_age=270,
            resistances={game_types.ElementTypes.EARTH: 10}
            )
        
class Tiefling(BaseRace):
    def __init__(self) -> None:
        super().__init__(
            name='Tiefling',
            name_adj='tiefling',
            default_char='t',
            attribute_bonuses={'CON': 2, 'STR': 1},
            dark_vision=20,
            average_lifespan = 270,
            adult_age=60,
            elderly_age=200,
            resistances={game_types.ElementTypes.FIRE: 50}
            )

RACES: List[BaseRace] = [Human(), Elf(), Dwarf(), Tiefling()]