#!/usr/bin/env python3
import tcod, copy


import color
from engine import Engine
import sprite_data
from mapgen import generate_dungeon_floor

def main() -> None:
    screen_width = 80
    screen_height = 50
    
    map_width = 80
    map_height = 43
    
    room_max_size = 10
    room_min_size = 6
    max_rooms = [20, 30]
    
    max_enemies_per_room = (0, 2)
    
    #tileset_file = 'assets/textures/dejavu10x10_gs_tc.png'
    #tileset = tcod.tileset.load_tilesheet(
    #    tileset_file, 32, 8, tcod.tileset.CHARMAP_TCOD
    #)
    
    tileset_file = 'assets/textures/rexpaint_cp437_10x10.png'
    tileset = tcod.tileset.load_tilesheet(
        tileset_file, 16, 16, tcod.tileset.CHARMAP_CP437
    )
    tcod.tileset.CHARMAP_CP437
    player = copy.deepcopy(sprite_data.player)
    
    engine = Engine(player=player)
    
    engine.game_map = generate_dungeon_floor(
        max_rooms=max_rooms,
        room_min_size= room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        enemies_per_room_range=max_enemies_per_room,
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
            
            
            engine.event_handler.handle_events(context)
            
if __name__ == '__main__':
    main()