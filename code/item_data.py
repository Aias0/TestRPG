from __future__ import annotations
from typing import TYPE_CHECKING

from entity import Item
from entity_effect import ItemEffect, HealingEffect, ScrollEffect

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

staff = Item(
    'Staff', 10, 4, '⌠', itemtype=ItemTypes.STAFF, itemsubtypes=MagicFocusTypes.BALANCE, effect=ItemEffect(magc_atk_bonus=2), color=(130, 61, 8)
)

chest_plate = Item(
    'Chest plate', 10, 12, itemtype=ItemTypes.CHEST_ARMOR, effect=ItemEffect(phys_defense_bonus=5, phys_negation_bonus=2)
)

lightning_bolt_scroll = Item(
    'Lightning Bolt Scroll', 200, 1, itemtype=ItemTypes.SCROLL, effect=ScrollEffect(magic.LightningBolt()), rarity=5
)

fire_ball_scroll = Item(
    'Fire Ball Scroll', 400, 1, itemtype=ItemTypes.SCROLL, effect=ScrollEffect(magic.FireBall()), rarity=2
)

ITEMS = [health_potion, sword, fire_ball_scroll, lightning_bolt_scroll, mana_potion, staff]