from __future__ import annotations
from typing import TYPE_CHECKING

import tcod

if TYPE_CHECKING:
    from sprite import Actor

class BaseAI:
    def __init__(self, actor: Actor) -> None:
        self.actor = actor
        
    def perform(self) -> None:
        """ Needs to be overwritten by subclass. """
        raise NotImplementedError()
    
    def get_path_to(self, dest_x: int, dest_y: int) -> list[tuple[int, int]]:
        """Compute and return a path to the target position.

        If there is no valid path then returns an empty list.
        """
        # Copy the walkable array.
        pass
        