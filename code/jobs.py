from __future__ import annotations
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from entity import Character

class BaseJob():
    parent: Character
    def __init__(self, name: str, base_chance: int = 10) -> None:
        self.name = name
        self.base_chance = base_chance

class Mage(BaseJob):
    def __init__(self) -> None:
        super().__init__(name='Mage', base_chance= 5)

class Rouge(BaseJob):
    def __init__(self) -> None:
        super().__init__(name='Rouge')

class Fighter(BaseJob):
    def __init__(self) -> None:
        super().__init__(name='Fighter', base_chance= 15)
        
JOBS: List[BaseJob] = [Mage(), Rouge(), Fighter()]