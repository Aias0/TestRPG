from __future__ import annotations
from typing import List, Tuple, TYPE_CHECKING, Optional

import numpy as np
import tcod, random

from actions import Action, MeleeAction, MovementAction, WaitAction, BumpAction

from tcod.map import compute_fov

from sprite import Actor

if TYPE_CHECKING:
    from sprite import Actor

class BaseAI(Action):
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
        
        self.lose_aggro_turns = self.sprite.entity.INT // 2
        self.aggro_turn = 0
        

    def perform(self) -> Action:
        target = self.engine.player
        
        visible = np.copy(self.sprite.gamemap.tiles['transparent'])

        for sprite in self.sprite.gamemap.sprites:
            if sprite.blocks_fov:
                visible[sprite.x, sprite.y] = False
        
        vis_tiles = compute_fov(
            visible,
            (self.sprite.x, self.sprite.y),
            radius=8,
        )

        for sprite in self.engine.game_map.sprites - {self.sprite} - {sprite for sprite in self.engine.game_map.sprites if not hasattr(sprite, 'ai')}:
            if not sprite.ai:
                continue
            sprite: Actor
            if vis_tiles[sprite.x, sprite.y] and sprite.hostile and not sprite.ai.aggro_turn:# If another sprite in range becomes hostile also become hostile.
                self.sprite.hostile = True
                self.aggro_turn = int(self.lose_aggro_turns * 1/4 + 0.5)
            
        if vis_tiles[target.x, target.y]: # If player in FOV become hostile
            self.sprite.hostile = True
            self.aggro_turn = 0
        elif self.sprite.hostile:
            self.aggro_turn +=1
            
            if self.aggro_turn > self.lose_aggro_turns:
                self.sprite.hostile = False
                self.aggro_turn = 0
        else:
            return WaitAction(self.sprite).perform()
        
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
    
    
class ConfusedEnemy(BaseAI):
    """ A confused enemy will stumble around aimlessly for a given number of turns, then revert back to its previous AI.
    If an actor occupies a tile it is randomly moving into, it will attack. """
    
    
    def __init__(self, sprite: Actor, previous_ai: Optional[BaseAI], turns_remaining) -> None:
        super().__init__(sprite)
        
        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining
        
    def perform(self) -> None:
        # Revert the AI back to the original state if the effect has run its course.
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                f'The {self.sprite.name} is no longer confused.'
            )
            self.sprite.ai = self.previous_ai
        else:
            # Pick a random direction
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),  # Northwest
                    (0, -1),  # North
                    (1, -1),  # Northeast
                    (-1, 0),  # West
                    (1, 0),  # East
                    (-1, 1),  # Southwest
                    (0, 1),  # South
                    (1, 1),  # Southeast
                ]
            )
            
            self.turns_remaining -= 1
            # The actor will either try to move or attack in the chosen random direction.
            # Its possible the actor will just bump into the wall, wasting a turn.
            return BumpAction(self.entity, direction_x, direction_y,).perform()
