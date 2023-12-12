from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple

import random

if TYPE_CHECKING:
    from game_map import GameMap
    from sprite import Actor, Sprite

def get_max_value_for_floor(
    max_value_by_floor: List[Tuple(int, int)], floor: int
) -> int:
    current_value = 0
    
    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value
            
    return current_value

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
        
def place_sprites(room: Room, gamemap: GameMap, floor_number: int) -> None:
    number_of_enemies = random.randint(
        0, get_max_value_for_floor()
    )
    number_of_items = random.randint(
        0, get_max_value_for_floor()
    )
    enemies: List[Actor]