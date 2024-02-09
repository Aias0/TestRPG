from __future__ import annotations
from typing import TYPE_CHECKING, Iterator, Tuple, List

import random

from game_map import GameMap
import tile_types

import tcod

import numpy as np

from spritegen import gen_enemies, gen_items, entity_to_sprite

from values import LockValues

import game_types

if TYPE_CHECKING:
    from engine import Engine
    from sprite import Actor, Sprite
    from entity import Door

class Room:
    @property
    def center(self) -> Tuple[int, int]:
        """ Return center of room. """
        raise NotImplementedError()
    
    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        raise NotImplementedError()
    
    def intersects(self, other: Room) -> bool:
        """Return True if this room overlaps with another Room."""
        raise NotImplementedError()
    
    def point_in(self, point: tuple) -> bool:
        """ Return True if point is in room. """
        raise NotImplementedError()
    

class RectangularRoom(Room):
    def __init__(self, x: int, y: int, width: int, height: int, safe: bool = False) -> None:
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height
        self.safe = safe
        
    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)
        
        return center_x, center_y
    
    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)
    
    @property
    def outer(self) -> List[Tuple[int, int]]:
        points: List[Tuple[int, int]] = []
        for i in range(self.x1, self.x2):
            points.append((i, self.y1))
            points.append((i, self.y2))
        for i in range(self.y1, self.y2):
            points.append((self.x1, i))
            points.append((self.x2, i))
            
        return points
    
    def random_place(self, dungeon: GameMap, sprite: Sprite):
        while True:
            loc = random.randint(1, dungeon.width-1), random.randint(1, dungeon.height-1)
            
            if dungeon.tiles[*loc]['walkable'] and not any(sprite.x == loc[0] and sprite.y == loc[1] for sprite in dungeon.sprites):
                sprite.place(*loc, dungeon)
                break
                
    
    def place_doors(self, dungeon:GameMap, chance: float = .5, open_chance: float = .25, lock_chance: float = .05) -> None:
        surrounding_points = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
        from sprite_data import door
        for point in self.outer:
            if dungeon.tiles[point] != tile_types.floor:
                continue
            
            door_around = False
            for s_point in surrounding_points:
                if isinstance(dungeon.get_sprite_at_location(point[0]+s_point[0], point[1]+s_point[1]), door.__class__):
                    door_around = True
            if door_around:
                continue
            if (dungeon.tiles[tuple(np.add(point, (0, 1)))] == tile_types.wall and dungeon.tiles[tuple(np.add(point, (0, -1)))] == tile_types.wall) or (dungeon.tiles[tuple(np.add(point, (1, 0)))] == tile_types.wall and dungeon.tiles[tuple(np.add(point, (-1, 0)))] == tile_types.wall):
                if random.random() < chance:
                    new_door: Door = door.spawn(dungeon, *point).entity
                    if random.random() > open_chance:
                        new_door.close()
                    else:
                        new_door.open()
                    if random.random() < lock_chance:
                        lock_val = LockValues.new_lock()[0]
                        new_door.lock(lock_val)
                        from entity import Item
                        from entity_effect import KeyEffect
                        key_item = Item(
                            'Rusty Key',
                            0,
                            1,
                            itemtype=game_types.ItemTypes.KEY,
                            effect=KeyEffect(lock_val),
                            color=(200,)*3
                        )
                        self.random_place(dungeon, entity_to_sprite(key_item))
    
    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )
        
    def point_in(self, point: tuple) -> bool:
        """ Return True if point is in room. """
        return (
            self.x1 <= point[0]
            and self.x2 >= point[0]
            and self.y1 <= point[1]
            and self.y2 >= point[1]
        )
        
def place_sprites(
    room: RectangularRoom, dungeon: GameMap, sprites: List[Sprite]
) -> None:
        
    for new_sprite in sprites:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)
        
        if not any(sprite.x == x and sprite.y == y for sprite in dungeon.sprites):
            new_sprite.place(x, y, dungeon)
        
def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2
    
    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y
        
def generate_dungeon_floor(
    max_rooms: int | tuple,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    enemies_per_room_range: int | list,
    items_per_room_range: int | list,
    engine: Engine,
    floor_level: int,
) -> GameMap:
    """ Generate a new dungeon map. """
    if isinstance(max_rooms, int):
        max_room_range = [max_rooms,]*2
    else:
        max_room_range = list(max_rooms)
    max_room_range[1] += 1
    
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, floor_level=floor_level, sprites=[player])
    
    rooms: List[RectangularRoom] = []
    
    center_of_last_room = (0, 0)
    
    num_rooms = random.randrange(max_room_range[0], max_room_range[1])
    for r in range(num_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)
        
        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)
        
        # "RectangularRoom" class makes rectangles easier to work with
        new_room = RectangularRoom(x, y, room_width, room_height)
        
        # Run through the other rooms and see if they intersect with this one.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue # This room intersects, so go to the next attempt.
        # If there are no intersections then the room is valid.
        
        # Dig out this rooms inner area.
        dungeon.tiles[new_room.inner] = tile_types.floor
        
        if len(rooms) == 0:
            # The first room, where the player starts.
            player.place(*new_room.center, dungeon)
            new_room.safe = True
            
            center_of_first_room = new_room.center
        else: # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            for x, y, in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor
                
            center_of_last_room = new_room.center
            
        

        sprites: List[Sprite] = gen_items(item_num=items_per_room_range)
        if not new_room.safe:
            sprites.extend(gen_enemies(enemy_num=enemies_per_room_range))
        place_sprites(new_room, dungeon, sprites)
        
        # Finally, append the new room to the list.
        rooms.append(new_room)
        
    dungeon.tiles[center_of_last_room] = tile_types.down_stairs
    dungeon.down_stairs_location = center_of_last_room
    
    if dungeon.floor_level > 1:
        dungeon.tiles[center_of_first_room] = tile_types.up_stairs
        dungeon.up_stairs_location = center_of_first_room
        
    for room in rooms:
        room.place_doors(dungeon)
    
    return dungeon
