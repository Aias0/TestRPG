from __future__ import annotations
from typing import TYPE_CHECKING
from main import logger


if TYPE_CHECKING:
    from engine import Engine
    from world import GameMap
    from sprite import Sprite, Actor
    from ai import BaseAI

class Entity():
    parent: Sprite
    
    def __init__(
        self,
        name:str,
        value:int,
        description:str = None,
        tags: set[str] = set(),
        providing_parent: bool = False,
        interactable: bool = False,
    ) -> None:
        self.name = name
        self.description = description

        self.value = value
        
        self.tags = tags
        self.interactable = interactable
        
        if not providing_parent:
            # Create a sprite here
            pass
            
    @property
    def display_name(self) -> str:
        return self.name
        
    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap
        
    @property
    def engine(self) -> Engine:
        return self.gamemap.engine
        
    def update(self) -> bool:
        pass
    
    def turn_end(self) -> None:
        pass
    
    def interact(self, character: None | None = None) -> bool:
        raise NotImplementedError()
        
    def __str__(self) -> str:
        return f'{self.name}'
    def __repr__(self):
        return self.__str__()
    
    def similar(self, other, bug = False) -> bool:
        if isinstance(other, self.__class__):
            for i, pair in enumerate(zip(
                [_[1] for _ in vars(self).items() if (_[0] != 'parent' and _[0] != 'holder')],
                [_[1] for _ in vars(other).items() if (_[0] != 'parent' and _[0] != 'holder')]
            )):
                if hasattr(pair[0], 'similar') and not pair[0].similar(pair[1]):
                    return False
                elif not hasattr(pair[0], 'similar') and pair[0] != pair[1]:
                    return False
                
            return True
        return False
    
class Item(Entity):
    pass

class Character(Entity):
    parent: Actor
    
    def __init__(
        self,
        name: str,
        value: int,
        description: str = None,
        tags: set[str] = set(),
        providing_parent: TYPE_CHECKING = False,
        interactable: TYPE_CHECKING = False
    ) -> None:
        super().__init__(
            name=name,
            value=value,
            description=description,
            tags=tags,
            providing_parent=providing_parent,
            interactable=interactable
        )
        
        self.hp = 10
        self.mp = 10
        self.sp = 10
        
        
        self.ai: BaseAI = None