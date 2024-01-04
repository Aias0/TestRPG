"""Handle the loading and initialization of game sessions."""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional

import copy, color
import tcod, libtcodpy
import lzma, pickle

import traceback

import input_handler

from engine import Engine
import sprite_data
import item_data
from magic import SPELLS

from mapgen import generate_dungeon_floor

background_image = None
#try:
#    background_image = tcod.image.load("menu_background.png")[:, :, :3]
#except:
#    pass
    
def new_game() -> Engine:
    """Return a brand new game session as an Engine instance."""
    map_width = 80
    map_height = 43
    
    room_max_size = 10
    room_min_size = 6
    max_rooms = [20, 30]
    
    max_enemies_per_room = (0, 2)
    max_items_per_room = (0, 2)
    
    player = copy.deepcopy(sprite_data.player)
    player.entity.equip(copy.deepcopy(item_data.sword), silent=True)
    player.entity.add_inventory(copy.deepcopy(item_data.health_potion), silent=True)
    player.entity.spell_book.append(copy.deepcopy(SPELLS[2]))
    
    engine = Engine(player=player)
    
    engine.game_map = generate_dungeon_floor(
        max_rooms=max_rooms,
        room_min_size= room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        enemies_per_room_range=max_enemies_per_room,
        items_per_room_range=max_items_per_room,
        engine=engine
    )
    engine.player.parent = engine.game_map
    engine.update_fov()
    engine.message_log.add_message(
        "Hello and welcome, adventurer, to yet another dungeon!", color.welcome_text
    )
    return engine

def load_game(filename: str) -> Engine:
    """ Load an Engine instance from a file. """
    with open(f'data/user_data/{filename}', 'rb') as f:
        engine = pickle.loads(lzma.decompress(f.read()))
    assert isinstance(engine, Engine)
    return engine

class MainMenu(input_handler.BaseEventHandler):
    """Handle the main menu rendering and input."""

    def on_render(self, console: tcod.console.Console) -> None:
        if background_image:
            console.draw_semigraphics(background_image, 0, 0)
        
        console.print(
            console.width // 2,
            console.height // 2 - 4,
            'TestRPG',
            fg=color.menu_title,
            alignment=libtcodpy.CENTER
        )
        console.print(
            console.width // 2,
            console.height - 2,
            'By Quentin Balestri',
            fg=color.menu_title,
            alignment=libtcodpy.CENTER
        )
        
        menu_width = 24
        for i, text in enumerate(
            ['[N] New game', '[C] Continue last game', '[L] Load Game', '[S] Settings', '[Q] Quit']
        ):
            console.print(
                console.width // 2,
                console.height // 2 - 2 + i,
                text.ljust(menu_width),
                fg=color.menu_text,
                bg=color.black,
                alignment=libtcodpy.CENTER,
                bg_blend=libtcodpy.BKGND_ALPHA(64),
            )
            
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[input_handler.EventHandler]:
        match event.sym:
            case tcod.event.KeySym.q | tcod.event.KeySym.ESCAPE:
                raise SystemExit()
            
            case tcod.event.KeySym.c:
                try:
                    saved_engine = load_game('savegame.sav')
                except FileNotFoundError:
                    print('No save File')
                except Exception as exc:
                    traceback.print_exc()
                self.__class__ = input_handler.MainGameEventHandler
                self.__dict__ = input_handler.MainGameEventHandler(saved_engine).__dict__
            
            case tcod.event.KeySym.l:
                # TODO: Load choice game.
                pass
            
            case tcod.event.KeySym.s:
                # TODO: Settings.
                pass
            
            case tcod.event.KeySym.n:
                print('New Game')
                self.__class__ = input_handler.MainGameEventHandler
                self.__dict__ = input_handler.MainGameEventHandler(new_game()).__dict__
        