from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Optional

import copy, math

from refactor.entity import Entity
from refactor.world import GameMap

if TYPE_CHECKING:
    from world import GameMap
    from entity import Entity, Character
    from ai import BaseAI

T = TypeVar("T", bound="Sprite")

class Sprite():
    """
    A generic object to represent actor, items, etc.
    """
    
    parent: GameMap
    
    def __init__(
        self,
        entity: Entity,
        parent: GameMap | None = None,
        char: str = '?',
        x: int = 0,
        y: int = 0,
        color: tuple[int, int, int] = (255, 255, 255),
        blocks_movement: bool = False,
        render_order = None,
        pickupable:bool = True,
        blocks_fov: bool = False,
        ) -> None:

        self.entity = entity
        self.char = char
        self.x = x
        self.y = y
        self.color = color
        self.blocks_movement = blocks_movement
        self.render_order = render_order
        self.pickupable = pickupable
        self.blocks_fov = blocks_fov
        
        self.entity.parent = self
        
        if parent:
            # If parent isn't provided now then it will be set later.
            self.parent = parent
            parent.sprites.add(self)
            
    @property
    def gamemap(self) -> GameMap:
        return self.parent
    
    @property
    def name(self) -> str:
        return self.entity.name
        
    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """Spawn a copy of this instance at the given location."""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.sprites.add(clone)
        return clone
    
    def place(self, x: int, y: int, gamemap: GameMap | None) -> None:
        """Place this entity at a new location.  Handles moving across GameMaps."""
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, 'parent'): # Possibly uninitialized.
                if self.parent is self.gamemap:
                    self.gamemap.sprites.remove(self)
            self.parent = gamemap
            gamemap.sprites.add(self)
    
    def distance(self, x: int, y: int):
        """Return the distance between the current entity and the given (x, y) coordinate."""
        return math.sqrt((x-self.x)**2 + (y-self.y)**2)
    
    def move(self, dx: int, dy: int) -> None:
        # Move the entity by a given amount
        self.x += dx
        self.y += dy
        
    def __str__(self) -> str:
        return f'{self.char}({str(self.color)[1:-1]}): {self.name}'
    def __repr__(self):
        return f'{self.__str__()}'
    
    def similar(self, other):
        if isinstance(other, self.__class__):
            for i, pair in enumerate(zip([_[1] for _ in vars(self).items() if _[0] != 'parent'], [_[1] for _ in vars(other).items() if _[0] != 'parent'])):
                if hasattr(pair[0], 'similar') and not pair[0].similar(pair[1]):
                    return False
                elif not hasattr(pair[0], 'similar') and pair[0] != pair[1]:
                    return False
                
            return True
        
        
class Actor(Sprite):
    entity: Character
    def __init__(
        self,
        character: Character,
        char: str = '?',
        x: int = 0,
        y: int = 0,
        color: tuple[int, int, int] = (255, 255, 255),
        blocks_movement: bool = True,
        ai_cls: type[BaseAI] = None,
        hostile = False
    ) -> None:
        super().__init__(
            entity=character,
            char=char,
            x=x,
            y=y,
            color=color,
            blocks_movement=blocks_movement,
            render_order= RenderOrder.ACTOR,
            pickupable=False,
            )
        
        self.entity: Character
        self.entity.parent = self
        
        if ai_cls:
            self.ai: Optional[BaseAI] = ai_cls(self)
            
        self.hostile = hostile

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai)