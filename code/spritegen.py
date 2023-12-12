from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Dict

import random
import numpy as np

from races import RACES
from jobs import JOBS
from item_data import ITEMS

from entity import Character, Item, Entity
from sprite import Sprite, Actor

from render_order import RenderOrder
from item_types import ItemTypes

if TYPE_CHECKING:
    from races import BaseRace
    from jobs import BaseJob


base_race_list = ['Human', 'Elf', 'Dwarf']
base_race_list = dict(zip(base_race_list, [10,]*3))

base_job_list = dict(zip([job.__class__.__name__ for job in JOBS], [10]*len(JOBS)))

base_level_list = {1:15, 2:10, 3:5}

base_item_list = dict(zip([item.name for item in ITEMS], [10]*len(ITEMS)))


def gen_enemies(
    enemy_num_range: int | list,
    race_list: Optional[Dict[BaseRace, int]] = None,
    race_overwrite: bool = False,
    job_list: Optional[Dict[BaseJob, int]] = None,
    job_overwrite: bool = False,
    level_list: Optional[Dict[int, int]] = None,
    level_overwrite: bool = True,
    ) -> List[Actor]:
    """ `overwrite` `True` overwrites defualt values, `False` blends values.\n\n"""
    
    # Convert int into tuple so random always is int
    if type(enemy_num_range) == int:
        enemy_num_range = [enemy_num_range,]*2
    enemy_num_range[1] += 1
    
    if race_overwrite and race_list:
        race_list = race_list
    elif race_list:
        race_list = base_race_list | race_list
    else:
        race_list = base_race_list
    race_list, level_race_weights = zip(*race_list.items())
    
    num_enemies = random.randrange(enemy_num_range[0], enemy_num_range[1])
    
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
        
        enemies.append(Character(
                name= f'{enemy_race.name} {enemy_job.name}',
                corpse_value= enemy_race.default_corpse_val,
                race= enemy_race,
                job= enemy_job,
                level= random.choices(level_list, level_level_weights)[0]
            ))
        
    enemies_actors: List[Actor] = entity_to_sprite(enemies)
    
    for enemy in enemies_actors:
        enemy.hostile = True
        
    return enemies_actors

def gen_items(
    item_num_range: int | list,
    item_list: Optional[Dict[BaseRace, int]] = None,
    item_overwrite: bool = False,
) -> List[Sprite]:
    
    if type(item_num_range) == int:
        item_num_range = [item_num_range,]*2
    item_num_range[1] += 1
    
    if item_list and item_overwrite:
        item_chance = item_list
    elif item_list:
        item_chance = base_item_list | item_list
    else:
        item_chance = base_item_list
    
    item_list, item_weights = zip(*item_chance.items())
    
    num_items = random.randrange(item_num_range[0], item_num_range[1])

    item_choices:List[str] = random.choices(item_list, item_weights, k=num_items)
    
    items:List[Item] = []
    for item in item_choices:
        items.append([i for i in ITEMS if i.name == item][0])
    
    return entity_to_sprite(items)
    

def entity_to_sprite(entities: Entity | List[Entity]) -> Sprite | List[Sprite]:
    if type(entities) != list:
        entities = [entities]
    
    sprites = []
    for entity in entities:
        if type(entity) == Character:
            sprites.append(Actor(
                character=entity,
                char=entity.race.defualt_char,
                color=entity.job.default_color,
            ))
        elif type(entity) == Item:
            sprites.append(Sprite(
                entity=entity,
                char=entity.char,
                color=entity.color,
                render_order=RenderOrder.ITEM
            ))
        else:
            sprites.append(Sprite())
            
    return sprites

        
    
result = gen_enemies(
    enemy_num_range=[4, 8],
    race_list={'Human': 10, 'Elf': 2, 'Dwarf': 5},
    
    )

print(result)
[print(i.entity.description) for i in result]

result2 = gen_items(
    item_num_range=[3, 6],
)
print(result)