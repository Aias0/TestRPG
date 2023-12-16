from __future__ import annotations
from typing import TYPE_CHECKING, Set, Iterable, Any

from tcod.console import Console
from tcod.context import Context
from tcod.map import compute_fov

from input_handler import MainGameEventHandler

if TYPE_CHECKING:
    from sprite import Sprite, Actor
    from entity import Character
    from game_map import GameMap
    from input_handler import EventHandler

class Engine:
    game_map: GameMap
    
    def __init__(self, player: Actor):
        self.event_handler: EventHandler = MainGameEventHandler(self)
        self.player = player
        
    def handle_npc_turns(self) -> None:
        for sprite in self.game_map.sprites - {self.player}:
            sprite: Actor
            if sprite.ai:
                sprite.ai.perform()
            
    def update_fov(self) -> None:
        """ Recompute the visible area based on the players point of view. """
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles['transparent'],
            (self.player.x, self.player.y),
            radius=8,
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible
    
    def render(self, console: Console, context: Context) -> None:
        self.game_map.render(console)
        
        console.print(
            x=1,
            y=47,
            string=f'HP: {self.player.entity.hp}/{self.player.entity.max_hp}'
        )
            
        context.present(console)
        
        console.clear()