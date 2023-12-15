from __future__ import annotations
from typing import List, Tuple, TYPE_CHECKING

import numpy as np
import tcod

from actions import Action, MeleeAction, MovementAction, WaitAction
from entity import Entity

if TYPE_CHECKING:
    from sprite import Actor

class BaseAI(Action, Entity):
    sprite: Actor
    
    def perform(self) -> None:
        raise NotImplementedError()
    
    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """Compute and return a path to the target position.

        If there is no valid path then returns an empty list.
        """
        # Copy the walkable array.
        cost = np.array(self.sprite.gamemap.tiles['walkable'], dtype=np.int8)
        
        for sprite in self.sprite.gamemap.sprites:
            # Check that an entity blocks movement and the cost isn't zero (blocking).
            if sprite.blocks_movement and cost[sprite.x, sprite.y]:
                # Add to the cost of a blocked position.
                # A lower number means more enemies will take longer paths in
                # order to surround the player.
                cost[sprite.x, sprite.y] += 10
                
        # Create a graph from the cost array and pass that graph to a new pathfinder.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)
        
        pathfinder.add_root((self.sprite.x, self.sprite.y)) # Start position.
        
        # Compute the path to the destination and remove the starting point.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()
        
        # Convert from List[List[int]] to List[Tuple[int, int]].
        return [(index[0], index[1]) for index in path]
    
class HostileEnemy(BaseAI):
    def __init__(self, sprite: Actor):
        super().__init__(sprite)
        self.path: List[Tuple[int, int]] = []
        
    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.sprite.x
        dy = target.y - self.sprite.y
        distance = max(abs(dx), abs(dy)) # Chebyshev distance.
        
        if self.engine.game_map.visible[self.sprite.x, self.sprite.y]:
            if distance <= 1:
                return MeleeAction(self.sprite, dx, dy).perform()
            
        self.path = self.get_path_to(target.x, target.y)
        
        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.sprite, dest_x - self.sprite.x, dest_y - self.sprite.y,
            ).perform()
            
        return WaitAction(self.sprite).perform()