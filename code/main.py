#!/usr/bin/env python3
import tcod, copy
import traceback

from config import SETTINGS

import color
from engine import Engine
import sprite_data
import item_data

from mapgen import generate_dungeon_floor

def main() -> None:
    screen_width = SETTINGS['screen_width']
    screen_height = SETTINGS['screen_height']
    
    map_width = 80
    map_height = 43
    
    room_max_size = 10
    room_min_size = 6
    max_rooms = [20, 30]
    
    max_enemies_per_room = (0, 2)
    max_items_per_room = (0, 2)
    
    tileset_file = SETTINGS['tileset_file']
    tileset = tcod.tileset.load_tilesheet(
        tileset_file, 16, 16, tcod.tileset.CHARMAP_CP437
    )
    tcod.tileset.CHARMAP_CP437
    player = copy.deepcopy(sprite_data.player)
    player.entity.equip(copy.deepcopy(item_data.sword), silent=True)
    
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
    
    engine.update_fov()
    
    engine.message_log.add_message(
        "Hello and welcome, adventurer, to yet another dungeon!", color.welcome_text
    )
    
    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title='TestRPG',
        vsync=True,
    ) as context:
        root_console = tcod.console.Console(screen_width, screen_height, order='F')
        while True:
            root_console.clear()
            engine.event_handler.on_render(console=root_console)
            context.present(root_console)
            
            try:
                if engine.wait:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        engine.event_handler.handle_events(event)
                else:
                    for event in tcod.event.get():
                        context.convert_event(event)
                        engine.event_handler.handle_events(event)
            except Exception: # Handle exceptions in game.
                traceback.print_exc() # Print error to stderr
                # Then print to the message log.
                engine.message_log.add_message(traceback.format_exc(), color.error)
            
if __name__ == '__main__':
    main()