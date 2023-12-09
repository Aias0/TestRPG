from __future__ import annotations
from typing import TYPE_CHECKING

from tcod.console import Console

from message_log import MessageLog

if TYPE_CHECKING:
    from sprite import Actor

class Engine:
    
    def __init__(self, player: Actor):
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player
        
    def handle_enemy_turns(self) -> None:
        raise NotImplementedError
    
    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        raise NotImplementedError
    
    def render(self, console: Console):
        raise NotImplementedError