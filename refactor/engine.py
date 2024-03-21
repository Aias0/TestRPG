from __future__ import annotations
from typing import TYPE_CHECKING
from main import logger

import tcod
from tcod.console import Console

if TYPE_CHECKING:
    from handlers import EventHandler
    from world import GameWorld, GameMap
    from sprite import Actor

class Engine:
    game_world: GameWorld
    
    def __init__(self, player: Actor):
        self.event_handler: EventHandler = None
        self.message_log = None
        self.mouse_loc: tuple[int, int] = (0, 0)
        
        self.player = player
        
        self.ai_on: bool = True
        
    @property
    def game_map(self) -> GameMap:
        return self.game_world.current_game_map