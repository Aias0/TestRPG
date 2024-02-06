from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Dict

import random, copy
import numpy as np

from entity import Character, Item, Entity
from sprite import Sprite, Actor

from render_order import RenderOrder

from ai import HostileEnemy

if TYPE_CHECKING:
    from races import BaseRace
    from jobs import BaseJob

def gen_enemies(
    enemy_num: int | tuple,
    race_list: Optional[Dict[BaseRace, int]] = None,
    race_overwrite: bool = False,
    job_list: Optional[Dict[BaseJob, int]] = None,
    job_overwrite: bool = False,
    level_list: Optional[Dict[int, int]] = None,
    level_overwrite: bool = True,
    ) -> List[Actor]:
    """ `overwrite` `True` overwrites default values, `False` blends values."""
    from races import RACES
    from jobs import JOBS
    base_race_list = dict(zip([race.__class__.__name__ for race in RACES], [race.rarity for race in RACES]))
    base_job_list = dict(zip([job.__class__.__name__ for job in JOBS], [job.rarity for job in JOBS]))
    base_level_list = {1:15, 2:10, 3:5}
    
    # Convert int into list so random always is list
    
    if isinstance(enemy_num, int):
        enemy_num_range = [enemy_num,]*2
    else:
        enemy_num_range = list(enemy_num)
    enemy_num_range[1] += 1
    
    if race_overwrite and race_list:
        race_chance = race_list
    elif race_list:
        race_chance = base_race_list | race_list
    else:
        race_chance = base_race_list
    race_chance, level_race_weights = zip(*race_chance.items())
    
    num_enemies = random.randrange(*enemy_num_range)
    
    enemy_races = random.choices(race_chance, level_race_weights, k=num_enemies)
    
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
                gender= random.choice(['male', 'female']),
                job= enemy_job,
                level= random.choices(level_list, level_level_weights)[0],
                base_CON=8,
                base_DEX=8,
                base_STR=8
            ))

    enemies_actors = entity_to_sprite(enemies)
    
    if not isinstance(enemies_actors, list):
        enemies_actors = [enemies_actors]
        
    return enemies_actors

def gen_items(
    item_num: int | tuple,
    item_list: Optional[Dict[BaseRace, int]] = None,
    item_overwrite: bool = False,
) -> List[Sprite]:
    from item_data import ITEMS
    base_item_list = dict(zip([item.name for item in ITEMS], [item.rarity for item in ITEMS]))
    
    if isinstance(item_num, int):
        item_num_range = [item_num,]*2
    else:
        item_num_range = list(item_num)
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
        items.append(copy.deepcopy([i for i in ITEMS if i.name == item][0]))
    
    item_sprites = entity_to_sprite(items)
    if not isinstance(item_sprites, list):
        item_sprites = [item_sprites]
    
    return item_sprites
    

def entity_to_sprite(entities: Entity | List[Entity]) -> Sprite | List[Sprite]:
    if not isinstance(entities, list):
        entities = [entities]
    
    sprites = []
    for entity in entities:
        if isinstance(entity, Character):
            sprites.append(Actor(
                character=entity,
                char=entity.race.default_char,
                color=entity.job.default_color,
                ai_cls=HostileEnemy,
            ))
        elif isinstance(entity, Item):
            sprites.append(Sprite(
                entity=entity,
                char=entity.char,
                color=entity.color,
                render_order=RenderOrder.ITEM
            ))
    
    if len(sprites) == 1:
        return sprites[0]
    return sprites