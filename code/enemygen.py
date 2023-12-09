from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Dict

import random
import numpy as np

from races import RACES
from jobs import JOBS
from entity import Character

if TYPE_CHECKING:
    from races import BaseRace
    from jobs import BaseJob


base_race_list = ['Human', 'Elf', 'Dwarf']
base_race_list = dict(zip(base_race_list, [10,]*3))

base_job_list = dict(zip([job.__class__.__name__ for job in JOBS], [10]*len(JOBS)))

base_level_list = {1:15, 2:10, 3:5}


def gen_enemies(
    enemy_range: int | list,
    race_list: Optional[Dict[BaseRace, int]] = None,
    race_overwrite: bool = False,
    job_list: Optional[Dict[BaseJob, int]] = None,
    job_overwrite: bool = False,
    level_list: Optional[Dict[int, int]] = None,
    level_overwrite: bool = True,
    ) -> List[Character]:
    """ `overwrite` `True` overwrites defualt values, `False` blends values.\n\n"""
    
    # Convert int into tuple so random always is int
    if type(enemy_range) == int:
        enemy_range = [enemy_range,]*2
    enemy_range[1] += 1
    
    if race_overwrite and race_list:
        race_list = race_list
    elif race_list:
        race_list = base_race_list | race_list
    else:
        race_list = base_race_list
    race_list, level_race_weights = zip(*race_list.items())
    
    num_enemies = random.randrange(enemy_range[0], enemy_range[1])
    
    enemy_races = random.choices(race_list, level_race_weights, k=num_enemies)
    
    if level_overwrite and level_list:
        level_chance = level_list
    elif level_list:
        level_chance = base_level_list | level_list
    else:
        level_chance = base_level_list
    level_list, level_level_weights = zip(*level_chance.items())
        
    enemies: List[Character] = []
    for enemy in enemy_races:
        enemy_race = [i for i in RACES if i.__class__.__name__ == enemy][0]
        
        if job_overwrite:
            job_chance = job_list
        else:
            job_chance = base_job_list | enemy_race.job_chance
        job_key, level_job_weights = zip(*job_chance.items())
        job_pick = random.choices(job_key, level_job_weights)[0]
        enemy_job = [i for i in JOBS if i.__class__.__name__ == job_pick][0]
        
        enemies.append(
            Character(
                name= f'{enemy_race.name} {enemy_job.name}',
                corpse_value= enemy_race.default_corpse_val,
                race= enemy_race,
                job= enemy_job,
                level= random.choices(level_list, level_level_weights)[0]
                
            )
            )
    
    return enemies
        
        
    
result = gen_enemies(
    enemy_range=[4, 8],
    race_list={'Human': 10, 'Elf': 2, 'Dwarf': 5},
    
    )

print(result)
[print(i.description) for i in result]