
from entity_effect import DOTEffect, CharacterEffect
import game_types

EFFECTS = {
    "Dwarf": [
        DOTEffect(
            damage= 1,
            damage_type= game_types.DamageTypes.PHYS,
            element_type =  game_types.ElementTypes.POISON,
            duration = 5
        ),
        CharacterEffect(
            attribute_bonuses = {"CON": 1},
            stackable=False,
        )
    ],
    "Elf": [
        DOTEffect(
            damage= 1,
            damage_type= game_types.DamageTypes.PHYS,
            element_type =  game_types.ElementTypes.POISON,
            duration = 5
        ),
        CharacterEffect(
            attribute_bonuses = {"DEX": 1},
            stackable=False,
        )
    ],
}