from __future__ import annotations
from typing import TYPE_CHECKING, Optional

import numpy as np
from entity import Item

import item_data

import copy, os, sys

from item_data import ITEMS
from input_handler import SelectTileHandler

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
            omniscience(engine, god)
            return f'God mode: {onoff[god]}'
        case ['god', cmd]:
            god = onoff_bool[cmd]
            invincible(engine, god)
            omniscience(engine, god)
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
        
        case['print', 'player', cmd]:
            try:
                return f'{cmd}: {str(getattr(engine.player.entity, cmd))}'
            except AttributeError:
                return f'player.entity.{cmd} does not exist.'
            
        case ['player', 'add', cmd]:
            cmd = cmd.replace('_', ' ')
            item = [item for item in ITEMS if item.name == cmd]
            if not item:
                return f'Item with name: {cmd} does not exist.'
            from spritegen import entity_to_sprite
            item = copy.deepcopy(item[0])
            item.parent = entity_to_sprite(item)
            item.parent.parent = engine.game_map
            
            engine.player.entity.add_inventory(item, True)
            return f'{cmd} added to inventory.'
        case ['player', 'add', cmd, amount]:
            cmd = cmd.replace('_', ' ')
            item = [item for item in ITEMS if item.name == cmd]
            if not item:
                return f'Item with name: {cmd} does not exist.'
            from spritegen import entity_to_sprite
            item = item[0]
            item.parent = entity_to_sprite(item)
            item.parent.parent = engine.game_map
            for i in range(int(amount)):
                engine.player.entity.add_inventory(copy.deepcopy(item), True)
            return f'{cmd}x{amount} added to inventory.'
        
        case ['player', 'set', attr, value]:
            from config import tryeval
            try:
                setattr(engine.player.entity, attr, tryeval(value))
                return f'{attr}: {value}'
            except AttributeError:
                return f'player.entity.{attr} does not exist.'
        
        case ['getinfo']:
            engine.event_handler = SelectTileHandler(engine)
            
        
        case ['cls']:
            engine.message_log.messages = []
            return 'message log cleared.'
        
        case ['biginv']:
            for i in range(80):
                engine.player.entity.add_inventory(Item(f'Test Item {i}', 1, 0), True)
            return 'test inventory big added.'
        case ['multiinv']:
            for i in range(3):
                engine.player.entity.add_inventory(copy.deepcopy(item_data.health_potion), True)
            return 'test inventory multi added.'
        case ['equipinv']:
            for i in range(5):
                engine.player.entity.add_inventory(copy.deepcopy(item_data.sword), True)
                return 'test inventory equip added.'
            
        case ['heal']:
            engine.player.entity.hp = engine.player.entity.max_hp
            return 'player healed'
        case ['heal', cmd]:
            engine.player.entity.hp = int(cmd)
            return f'{engine.player.name} healed for {cmd}'
        
        case ['revive']:
            engine.player.entity.resurrect(1)
            return f' returned {engine.player.name} to life.'
        
        case ['restart']:
            os.execl(sys.executable, sys.executable, * sys.argv)
            
        
        case ['help']:
            return ', '.join([
                'invincible',
                'wallhacks',
                'god',
                'revealmap',
                'hidemap',
                'seeall',
                'allseeing',
                'enemyai',
                'print player _',
                'player add _',
                'cls',
                'biginv',
                'multiinv',
                'equipinv',
                'heal',
                'heal _',
                'revive',
                'restart'
            ])
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
    