from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from entity import Character

class BaseJob():
    parent: Character
    def __init__(self, name: str, default_color: Tuple[int, int, int],rarity: int = 10) -> None:
        self.name = name
        self.default_color = default_color
        self.rarity = rarity

class Mage(BaseJob):
    def __init__(self) -> None:
        super().__init__(name='Mage', default_color=[0, 0, 255], rarity= 5)

class Rouge(BaseJob):
    def __init__(self) -> None:
        super().__init__(name='Rouge', default_color=[0, 255, 0])

class Fighter(BaseJob):
    def __init__(self) -> None:
        super().__init__(name='Fighter', default_color=[255, 0, 0], rarity= 15)
        
JOBS: List[BaseJob] = [Mage(), Rouge(), Fighter()]