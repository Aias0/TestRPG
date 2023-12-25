from __future__ import annotations
from typing import TYPE_CHECKING

from entity import Item
from entity_effect import ItemEffect, HealingEffect, ScrollEffect

from magic import LightningBolt

from game_types import ItemTypes

health_potion = Item(
    'Health Potion', 100, 1, itemtype=ItemTypes.POTION, effect=HealingEffect(amount=4), rarity= 25
)

sword = Item(
    'Sword', 5, 6, itemtype=ItemTypes.SWORD, effect=ItemEffect(phys_atk_bonus=2)
)

chest_plate = Item(
    'Chest plate', 10, 12, itemtype=ItemTypes.CHEST_ARMOR, effect=ItemEffect(phys_defense_bonus=5, phys_negation_bonus=2)
)

lightning_bolt_scroll = Item(
    'Lightning Bolt Scroll', 200, 1, itemtype=ItemTypes.SCROLL, effect=ScrollEffect(LightningBolt()), rarity=5
)

ITEMS = [health_potion, sword, lightning_bolt_scroll]