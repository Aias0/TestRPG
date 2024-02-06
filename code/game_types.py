from __future__ import annotations
from typing import TYPE_CHECKING

from enum import auto, Enum

if TYPE_CHECKING:
    from entity import Item

class ItemTypes(Enum):
    UNKNOWN = auto()
    
    MISCELLANEOUS = auto()
    CORPSE = auto()
    
    POTION = auto()
    SCROLL = auto()
    KEY = auto()
    
    SWORD = auto()
    DAGGER = auto()
    
    SHIELD = auto()
    
    STAFF = auto()
    
    HEAD_ARMOR = auto()
    CHEST_ARMOR = auto()
    LEG_ARMOR = auto()
    FOOT_ARMOR = auto()
    HAND_ARMOR = auto()
    
    RING = auto()
    AMULET = auto()
    
    @staticmethod
    def melee_weapons() -> set:
        return {ItemTypes.SWORD, ItemTypes.DAGGER}
    def is_melee_weapons(item: Item) -> bool:
        return item.itemtype in ItemTypes.melee_weapons()
    @staticmethod
    def ranged_weapons() -> set:
        return set()
    def is_ranged_weapons(item: Item) -> bool:
        return item.itemtype in ItemTypes.ranged_weapons()
    @staticmethod
    def magic_weapons() -> set:
        return {ItemTypes.STAFF, }
    def is_magic_weapon(item: Item) -> bool:
        return item.itemtype in ItemTypes.magic_weapons()
    @staticmethod
    def weapons() -> set:
        s = set()
        s.update(ItemTypes.melee_weapons())
        s.update(ItemTypes.ranged_weapons())
        s.update(ItemTypes.magic_weapons())
        return s
    def is_weapon(item: Item):
        return item.itemtype in ItemTypes.weapons()
    
    @staticmethod
    def armors() -> set:
        return {ItemTypes.HEAD_ARMOR, ItemTypes.CHEST_ARMOR, ItemTypes.LEG_ARMOR, ItemTypes.FOOT_ARMOR, ItemTypes.HAND_ARMOR}
    def is_armor(item: Item) -> bool:
        return item.itemtype in ItemTypes.armors()
    
    @staticmethod
    def accessories() -> set:
        return {ItemTypes.RING, ItemTypes.AMULET}
    def is_accessory(item: Item) -> bool:
        return item.itemtype in ItemTypes.accessories()
    
    @staticmethod
    def useable() -> set:
        return {ItemTypes.POTION, ItemTypes.SCROLL}
    def is_useable(item: Item) -> bool:
        return item.itemtype in ItemTypes.useable()
    
class ItemSubTypes(Enum):
    SHORT_SWORD = auto()
    
    HEAVY_ARMOR = auto()
    MEDIUM_ARMOR = auto()
    LIGHT_ARMOR = auto()
    
    CLOTHING = auto()

class MagicFocusTypes(Enum):
    BALANCE = auto()
    
    POWER = auto()
    PRECISION = auto()
    EFFICIENCY = auto()
    
class DamageTypes(Enum):
    PHYS = auto()
    MAGC = auto()
    
    TRUE = auto()
    
class ElementTypes(Enum):
    NONE = auto()
    
    FIRE = auto()
    WATER = auto()
    AIR = auto()
    EARTH = auto()
    
    LIGHTNING = auto()
    ICE = auto()
    
    POISON = auto()
    
    @staticmethod
    def elements() -> set:
        return {ElementTypes.FIRE, ElementTypes.WATER, ElementTypes.AIR, ElementTypes.EARTH, ElementTypes.LIGHTNING, ElementTypes.ICE, ElementTypes.POISON}
    
class MaterialTypes(Enum):
    METAL = auto()
    GLASS = auto()
    STONE = auto()
    
    BIOLOGICAL = auto()
    NON_BIOLOGICAL = auto()
    
class GameTypeNames:
    damagetype_to_name = {DamageTypes.PHYS: 'physical', DamageTypes.MAGC: 'magical', DamageTypes.TRUE: 'true'}
    elementtype_to_name = {ElementTypes.FIRE: 'fire', ElementTypes.WATER: 'water', ElementTypes.AIR: 'air', ElementTypes.EARTH: 'earth', ElementTypes.POISON: 'poison', ElementTypes.LIGHTNING: 'lightning', ElementTypes.ICE: 'ice'}
    magicfocustypes_to_name = {MagicFocusTypes.BALANCE: 'balance', MagicFocusTypes.POWER: 'power', MagicFocusTypes.PRECISION: 'precision', MagicFocusTypes.EFFICIENCY: 'efficiency'}