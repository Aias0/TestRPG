from __future__ import annotations
from typing import TYPE_CHECKING, Iterable, Iterator, Optional

import numpy as np
import tile_types

from sprite import Actor
from entity import Item

from tcod.console import Console

if TYPE_CHECKING:
    from engine import Engine
    from sprite import Sprite

class GameMap:
    def __init__(self, engine: Engine, width: int, height: int, sprites: Iterable[Sprite] = ()) -> None:
        self.engine = engine
        self.width, self.height = width, height
        self.sprites = sprites
        
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order='F')
        
        self.visible = np.full(
            (width, height), fill_value=False, order='F'
        ) # Tiles player can see
        self.explored = np.full(
            (width, height), fill_value=False, order='F'
        ) # Tiles the player has seen
        
    @property
    def gamemap(self) -> GameMap:
        return self
    
    @property
    def actors(self) -> Iterator[Sprite]:
        """Iterate over this maps living actors."""
        yield from (
            sprite for sprite in self.sprites if isinstance(sprite, Actor) and sprite.is_alive
        )
    
    @property
    def items(self) -> Iterator[Sprite]:
        yield from (
            sprite for sprite in self.sprites if isinstance(sprite.entity, Item)
        )
        
    def get_blocking_entity_at_location(
        self, location_x: int, location_y: int,
    ) -> Optional[Sprite]:
        
        for sprite in self.sprites:
            if (
                sprite.blocks_movement
                and sprite.x == location_x
                and sprite.y == location_y
            ):
                return sprite
            
        return None
    
    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor
            
        return None
    
    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if x and y are inside of the bounds of this map."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def render(self, console: Console) -> None:
        """
        Renders the map.

        If a tile is in the "visible" array, then draw it with the "light" colors.
        If it isn't, but it's in the "explored" array, then draw it with the "dark" colors.
        Otherwise, the default is "SHROUD".
        """
        console.tiles_rgb[0 : self.width, 0: self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles['light'], self.tiles['dark']],
            default=tile_types.SHROUD,
        )
        
        sprites_sorted_for_rendering = sorted(
            self.sprites, key=lambda x: x.render_order.value
        )
        
        for sprite in sprites_sorted_for_rendering:
            # Only print sprites that are in FOV
            if self.visible[sprite.x, sprite.y]:
                console.print(
                    x=sprite.x, y=sprite.y, string=sprite.char, fg=sprite.color
                )
                
class GameWorld:
    """
    Holds the settings for the GameMap, and generates new maps when moving down the stairs. [TODO] store generated gamemaps for recall.
    """
    
    def __init__(
        self,
        *,
        engine: Engine,
        map_width: int,
        map_height: int,
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        current_floor: int = 0
    ) -> None:
        
        self.engine = engine
        
        self.map_width = map_width
        self.map_height = map_height
        
        self.max_rooms = max_rooms
        
        self.room_min_size = room_min_size
        self.room_max_size = room_max_size
        
        self.current_floor = current_floor
        
    def generate_floor(self) -> None:
        pass