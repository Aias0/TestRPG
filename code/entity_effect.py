from __future__ import annotations
from typing import TYPE_CHECKING, Optional

import actions, color, random, game_types, sys
from game_types import ElementTypes

from exceptions import Impossible

from input_handler import RangedAttackHandler, FAVORITES
from magic import AOESpell

if TYPE_CHECKING:
    from entity import Entity, Item, Character, Corpse
    from magic import AttackSpell

_bonus_dict = {'CON': 0, 'STR': 0, 'END': 0, 'DEX': 0, 'FOC': 0, 'INT': 0, 'WIL': 0, 'WGT': 0, 'LCK': 0}
class BaseEffect():
    parent: Entity
    def __init__(
        self,
        name: str = None,
        phys_atk_bonus: int = 0,
        magc_atk_bonus: int = 0,
        phys_defense_bonus: int = 0,
        phys_negation_bonus: int = 0,
        magc_defense_bonus: int = 0,
        magc_negation_bonus: int = 0,
        dodge_chance_bonus: int = 0,
        attribute_bonuses: dict[str, int] = {},
        stackable: bool = True,
        resistances: dict[game_types.ElementTypes, int] = {},
    ) -> None:
        
        self.name = name
        
        self.phys_atk_bonus = phys_atk_bonus
        self.magc_atk_bonus = magc_atk_bonus
        self.phys_defense_bonus = phys_defense_bonus
        self.phys_negation_bonus = phys_negation_bonus
        self.magc_defense_bonus = magc_defense_bonus
        self.magc_negation_bonus = magc_negation_bonus
        self.dodge_chance_bonus = dodge_chance_bonus
        
        self.attribute_bonuses = _bonus_dict | attribute_bonuses
        
        self.resistances = {elem: 0 for elem in game_types.ElementTypes.elements()} | resistances
        
        self.stackable = stackable
        
    def get_effect(self) -> None:
        """Try to return the effect for this item."""
        raise Impossible(f'{self.parent} effect has no effect.')
    
    def get_action(self) -> actions.Action | None:
        """Try to return the action for this item."""
        if self.parent.__class__.__name__ == 'Item':
            return actions.EffectAction(self.parent.holder.parent, self)
        elif self.parent.__class__.__name__ == 'Character':
            return actions.EffectAction(self.parent.parent, self)
    
    def activate(self, action: actions.EffectAction | None) -> None:
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
        name: str = None,
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
        stackable: bool = True,
        resistances: dict[game_types.ElementTypes, int] = {},
    ):

        super().__init__(
            name=name,
            phys_atk_bonus=phys_atk_bonus,
            magc_atk_bonus=magc_atk_bonus,
            phys_defense_bonus=phys_defense_bonus,
            phys_negation_bonus=phys_negation_bonus,
            magc_defense_bonus=magc_defense_bonus,
            magc_negation_bonus=magc_negation_bonus,
            dodge_chance_bonus=dodge_chance_bonus,
            attribute_bonuses=attribute_bonuses,
            stackable=stackable,
            resistances=resistances,
        )
        self.needs_equipped = needs_equipped # True means that bonus will only be applied if item is equipped
        
        self.consumable = consumable

    def consume(self) -> None:
        """Remove the consumed item from its containing inventory."""
        global FAVORITES
        favorite_key = None
        for key, item in FAVORITES.items():
            if isinstance(item, list) and self.parent in item:
                favorite_key = key
                break

        if favorite_key:
            FAVORITES[key].remove(self.parent)
            if not FAVORITES[key]:
                FAVORITES[key] = None
        
        if self.parent.holder.in_inventory(self.parent):
            self.parent.holder.inventory.remove(self.parent)
        else:
            self.parent.gamemap.sprites.remove(self.parent.parent)
        
    def eat(self, action: actions.EffectAction) -> None:
        raise Impossible(f'{self.parent} is not edible.')
    
class CharacterEffect(BaseEffect):
    parent: Character
    def __init__(
        self,
        name: str = None,
        phys_atk_bonus: int = 0,
        magc_atk_bonus: int = 0,
        phys_defense_bonus: int = 0,
        phys_negation_bonus: int = 0,
        magc_defense_bonus: int = 0,
        magc_negation_bonus: int = 0,
        dodge_chance_bonus: int = 0,
        attribute_bonuses: dict[str, int] = {},
        stackable: bool = True,
        duration: int = 60,
        automatic: bool = True,
        resistances: dict[game_types.ElementTypes, int] = {},
    ) -> None:
        """ `duration` of -1 is indicates a infinite time."""
        self.duration = duration
        self.automatic = automatic
        self.current_turn = 0
        
        super().__init__(
            name=name,
            phys_atk_bonus=phys_atk_bonus,
            magc_atk_bonus=magc_atk_bonus,
            phys_defense_bonus=phys_defense_bonus,
            phys_negation_bonus=phys_negation_bonus,
            magc_defense_bonus=magc_defense_bonus,
            magc_negation_bonus=magc_negation_bonus,
            dodge_chance_bonus=dodge_chance_bonus,
            attribute_bonuses=attribute_bonuses,
            stackable=stackable,
            resistances=resistances,
        )
        
    def remove(self) -> None:
        """ Remove effect from character. """
        self.parent.remove_effect(self)
#getattr(self, func_name, None)

class HealingEffect(ItemEffect):
    def __init__(self, amount: int | list, type: str = 'hp', consumable: bool = True, name: str = None, stackable: bool = True):
        super().__init__(
            name=name,
            phys_atk_bonus=0,
            magc_atk_bonus=0,
            phys_defense_bonus=0,
            phys_negation_bonus=0,
            magc_defense_bonus=0,
            magc_negation_bonus=0,
            dodge_chance_bonus=0,
            attribute_bonuses={},
            stackable=stackable,
            needs_equipped=False,
            consumable=consumable
            )
        
        self.amount = amount
        self.type = type
    
    def activate(self, action: actions.EffectAction | None) -> None:
        if isinstance(self.amount, list):
            if self.parent.holder.LCK > 15:
                self.amount = max(random.randrange(*self.amount), random.randrange(*self.amount))
            elif self.parent.holder.LCK < 5:
                self.amount = min(random.randrange(*self.amount), random.randrange(*self.amount))
            else:
                self.amount = random.randrange(*self.amount)
        
        amount_recovered = self.parent.holder.heal(self.amount, self.type)
        
        you_or_enemy = {True: 'You', False: self.parent.name}
        s = {False: ['s', 'ed'], True: ['',]*2}
        type_fullname = {'hp': 'health', 'mp': 'mana', 'sp': 'stamina'}
        
        is_player = self.parent.holder == self.parent.holder.parent.parent.engine.player.entity
        if amount_recovered > 0:
            self.parent.holder.parent.parent.engine.message_log.add_message(
                f'{you_or_enemy[is_player]} consume{s[is_player][0]} the {self.parent.name}, and recover{s[is_player][1]} {amount_recovered} {self.type.upper()}!',
                color.health_recovered,
            )
        elif is_player:
            raise Impossible(f'Your {type_fullname[self.type]} is already full.')
        
        if self.consumable:
            self.consume()
        
class ScrollEffect(ItemEffect):
    def __init__(self, spell: AttackSpell, consumable: bool = True, name: str = None, stackable: bool = True):
        super().__init__(
            name=name,
            phys_atk_bonus=0,
            magc_atk_bonus=0,
            phys_defense_bonus=0,
            phys_negation_bonus=0,
            magc_defense_bonus=0,
            magc_negation_bonus=0,
            dodge_chance_bonus=0,
            attribute_bonuses={},
            stackable=stackable,
            needs_equipped=False,
            consumable=consumable,
            )
        
        self.spell = spell
        
    def get_action(self) -> actions.Action | None:
        self.parent.engine.message_log.add_message(
            "Select a target location.", color.prompt_player
        )
        self.parent.engine.event_handler = RangedAttackHandler(
            self.parent.engine,
            callback=lambda xy: actions.EffectAction(self.parent.holder.parent, self, xy),
            effect=self,
        )
        return None
        
    def activate(self, action: actions.EffectAction) -> None:
        target_xy = action.target_xy
        self.spell.cast(caster=self.parent.holder, target=target_xy, scroll_cast=True)
        
        if self.consumable:
            self.consume()
        
class CorpseEffect(ItemEffect):
    """ This effect's purpose is to contain then apply effects onto a character when the corpse is eatten. """
    parent: Corpse
    def __init__(self, effects: list[CharacterEffect | DOTEffect | HealingEffect], name: str = None, stackable: bool = True):
        super().__init__(
            name=name,
            phys_atk_bonus=0,
            magc_atk_bonus=0,
            phys_defense_bonus=0,
            phys_negation_bonus=0,
            magc_defense_bonus=0,
            magc_negation_bonus=0,
            dodge_chance_bonus=0,
            attribute_bonuses={},
            stackable=stackable,
            needs_equipped=False,
            consumable=True
        )
        
        self.effects = effects
    
    def eat(self, action: actions.EffectAction | None):
        for effect in self.effects:
            if isinstance(effect, CharacterEffect):
                self.parent.holder.add_effect(effect)
            if isinstance(effect, HealingEffect):
                effect.activate(effect.get_action())
        self.consume()
            
class DOTEffect(CharacterEffect):
    def __init__(
        self,
        damage: int,
        damage_type: game_types.DamageTypes,
        element_type: game_types.ElementTypes,
        name: str = None,
        phys_atk_bonus: int = 0,
        magc_atk_bonus: int = 0,
        phys_defense_bonus: int = 0,
        phys_negation_bonus: int = 0,
        magc_defense_bonus: int = 0,
        magc_negation_bonus: int = 0,
        dodge_chance_bonus: int = 0,
        attribute_bonuses: dict[str, int] = {},
        stackable: bool = True,
        duration: int = 60,
        resistances: dict[game_types.ElementTypes, int] = {},
    ) -> None:
        
        super().__init__(
            name=name,
            phys_atk_bonus=phys_atk_bonus,
            magc_atk_bonus=magc_atk_bonus,
            phys_defense_bonus=phys_defense_bonus,
            phys_negation_bonus=phys_negation_bonus,
            magc_defense_bonus=magc_defense_bonus,
            magc_negation_bonus=magc_negation_bonus,
            dodge_chance_bonus=dodge_chance_bonus,
            attribute_bonuses=attribute_bonuses,
            stackable=stackable,
            duration=duration,
            resistances=resistances,
        )
        self.damage = damage
        self.damage_type = damage_type
        self.element_type = element_type
        
    def activate(self, action: actions.EffectAction | None) -> None:
        if self.current_turn >= self.duration:
            self.remove()
        else:
            damage_taken = self.parent.take_damage(self.damage, self.damage_type, self.element_type, dodgeable=False)
            self.parent.engine.message_log.add_message(
                f'{self.parent.name} took {damage_taken} points of {game_types.GameTypeNames.damagetype_to_name[self.damage_type]} {game_types.GameTypeNames.elementtype_to_name[self.element_type]} damage.',
                color.enemy_atk
            )
            
            self.current_turn += 1
            
class KeyEffect(ItemEffect):
    def __init__(
        self,
        key: int,
        one_time: bool = False,
        name: str = None,
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
        stackable: bool = True,
        resistances: dict[game_types.ElementTypes, int] = {},
    ):
        super().__init__(
            name,
            phys_atk_bonus,
            magc_atk_bonus,
            phys_defense_bonus,
            phys_negation_bonus,
            magc_defense_bonus,
            magc_negation_bonus,
            dodge_chance_bonus,
            attribute_bonuses,
            needs_equipped,
            consumable,
            stackable,
            resistances
        )
        
        self.key = key
        self.one_time = one_time