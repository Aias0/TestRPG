from __future__ import annotations
from typing import TYPE_CHECKING

from entity import Item
from entity_effect import ItemEffect, HealingEffect, ScrollEffect, KeyEffect

import magic

from game_types import ItemTypes, ItemSubTypes, MagicFocusTypes

health_potion = Item(
    'Health Potion', 100, 1, itemtype=ItemTypes.POTION, effect=HealingEffect(amount=4, type='hp'), rarity= 25
)
mana_potion = Item(
    'Mana Potion', 100, 1, itemtype=ItemTypes.POTION, effect=HealingEffect(amount=4, type='mp'), rarity= 15
)

sword = Item(
    'Sword', 5, 6, itemtype=ItemTypes.SWORD, itemsubtypes=ItemSubTypes.SHORT_SWORD, effect=ItemEffect(phys_atk_bonus=2)
)

dagger = Item(
    'Dagger', 5, 6, itemtype=ItemTypes.DAGGER, effect=ItemEffect(phys_atk_bonus=1)
)

staff = Item(
    'Staff', 10, 4, '⌠', itemtype=ItemTypes.STAFF, itemsubtypes=MagicFocusTypes.BALANCE, effect=ItemEffect(magc_atk_bonus=2), color=(130, 61, 8)
)

chest_plate = Item(
    'Chest Plate', 10, 12, itemtype=ItemTypes.CHEST_ARMOR, itemsubtypes=ItemSubTypes.MEDIUM_ARMOR, effect=ItemEffect(phys_defense_bonus=5, phys_negation_bonus=2)
)

leather_jerkin = Item(
    'Leather Jerkin', 8, 4, itemtype=ItemTypes.CHEST_ARMOR, itemsubtypes=ItemSubTypes.LIGHT_ARMOR, effect=ItemEffect(phys_defense_bonus=3, phys_negation_bonus=1)
)

robes = Item(
    'Robes', 8, 2, itemtype=ItemTypes.CHEST_ARMOR, itemsubtypes=ItemSubTypes.CLOTHING, effect=ItemEffect(phys_defense_bonus=2, phys_negation_bonus=0, magc_defense_bonus=4, magc_negation_bonus=2)
)

lightning_bolt_scroll = Item(
    'Lightning Bolt Scroll', 200, 1, itemtype=ItemTypes.SCROLL, effect=ScrollEffect(magic.LightningBolt()), rarity=5
)

fire_ball_scroll = Item(
    'Fire Ball Scroll', 400, 1, itemtype=ItemTypes.SCROLL, effect=ScrollEffect(magic.FireBall()), rarity=2
)

simple_key = Item(
    'Simple Key', 1, 1, '⌐', color=(200,)*3, itemtype=ItemTypes.KEY, effect=KeyEffect(1)
)

ITEMS = [health_potion, sword, fire_ball_scroll, lightning_bolt_scroll, mana_potion, staff, dagger, leather_jerkin, robes, chest_plate]

ITEMS_NAME_DICT = {value.name: value for value in ITEMS}