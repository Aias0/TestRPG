from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from entity import Entity, Item, Character

_bonus_dict = {'CON': 0, 'STR': 0, 'END': 0, 'DEX': 0, 'FOC': 0, 'INT': 0, 'WIL': 0, 'WGT': 0, 'LCK': 0}
class BaseEffect():
    def __init__(
        self,
        phys_atk_bonus: int = 0,
        magc_atk_bonus: int = 0,
        phys_defense_bonus: int = 0,
        phys_negation_bonus: int = 0,
        magc_defense_bonus: int = 0,
        magc_negation_bonus: int = 0,
        dodge_chance_bonus: int = 0,
        attribute_bonuses: dict[str, int] = {},
    ) -> None:
        
        self.phys_atk_bonus = phys_atk_bonus
        self.magc_atk_bonus = magc_atk_bonus
        self.phys_defense_bonus = phys_defense_bonus
        self.phys_negation_bonus = phys_negation_bonus
        self.magc_defense_bonus = magc_defense_bonus
        self.magc_negation_bonus = magc_negation_bonus
        self.dodge_chance_bonus = dodge_chance_bonus
        
        self.attribute_bonuses = _bonus_dict | attribute_bonuses
        
    def get_effect(self) -> None:
        """Try to return the effect for this item."""
        raise NotImplementedError()
    
    def get_action(self) -> None:
        """Try to return the action for this item."""
        raise NotImplementedError()
    
    def activate(self) -> None:
        """Invoke this items ability."""
        raise NotImplementedError()
    
    def __eq__(self, other) :
        return self.__dict__ == other.__dict__
    def __ne__(self, other) :
        return self.__dict__ != other.__dict__
        


class ItemEffect(BaseEffect):
    parent: Item
    def __init__(
        self,
        phys_atk_bonus: int = 0,
        magc_atk_bonus: int = 0,
        phys_defense_bonus: int = 0,
        phys_negation_bonus: int = 0,
        magc_defense_bonus: int = 0,
        magc_negation_bonus: int = 0,
        dodge_chance_bonus: int = 0,
        attribute_bonuses: dict[str, int] = {},
        needs_equipped: bool = True,
        consumable: bool = False,
        
    ):

        super().__init__(
            phys_atk_bonus = phys_atk_bonus,
            magc_atk_bonus = magc_atk_bonus,
            phys_defense_bonus = phys_defense_bonus,
            phys_negation_bonus = phys_negation_bonus,
            magc_defense_bonus = magc_defense_bonus,
            magc_negation_bonus = magc_negation_bonus,
            dodge_chance_bonus = dodge_chance_bonus,
            attribute_bonuses = attribute_bonuses,
        )
        self.needs_equipped = needs_equipped # True means that bonus will only be applied if item is equipped
        
        self.consumable = consumable

    def consume(self) -> None:
        """Remove the consumed item from its containing inventory."""
        self.parent.holder.inventory.remove(self)
    
class CharacterEffect(BaseEffect):
    def __init__(
        self,
        phys_atk_bonus: int = 0,
        magc_atk_bonus: int = 0,
        phys_defense_bonus: int = 0,
        phys_negation_bonus: int = 0,
        magc_defense_bonus: int = 0,
        magc_negation_bonus: int = 0,
        dodge_chance_bonus: int = 0,
        attribute_bonuses: dict[str, int] = {},
        time: int = 60,
    ) -> None:
        self.time = time
        
        
        super().__init__(
            phys_atk_bonus = phys_atk_bonus,
            magc_atk_bonus = magc_atk_bonus,
            phys_defense_bonus = phys_defense_bonus,
            phys_negation_bonus = phys_negation_bonus,
            magc_defense_bonus = magc_defense_bonus,
            magc_negation_bonus = magc_negation_bonus,
            dodge_chance_bonus = dodge_chance_bonus,
            attribute_bonuses = attribute_bonuses,
        )

    


    