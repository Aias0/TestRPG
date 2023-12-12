from __future__ import annotations
from typing import TYPE_CHECKING, List, Iterable

from enum import auto, Enum

if TYPE_CHECKING:
    from entity import Item

class ItemTypes(Enum):
    UNKNOWN = auto()
    
    MISCELLANEOUS = auto()
    
    POTION = auto()
    SCROLL = auto()
    
    SWORD = auto()
    SHIELD = auto()
    
    HEAD_ARMOR = auto()
    CHEST_ARMOR = auto()
    LEG_ARMOR = auto()
    FOOT_ARMOR = auto()
    HAND_ARMOR = auto()
    
    RING = auto()
    
    @staticmethod
    def weapons() -> set:
        return {ItemTypes.SWORD}
    def is_weapon(item: Item) -> bool:
        return item.itemtype in ItemTypes.weapons()
    
    @staticmethod
    def armors() -> set:
        return {ItemTypes.HEAD_ARMOR, ItemTypes.CHEST_ARMOR, ItemTypes.LEG_ARMOR, ItemTypes.FOOT_ARMOR, ItemTypes.HAND_ARMOR}
    def is_armor(item: Item) -> bool:
        return item.itemtype in ItemTypes.armors()
    
    @staticmethod
    def accessories() -> set:
        return {ItemTypes.RING}
    def is_accessory(item: Item) -> bool:
        return item.itemtype in ItemTypes.accessories()
    
    @staticmethod
    def consumables() -> set:
        return {ItemTypes.POTION, ItemTypes.SCROLL}
    def is_consumable(item: Item) -> bool:
        return item.itemtype in ItemTypes.consumables()