from sprite import Actor
from entity import Character

import races
import jobs

from ai import HostileEnemy

from item_data import sword

player = Actor(
    char='@',
    character=Character(
        name='Player',
        corpse_value=1,
        race=races.Human(),
        gender='male',
        job=jobs.Fighter(),
        base_CON=14,
        base_STR=14,
        starting_equipment=[sword]
        ),
    ai_cls=HostileEnemy
)
