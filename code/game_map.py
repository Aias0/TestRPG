from __future__ import annotations
from typing import Iterable, TYPE_CHECKING, Optional, Iterator, List

import numpy as np # type: ignore
from tcod.console import Console

import color

import tile_types
from sprite import Sprite, Actor
from entity import Corpse, Item

if TYPE_CHECKING:
    from engine import Engine

class GameMap:
    def __init__(
        self, engine: Engine, width: int, height: int, floor_level: int = 0, sprites: Iterable[Sprite] = ()
    ) -> None:
        self.engine = engine
        self.width, self.height = width, height
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order='F')
        self.sprites = set(sprites)
        
        self.floor_level = floor_level
        
        self.remembered_sprites: list[list[str | tuple | int | int | Sprite]] = []
        
        self.visible = np.full(
            (width, height), fill_value=False, order='F'
        ) # Tiles the player can currently see
        self.explored = np.full(
            (width, height), fill_value=False, order='F'
        ) # Tiles the player has seen before
        
        self.down_stairs_location = (0, 0)
        self.up_stairs_location = (0, 0)
    
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
    
    def get_sprite_at_location(self, x: int, y: int, exclude: set[Sprite] = set()) -> Optional[Sprite]:
        for sprite in self.sprites - exclude:
            if sprite.x == x and sprite.y == y:
                return sprite
        
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
                if console.rgb[sprite.x, sprite.y][0] not in [ord(" "), ord(">"), ord("<")] and isinstance(sprite.entity, Item):
                    console.print(
                    x=sprite.x, y=sprite.y, string='#', fg=color.white
                    )
                else:
                    console.print(
                        x=sprite.x, y=sprite.y, string=sprite.char, fg=sprite.color
                    )
                
                #Remember sprites seen
                #if sprite has already been then update it's last seen turn
                if not sprite in sprites_remembered and sprite != self.engine.player:
                    self.remembered_sprites.append([sprite.char, sprite.x, sprite.y, self.engine.turn_count, sprite])
                elif sprite != self.engine.player:
                    self.remembered_sprites[sprites_remembered.index(sprite)] = [sprite.char, sprite.x, sprite.y, self.engine.turn_count, sprite]
            
            # Print sprite's in memory
            elif sprite in sprites_remembered:
                if self.visible[sprite.x, sprite.y]:
                    continue
                
                remembered_sprite = self.remembered_sprites[sprites_remembered.index(sprite)]
                if console.rgb[sprite.x, sprite.y][0] not in [ord(" "), ord(">"), ord("<")] and isinstance(sprite.entity, Item):
                    console.print(
                    x=sprite.x, y=sprite.y, string='#', fg=color.white
                    )
                else:
                    console.print(
                        x=remembered_sprite[1], y=remembered_sprite[2], string=remembered_sprite[0], fg=sprite.color
                    )
        
        for remembered_sprite in self.remembered_sprites:
            #print(self.engine.turn_count, remembered_sprite[3], self.engine.player.entity.INT//2)
            if not 'keen mind' in self.engine.player.entity.tags and self.engine.turn_count-remembered_sprite[3] > self.engine.player.entity.INT:
                self.remembered_sprites.remove(remembered_sprite)
                
class GameLocation:
    """ Holds the settings for the GameMap, and generates new maps when moving down the stairs. """
    
    def __init__(
        self,
        *,
        engine: Engine,
        map_width: int,
        map_height: int,
        room_max_size: int,
        room_min_size: int,
        max_room_range: list,
        max_enemies_per_room: list,
        max_items_per_room: list,
        current_floor: int = 1,
        
    ) -> None:
        self.engine = engine
        
        self.map_width = map_width
        self.map_height = map_height
        
        self.max_room_range = max_room_range
        self.room_max_size = room_max_size
        self.room_min_size = room_min_size
        
        self.max_enemies_per_room = max_enemies_per_room
        self.max_items_per_room = max_items_per_room
        
        self.current_floor = current_floor
        
        self.maps: list[GameMap] = []
        
    def go_up(self) -> None:
        map_up = [gmap for gmap in self.maps if gmap.floor_level == self.current_floor-1]
        if map_up:
            self.current_floor -= 1
            self.engine.game_map = map_up[0]
            self.engine.player.x, self.engine.player.y = self.engine.game_map.down_stairs_location
            self.engine.game_map.sprites.add(self.engine.player)
            return True
        else:
            print('No map above.')
            return False
            
    def go_down(self, generate_floor: bool = True) -> None:
        map_down = [gmap for gmap in self.maps if gmap.floor_level == self.current_floor+1]
        if map_down:
            self.current_floor += 1
            self.engine.game_map = map_down[0]
            self.engine.player.x, self.engine.player.y = self.engine.game_map.up_stairs_location
            self.engine.game_map.sprites.add(self.engine.player)
            return True
        elif generate_floor:
            self.current_floor += 1
            self.generate_floor()
            return True
        else:
            print('No map bellow.')
            return False
            
        
    def generate_floor(self) -> None:
        from mapgen import generate_dungeon_floor
        self.engine.game_map = generate_dungeon_floor(
            max_rooms= self.max_room_range,
            room_min_size=self.room_min_size,
            room_max_size=self.room_max_size,
            map_width=self.map_width,
            map_height=self.map_height,
            enemies_per_room_range=self.max_enemies_per_room,
            items_per_room_range=self.max_items_per_room,
            engine=self.engine,
            floor_level = self.current_floor
        )
        
        self.maps.append(self.engine.game_map)
    
class GameWorld:
    def __init__(self) -> None:
        self.over_world_map: GameMap = None
        
        self.dungeons: List[GameLocation] = None