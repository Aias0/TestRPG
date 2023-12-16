from __future__ import annotations
from typing import TYPE_CHECKING, Set, Iterable, Any

from tcod.console import Console
from tcod.context import Context
from tcod.map import compute_fov

from input_handler import MainGameEventHandler
from render_functions import render_resource_bar

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
            if not hasattr(sprite, 'ai'):
                continue
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
        
        render_resource_bar(
            x=0,
            y=45,
            resource='hp',
            console=console,
            current_val=self.player.entity.hp,
            maximum_val=self.player.entity.max_hp,
            total_width=20
        )
        render_resource_bar(
            x=0,
            y=47,
            resource='mp',
            console=console,
            current_val=self.player.entity.mp,
            maximum_val=self.player.entity.max_mp,
            total_width=20
        )
        render_resource_bar(
            x=0,
            y=49,
            resource='sp',
            console=console,
            current_val=self.player.entity.sp,
            maximum_val=self.player.entity.max_sp,
            total_width=20
        )
            
        context.present(console)
        
        console.clear()