#!/usr/bin/env python3
import tcod, copy

from engine import Engine
import sprite_data
from mapgen import generate_dungeon_floor

def main() -> None:
    screen_width = 80
    screen_height = 50
    
    map_width = 80
    map_height = 45
    
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
    
    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title='TestRPG',
        vsync=True,
    ) as context:
        root_console = tcod.console.Console(screen_width, screen_height, order='F')
        while True:
            engine.render(console=root_console, context=context)
            
            engine.event_handler.handle_events()
    
if __name__ == '__main__':
    main()