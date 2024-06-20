from __future__ import annotations
from typing import TYPE_CHECKING, Iterator, Iterable
from main import logger

import tcod

if TYPE_CHECKING:
    from engine import Engine
    from sprite import Actor, Sprite
    from entity import Item

class GameMap:
    game_world: GameWorld
    
    def __init__(self, width: int, height: int, floor_level: int, sprites: Iterable[Sprite] = ()) -> None:
        self.width, self.height = width, height
        
        self.floor_level = floor_level
        
        self.sprites: Iterable[Sprite] = set()
    
    
    @property
    def actors(self) -> Iterator[Actor]:
        """ Iterate over this maps living actors. """
        from sprite import Actor
        yield from (
            sprite for sprite in self.sprites
            if isinstance(sprite, Actor) and sprite.is_alive
        )
        
    @property
    def items(self) -> Iterator[Item]:
        """ Iterate over this maps items. """
        from entity import Item
        yield from (
            sprite for sprite in self.sprites
            if isinstance(sprite.entity, Item)
        )
        
    @property
    def engine(self) -> Engine:
        return self.game_world.engine
    
    @property
    def parent(self) -> GameWorld:
        return self.game_world
    
    def get_sprites_at_location(self, x: int, y: int, exclude: set[Sprite] = set()) -> list[Sprite]:
        sprites_at_loc = []
        for sprite in self.sprites - exclude:
            if sprite.x == x and sprite.y == y:
                sprites_at_loc.append(sprite)
               
        return sprites_at_loc
    
    def get_sprite_at_location(self, x: int, y: int, exclude: set[Sprite] = set()) -> Sprite | None:
        for sprite in self.sprites - exclude:
            if sprite.x == x and sprite.y == y:
                return sprite
        
        return None
    
    
    def get_actors_at_location(self, x: int, y: int, exclude: set[Actor] = set()) -> list[Actor]:
        from sprite import Actor
        
        sprites = self.get_sprites_at_location(x, y, exclude)
        return [sprite for sprite in sprites if isinstance(sprite, Actor)]
    
    def get_actor_at_location(self, x: int, y: int, exclude: set[Actor] = set()) -> Actor | None:
        from sprite import Actor
        
        for sprite in self.sprites - exclude:
            if sprite.x == x and sprite.y == y and isinstance(sprite, Actor):
                return sprite
        
        return None
    
    
    def get_items_at_location(self, x: int, y: int, exclude: set[Sprite] = set()) -> list[Sprite]:
        from entity import Item
        
        sprites = self.get_sprites_at_location(x, y, exclude)
        return [sprite for sprite in sprites if isinstance(sprite.entity, Item)]
    
    def get_item_at_location(self, x: int, y: int, exclude: set[Sprite] = set()) -> Item:
        from entity import Item
        for sprite in self.sprites - exclude:
            if sprite.x == x and sprite.y == y and isinstance(sprite.entity, Item):
                return sprite
        
        return None
    
    
    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if x and y are inside of the bounds of this map."""
        return 0 <= x < self.width and 0 <= y < self.height

class GameWorld:
    
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        
        self.game_maps: list[GameMap] = []
        self.current_game_map: GameMap = None
        
    @property
    def actors(self) -> Iterator[Actor]:
        """ Iterate over all living actors on a gamemap. """
        from sprite import Actor
        yield from (
            sprite for sprite in self.sprites
            if isinstance(sprite, Actor) and sprite.is_alive
        )
        
    @property
    def items(self) -> Iterator[Item]:
        """ Iterate over all items on a gamemap. """
        from entity import Item
        yield from (
            sprite for sprite in self.sprites
            if isinstance(sprite.entity, Item)
        )
        
    @property
    def sprites(self) -> Iterator[Sprite]:
        """ Iterate over all sprites on a gamemap. """
        yield from (
            sprite for sprite in set().union(*(game_map.sprites for game_map in self.game_maps))
        )