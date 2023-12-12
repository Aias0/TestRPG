from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from entity import Character

class BaseJob():
    parent: Character
    def __init__(self, name: str, default_color: Tuple[int, int, int],base_chance: int = 10) -> None:
        self.name = name
        self.default_color = default_color
        self.base_chance = base_chance

class Mage(BaseJob):
    def __init__(self) -> None:
        super().__init__(name='Mage', default_color=[0, 0, 255], base_chance= 5)

class Rouge(BaseJob):
    def __init__(self) -> None:
        super().__init__(name='Rouge', default_color=[0, 255, 0])

class Fighter(BaseJob):
    def __init__(self) -> None:
        super().__init__(name='Fighter', default_color=[255, 0, 0], base_chance= 15)
        
JOBS: List[BaseJob] = [Mage(), Rouge(), Fighter()]