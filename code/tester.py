from sprite import Actor
from entity import Character, Item
from races import Human
from jobs import Mage

from entity_effect import ItemEffect
from game_types import ItemTypes


test = Actor(
    character=Character(
        name='Test',
        corpse_value=100,
        race=Human(),
        job=Mage(),
        level=1,
        starting_equipment=[
            Item('Sword', 100, 10, itemtype=ItemTypes.SWORD, effect=ItemEffect(attribute_bonuses={'DEX': 1}), equippable={'Right Hand': True}),
            Item('Keepsake', 1, 1, effect=ItemEffect(attribute_bonuses={'CON': 2}, needs_equipped=False))
            ]
    ),
)
guy = test.entity

""" print(guy.equipment)
print(guy.inventory[0].description)
print(f'{guy.weight}/{guy.carry_weight}')

print('DEX', guy.DEX)
print('CON', guy.CON)

guy.unequip(guy.inventory[0])

print(guy.equipment)

print('DEX', guy.DEX)
print('CON', guy.CON)

print(guy.inventory)
print(f'{guy.weight}/{guy.carry_weight}')

guy.add_inventory(Item('Heavy Weight', 0, 130))
print(guy.inventory)
print(guy.inventory[2].description)

print(f'{guy.weight}/{guy.carry_weight}')

guy.drop_inventory('Heavy Weight')
print(guy.inventory)

print(f'{guy.weight}/{guy.carry_weight}')
 """
print(f'Level: {guy.level}')

print(f'XP: {guy.current_xp}/{guy.xp_for_next_level}')

print(guy.hp)

guy.add_xp(500)

print(f'Level: {guy.level}')
print(f'XP: {guy.current_xp}/{guy.xp_for_next_level}')

print(guy.hp)