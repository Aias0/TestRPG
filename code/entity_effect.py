from __future__ import annotations
from typing import TYPE_CHECKING, Optional

import actions, color

from exceptions import Impossible

from input_handler import RangedAttackHandler
from magic import AOESpell

if TYPE_CHECKING:
    from entity import Entity, Item, Character
    from magic import Spell

_bonus_dict = {'CON': 0, 'STR': 0, 'END': 0, 'DEX': 0, 'FOC': 0, 'INT': 0, 'WIL': 0, 'WGT': 0, 'LCK': 0}
class BaseEffect():
    parent: Entity
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
        raise Impossible(f'{self.parent} effect has no effect.')
    
    def get_action(self) -> None:
        """Try to return the action for this item."""
        from entity import Item, Character
        if isinstance(self.parent, Item):
            return actions.EffectAction(self.parent.holder.parent, self)
        elif isinstance(self.parent, Character):
            return actions.EffectAction(self.parent.parent, self)
    
    def activate(self, action: actions.EffectAction) -> None:
        """Invoke this items ability."""
        raise Impossible(f'{self.parent} effect has no action.')

        
    def similar(self, other):
        if isinstance(other, self.__class__):
            for i, pair in enumerate(zip([_[1] for _ in vars(self).items() if _[0] != 'parent'], [_[1] for _ in vars(other).items() if _[0] != 'parent'])):
                if hasattr(pair[0], 'similar') and not pair[0].similar(pair[1]):
                    return False
                elif not hasattr(pair[0], 'similar') and pair[0] != pair[1]:
                    return False
            return True
        return False
        


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
        self.parent.holder.inventory.remove(self.parent)
    
class CharacterEffect(BaseEffect):
    parent: Character
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
        
    def remove(self) -> None:
        """ Remove effect from character. """
        self.parent.effects.remove(self)

class HealingEffect(ItemEffect):
    def __init__(self, amount: int, consumable: bool = True):
        super().__init__(
            phys_atk_bonus=0,
            magc_atk_bonus=0,
            phys_defense_bonus=0,
            phys_negation_bonus=0,
            magc_defense_bonus=0,
            magc_negation_bonus=0,
            dodge_chance_bonus=0,
            attribute_bonuses={},
            needs_equipped=False,
            consumable=consumable
            )
        
        self.amount = amount
    
    def activate(self, action: actions.EffectAction) -> None:
        amount_recovered = self.parent.holder.heal(self.amount)
        you_or_enemy = {True: 'You', False: self.parent.name}
        s = {False: ['s', 'ed'], True: ['',]*2}
        is_player = self.parent.holder == self.parent.holder.parent.parent.engine.player.entity
        if amount_recovered > 0:
            self.parent.holder.parent.parent.engine.message_log.add_message(
                f'{you_or_enemy[is_player]} consume{s[is_player][0]} the {self.parent.name}, and recover{s[is_player][1]} {amount_recovered} HP!',
                color.health_recovered,
            )
        elif is_player:
            raise Impossible('Your health is already full.')
        
        self.consume()
        
class ScrollEffect(ItemEffect):
    def __init__(self, spell: Spell, consumable: bool = True):
        super().__init__(
            phys_atk_bonus=0,
            magc_atk_bonus=0,
            phys_defense_bonus=0,
            phys_negation_bonus=0,
            magc_defense_bonus=0,
            magc_negation_bonus=0,
            dodge_chance_bonus=0,
            attribute_bonuses={},
            needs_equipped=False,
            consumable=consumable
            )
        
        self.spell = spell
        
    def get_action(self) -> actions.Action | None:
        self.parent.engine.message_log.add_message(
            "Select a target location.", color.needs_target
        )
        self.parent.engine.event_handler = RangedAttackHandler(
            self.parent.engine,
            self.spell,
            callback=lambda xy: actions.EffectAction(self.parent.holder.parent, self, xy),
        )
        return None
        
    def activate(self, action: actions.EffectAction) -> None:
        target_xy = action.target_xy
        self.spell.cast(caster=self.parent.holder, target=target_xy, scroll_cast=True)
        self.consume()
        
    
