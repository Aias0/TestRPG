from __future__ import annotations
from typing import TYPE_CHECKING, List

from enum import auto, Enum

class ItemTypes(Enum):
    UNKNOWN = auto()
    
    MISCELLANEOUS = auto()
    
    POTION = auto()
    SCROLL = auto()
    
    SWORD = auto()
    SHEILD = auto()
    
    HEAD_ARMOR = auto()
    CHEST_ARMOR = auto()
    LEG_ARMOR = auto()
    FOOT_ARMOR = auto()
    HAND_ARMOR = auto()
    
    RING = auto()
    
    @property
    def weapons() -> list:
        return [ItemTypes.SWORD]
    def is_weapon(itemtype) -> bool:
        return itemtype in ItemTypes.weapons
    
    @property
    def armors() -> list:
        return [ItemTypes.HEAD_ARMOR, ItemTypes.CHEST_ARMOR, ItemTypes.LEG_ARMOR, ItemTypes.FOOT_ARMOR, ItemTypes.HAND_ARMOR]
    def is_armor(itemtype) -> bool:
        return itemtype in ItemTypes.armors
    
    @property
    def accessories() -> list:
        return [ItemTypes.RING]
    def is_accessory(itemtype) -> bool:
        return itemtype in ItemTypes.accessories
    
    @property
    def consumables() -> list:
        return [ItemTypes.POTION, ItemTypes.SCROLL]
    def is_consumable(itemtype) -> bool:
        return itemtype in ItemTypes.consumables