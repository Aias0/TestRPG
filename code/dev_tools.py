from __future__ import annotations
from typing import TYPE_CHECKING, Optional

import numpy as np

if TYPE_CHECKING:
    from engine import Engine

onoff = {True: 'on', False: 'off'}

onoff_bool = {v: k for k, v in onoff.items()}

god = False

def dev_command(command: str, engine: Engine) -> str:
    global god
    #print(command.split())
    match command.split():
        case ['invincible']:
            return invincible(engine)
        case ['invincible', cmd]:
            return invincible(engine, onoff_bool[cmd])
        
        case ['wallhacks']:
            return wallhacks(engine)
        case ['wallhacks', cmd]:
            return wallhacks(engine, onoff_bool[cmd])
        
        case ['god']:
            god = not god
            invincible(engine, god)
            wallhacks(engine, god)
            return f'God mode: {onoff[god]}'
        case ['god', cmd]:
            god = onoff_bool[cmd]
            invincible(engine, god)
            wallhacks(engine, god)
            return f'God mode: {onoff[god]}'
        
        case ['revealmap']:
            engine.game_map.explored = np.full(engine.game_map.explored.shape, True)
            return 'Map revealed'
        case ['hidemap']:
            engine.game_map.explored = np.full(engine.game_map.explored.shape, False)
            return 'Map hidden'
        
        case ['seeall']:
            engine.game_map.visible = np.full(engine.game_map.visible.shape, True)
            return 'momentary omniscience'
        case ['allseeing']:
            return omniscience(engine)
        case ['allseeing', cmd]:
            return omniscience(engine, onoff_bool[cmd])
            
        case ['enemyai']:
            return enemyai(engine)
        case ['enemyai', cmd]:
            return enemyai(engine, onoff_bool[cmd])
        case _:
            return f'command not found: {command}'
        
def wallhacks(engine: Engine, state: Optional[bool] = None):
    if state is not None:
        engine.wallhacks = state
    else:
        engine.wallhacks = not engine.wallhacks
    return f'wall hacks: {onoff[engine.wallhacks]}'
def invincible(engine: Engine, state: Optional[bool] = None):
    if state is not None:
        engine.player.entity.invincible = state
    else:
        engine.player.entity.invincible = not engine.player.entity.invincible
    return f'invincible: {onoff[engine.player.entity.invincible]}'
def omniscience(engine: Engine, state: Optional[bool] = None):
    engine.game_map.visible = np.full(engine.game_map.visible.shape, True)
    if state is not None:
        engine.omniscient = state
    else:
        engine.omniscient = not engine.omniscient
    return f'omniscience: {onoff[engine.omniscient]}'
def enemyai(engine: Engine, state: Optional[bool] = None):
    if state is not None:
        engine.ai_on
    else:
        engine.ai_on = not engine.ai_on
    return f'Enemy ai: {onoff[engine.ai_on]}'
    