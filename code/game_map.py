from __future__ import annotations
from typing import Iterable, TYPE_CHECKING, Optional, Iterator, List

import numpy as np # type: ignore
from tcod.console import Console

import tile_types
from sprite import Sprite, Actor
from entity import Corpse, Item

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
        
        self.remembered_sprites: list[list[str | tuple | int | int | Sprite]] = []
        
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
        
    @property
    def items(self) -> Iterator[Sprite]:
        yield from (
            sprite for sprite in self.sprites
            if isinstance(sprite.entity, Item)
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
            if actor.x == x and actor.y == y and not isinstance(actor.entity, Corpse):
                return actor
        
        return None
    
    def get_actors_in_range(self, x: int, y: int, radius: int) -> List[Actor]:
        actors_in_range: List[Actor] = []
        for actor in self.actors:
            if actor.distance(x, y) <= radius:
                actors_in_range.append(actor)
        return actors_in_range
        
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
        
        sprites_sorted_for_rendering = sorted(
            self.sprites, key=lambda x: x.render_order.value
        )
        
        for sprite in sprites_sorted_for_rendering:
            
            if self.remembered_sprites:
                _,_,_,_,sprites_remembered = zip(*self.remembered_sprites)
            else:
                sprites_remembered: list[Sprite] = []
            sprites_remembered: list[Sprite]
            
            # Only print sprite that are in the FOV
            if self.visible[sprite.x, sprite.y] or self.engine.wallhacks:
                console.print(
                    x=sprite.x, y=sprite.y, string=sprite.char, fg=sprite.color
                )
                
                #Remember sprites seen
                #if sprite has already been then reset memory counter
                if not sprite in sprites_remembered and sprite != self.engine.player:
                    self.remembered_sprites.append([sprite.char, sprite.x, sprite.y, self.engine.turn_count, sprite])
                elif sprite != self.engine.player:
                    self.remembered_sprites[sprites_remembered.index(sprite)] = [sprite.char, sprite.x, sprite.y, self.engine.turn_count, sprite]
                    
            elif sprite in sprites_remembered:
                remembered_sprite = self.remembered_sprites[sprites_remembered.index(sprite)]
                console.print(
                    x=remembered_sprite[1], y=remembered_sprite[2], string=remembered_sprite[0], fg=sprite.color
                )
                if self.remembered_sprites[sprites_remembered.index(sprite)][3] == self.engine.turn_count-1:
                    self.remembered_sprites[sprites_remembered.index(sprite)][3] += 1
                
        for remembered_sprite in self.remembered_sprites:
            if not 'keen mind' in self.engine.player.entity.tags and self.engine.turn_count-remembered_sprite[3] > self.engine.player.entity.INT//2:
                self.remembered_sprites.remove(remembered_sprite)