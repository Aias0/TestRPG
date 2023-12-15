from __future__ import annotations
from typing import TYPE_CHECKING, Set, Iterable, Any

from tcod.console import Console
from tcod.context import Context

from input_handler import EventHandler

if TYPE_CHECKING:
    from sprite import Sprite, Actor
    from game_map import GameMap

class Engine:
    
    def __init__(self, entities: Set[Sprite], event_handler: EventHandler, game_map: GameMap, player: Actor):
        self.entities = entities
        self.event_handler = event_handler
        self.game_map = game_map
        self.player = player
        
    def handle_events(self, events: Iterable[Any]) -> None:
        for event in events:
            action = self.event_handler.dispatch(event)
                
            if action is None:
                continue
            
            action.perform(self, self.player)
    
    def render(self, console: Console, context: Context) -> None:
        self.game_map.render(console)
        
        for entity in self.entities:
            console.print(entity.x, entity.y, entity.char, fg=entity.color)
            
        context.present(console)
        
        console.clear()