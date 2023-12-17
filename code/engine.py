from __future__ import annotations
from typing import TYPE_CHECKING, Set, Iterable, Any

from tcod.console import Console
from tcod.map import compute_fov

from input_handler import MainGameEventHandler
from message_log import MessageLog
from render_functions import render_resource_bar, render_names_at_mouse_location

import numpy as np

if TYPE_CHECKING:
    from sprite import Actor
    from game_map import GameMap
    from input_handler import EventHandler

class Engine:
    game_map: GameMap
    
    def __init__(self, player: Actor):
        self.event_handler: EventHandler = MainGameEventHandler(self)
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player
        
        self.input_log = []
        
        self.wallhacks = False
        self.omniscient = False
        self.ai_on = True
        
    def handle_npc_turns(self) -> None:
        for sprite in self.game_map.sprites - {self.player}:
            if not hasattr(sprite, 'ai') or not self.ai_on:
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
        if self.omniscient:
            self.game_map.visible = np.full(self.game_map.visible.shape, True)
        
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible
    
    def render(self, console: Console) -> None:
        self.game_map.render(console)
        
        self.message_log.render(console=console, x=21, y=45, width=40, height=5)
        
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
        
        render_names_at_mouse_location(console=console, x=21, y=44, engine=self)