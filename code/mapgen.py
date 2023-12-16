from __future__ import annotations
from typing import TYPE_CHECKING, Iterator, Tuple, List

import random

from game_map import GameMap
import tile_types

import tcod

from spritegen import gen_enemies

if TYPE_CHECKING:
    from engine import Engine
    from sprite import Actor, Sprite

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
    engine: Engine,
) -> GameMap:
    """ Generate a new dungeon map. """
    if isinstance(max_rooms, int):
        max_room_range = [max_rooms,]*2
    else:
        max_room_range = list(max_rooms)
    max_room_range[1] += 1
    
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, sprites=[player])
    
    rooms: List[RectangularRoom] = []
    
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
        else: # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            for x, y, in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

        if not new_room.safe:
            sprites = gen_enemies(enemy_num=enemies_per_room_range)
            place_sprites(new_room, dungeon, sprites)
        
        # Finally, append the new room to the list.
        rooms.append(new_room)
    
    return dungeon
