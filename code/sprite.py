from __future__ import annotations
from typing import TYPE_CHECKING, Tuple

from render_order import RenderOrder

if TYPE_CHECKING:
    from entity import Entity, Character

class Sprite():
    def __init__(
        self,
        entity: Entity,
        char: str = '?',
        x: int = 0,
        y: int = 0,
        color: Tuple[int, int, int] = (255, 255, 255),
        blocks_movement: bool = False,
        render_order: RenderOrder = RenderOrder.CORPSE,
        pickupable:bool = True
        ) -> None:

        self.entity = entity
        self.char = char
        self.x = x
        self.y = y
        self.color = color
        self.blocks_movement = blocks_movement
        self.render_order = render_order
        self.pickupable = pickupable
        
        self.entity.parent = self
        
    def spawn(self):
        """Spawn a copy of this instance at the given location."""
        pass
    
    def place(self):
        """Place this entity at a new location.  Handles moving across GameMaps."""
        pass
    
    def distance(self):
        """Return the distance between the current entity and the given (x, y) coordinate."""
        pass
    
    def move(self, dx: int, dy: int) -> None:
        # Move the entity by a given amount
        self.x += dx
        self.y += dy
        
    def __str__(self) -> str:
        return f'{self.char}({self.color}) | {self.entity.name}'
    def __repr__(self):
        return f'({self.__str__()})'

class Actor(Sprite):
    def __init__(
        self,
        character: Character,
        char: str = '?',
        x: int = 0,
        y: int = 0,
        color: Tuple[int, int, int] = (255, 255, 255),
        blocks_movement: bool = True,
        render_order: RenderOrder = RenderOrder.ACTOR,
        ai = None,
        hostile = False
        ) -> None:
        
        super().__init__(
            entity=character,
            char=char,
            x=x,
            y=y,
            color=color,
            blocks_movement=blocks_movement,
            render_order=render_order,
            pickupable=False,
            )
        self.entity: Character
        
        self.ai = ai
        self.entity.parent = self
        
        self.hostile = hostile

        
    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai)