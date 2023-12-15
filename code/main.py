#!/usr/bin/env python3
import tcod

from engine import Engine
from input_handler import EventHandler
from mapgen import generate_dungeon

from sprite import Actor
from entity import Character
from races import Human
from jobs import Fighter

def main() -> None:
    screen_width = 80
    screen_height = 50
    
    map_width = 80
    map_height = 45
    
    tileset_file = 'assets/textures/dejavu10x10_gs_tc.png'
    
    tileset = tcod.tileset.load_tilesheet(
        tileset_file, 32, 8, tcod.tileset.CHARMAP_TCOD
    )
    
    event_handler = EventHandler()
    
    player = Actor(Character('Player', 1, Human(), Fighter()), '@', screen_width // 2, screen_height // 2)
    npc = Actor(Character('NPC', 1, Human(), Fighter()), '@', screen_width // 2 - 5, screen_height // 2, (255, 255, 0))
    entities = {player, npc}
    
    game_map = generate_dungeon(map_width, map_height)
    
    engine = Engine(entities=entities, event_handler=event_handler, game_map=game_map, player=player)
    
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
            
            events = tcod.event.wait()
            
            engine.handle_events(events)
    
if __name__ == '__main__':
    main()