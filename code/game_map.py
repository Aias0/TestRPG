from __future__ import annotations
from typing import Iterable, TYPE_CHECKING, Optional, Iterator

import numpy as np # type: ignore
from tcod.console import Console

import tile_types
from sprite import Sprite, Actor

if TYPE_CHECKING:
    from engine import Engine

class GameMap:
    def __init__(
        self, engine: Engine, width: int, height: int, sprites: Iterable[Sprite] = ()
    ) -> None:
        self.engine = engine
        self.width, self.height = width, height
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order='F')
        self.sprites = set(sprites)
        
        self.visible = np.full(
            (width, height), fill_value=False, order='F'
        ) # Tiles the player can currently see
        self.explored = np.full(
            (width, height), fill_value=False, order='F'
        ) # Tiles the player has seen before
        
    @property
    def actors(self) -> Iterator[Actor]:
        """ Iterate over this maps living actors. """
        yield from (
            sprite for sprite in self.sprites
            if isinstance(sprite, Actor) and sprite.is_alive
        )
        
    def get_blocking_sprite_at_location(
        self, location_x: int, location_y: int
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
        
    def in_bounds(self, x: int, y:int) -> bool:
        """Return True if x and y are inside of the bounds of this map."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def render(self, console: Console) -> None:
        """
        Renders the map.

        If a tile is in the "visible" array, then draw it with the "light" colors.
        If it isn't, but it's in the "explored" array, then draw it with the "dark" colors.
        Otherwise, the default is "SHROUD".
        """
        console.rgb[0:self.width, 0:self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles['light'], self.tiles['dark']],
            default=tile_types.SHROUD,
        )
        
        for sprite in self.sprites:
            # Only print sprite that are in the FOV
            if self.visible[sprite.x, sprite.y]:
                console.print(x=sprite.x, y=sprite.y, string=sprite.char, fg=sprite.color)