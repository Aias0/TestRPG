from sprite import Actor, Sprite
from entity import Character, Door

import races
import jobs

import color, copy

from magic import SPELLS
import item_data

from ai import HostileEnemy

dev_player = Actor(
    char='@',
    character=Character(
        name='Tester',
        corpse_value=1,
        race=races.Human(),
        gender='male',
        job=jobs.Fighter(),
        base_CON=14,
        base_STR=14,
        tags=set('player'),
        spell_book=[*SPELLS],
        inventory=[copy.deepcopy(item_data.simple_key)]
        ),
    ai_cls=HostileEnemy
)


door = Sprite(
    entity=Door(
        False
    ),
    char='+',
    blocks_movement=True,
    blocks_fov=True,
    color=color.brown
)
