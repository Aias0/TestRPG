from __future__ import annotations
from typing import TYPE_CHECKING

from enum import auto, Enum

if TYPE_CHECKING:
    from entity import Entity

class _KeyLock(Enum):
    ARCANE_LOCK = auto()
    
class LockValues:
    lock_vals: dict = {}
    for i in _KeyLock:
        lock_vals[i.name] = i.value
        
    @classmethod
    def new_lock(self, *, name: str | None = None, key: int = None) -> tuple[str, int]:
        
        if key is None:
            key = list(self.lock_vals.values())[-1]+1
            
        if key in self.lock_vals.values():
            raise KeyError(f'Key{key} already in lock values.')
        if not name:
            name = f'Lock{key}'
        self.lock_vals[name] = key
        
        return (name, key)
            