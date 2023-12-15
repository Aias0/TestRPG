from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Dict, Tuple

from render_order import RenderOrder
from item_types import ItemTypes

from entity_effect import ItemEffect, CharacterEffect

from races import RACES_PLURAL

import re

if TYPE_CHECKING:
    from sprite import Sprite, Actor
    from races import BaseRace
    from jobs import BaseJob
    from entity import Character
    from engine import Engine

class Entity():
    parent: Sprite
    
    def __init__(self, name:str, value:int, description:str = None) -> None:
        self.name = name
        if description:
            self.description = description
            
        # Auto gen item description if one doesn't exist.
        elif isinstance(self, Item):
            attr_desc = {'CON': 'Constitution', 'STR': 'Strength', 'END': 'Endurance', 'DEX': 'Dexterity', 'FOC': 'Focus', 'INT': 'Intelligence', 'WIL': "Will", 'WGT': 'Weight', 'LCK': 'Luck'}
            inv_vs_eqp = {True: 'equipped', False: 'in inventory'}
            self.description = f'A {name}.'
            
            # Add info based on item effects
            if self.effect != ItemEffect():
                inc = [desc[1] for desc in attr_desc.items() if self.effect.attribute_bonuses[desc[0]] > 0]
                dec = [desc[1] for desc in attr_desc.items() if self.effect.attribute_bonuses[desc[0]] < 0]
                if len(inc) == 1:
                    self.description += f' This increases {inc[0]}'
                elif len(inc) > 1:
                    self.description += f' This increases {str(inc[:-1]).replace("[", "").replace("]", "")}, and {inc[-1]}'
                
                if dec and inc:
                    self.description += ' and '
                elif dec:
                
                    self.description += ' This '
                if len(dec) == 1:
                    self.description += f'decreases {dec[0]}'
                elif len(dec) >1:
                    self.description += f' This increases {str(dec[:-1]).replace("[", "").replace("]", "")}, and {dec[-1]}'
                
                if len(inc) >= 1 or len(dec) >= 1:
                    self.description += f'. Effects activates when {inv_vs_eqp[self.effect.needs_equipped]}.'
             
        # Auto gen character description if one doesn't exist.
        elif type(self) == Character:
            self.description = f'A level {self.level} {RACES_PLURAL[self.race.name]} {re.sub(r"^(.)", lambda match: match.group(1).lower(), self.job.name)} named {self.name}.'
        else:
            self.description = 'This should\'t happen.'
        self.value = value
        
    @property
    def engine(self) -> Engine:
        return self.parent.gamemap.engine
        
    def __str__(self) -> str:
        return f'{self.name}'
    def __repr__(self):
        return self.__str__()

        
class Item(Entity):
    parent: Optional[Sprite]
    holder: Optional[Character] = None
    
    def __init__(
        self,
        name: str,
        value: int,
        weight: int,
        char: str = None,
        color: Tuple[int, int, int] = None,
        itemtype: ItemTypes = ItemTypes.MISCELLANEOUS,
        description: str = None,
        effect: ItemEffect = ItemEffect(),
        equippable: dict = {},
        rarity: int = 10,
    ) -> None:
        
        self.weight = weight
        self.default_char = char
        self.default_color = color
        self.effect = effect
        self.itemtype = itemtype
        self.equippable = {'Head': False, 'Chest': False, 'Legs': False, 'Boots': False, 'Gloves': False, 'Rings': False, 'Right Hand': False, 'Left Hand': False} | equippable
        self.equipped = False
        self.rarity = rarity
        
        super().__init__(name=name, description=description, value=value)
        
    @property
    def char(self) -> str:
        if self.default_char:
            return self.default_char
        elif ItemTypes.is_armor(self):
            return '['
        elif ItemTypes.is_weapon(self):
            return '/'
        elif ItemTypes.is_consumable(self):
            return '!'
        else:
            return '?'
        
    @property
    def color(self) -> Tuple[int, int, int]:
        if self.default_color:
            return self.default_color
        elif ItemTypes.is_weapon(self):
            return 0, 191, 255
        elif ItemTypes.is_armor(self):
            return 139, 69, 19
        elif ItemTypes.is_consumable(self):
            return 127, 0, 255
        else:
            return 0, 0, 0
            
            
        
        

        
class Character(Entity):
    parent: Actor
    
    attribute_names = {'CON': 'Constitution', 'STR': 'Strength', 'END': 'Endurance', 'DEX': 'Dexterity', 'FOC': 'Focus', 'INT': 'Intelligence', 'WIL': "Will", 'WGT': 'Weight', 'LCK': 'Luck'}
    pronouns: Dict[str, List[str]] = {'male': ['he', 'him', 'his'], 'female': ['she', 'hers', 'her'], 'other': ['they', 'them', 'theirs']}
    
    def __init__(
        self,
        name: str,
        corpse_value: int,
        race: BaseRace,
        gender: str,
        job: BaseJob,
        description: str = None,
        level: int = 1,
        inventory: List[Item] = [],
        starting_equipment: List[Item] = [],
        base_CON: int = 10,
        base_STR: int = 10,
        base_END: int = 10,
        base_DEX: int = 10,
        base_FOC: int = 10,
        base_INT: int = 10,
        base_WIL: int = 10,
        base_WGT: int = 10,
        base_LCK: int = 10,
        level_up_factor: int = 150,
        xp_given: int = 100,
    ) -> None:
        self.effects: List[CharacterEffect] = []
        
        self.race = race
        self.race.parent = self
        
        self.gender = gender
        
        self.job = job
        self.job.parent = self
        
        self.inventory = inventory
        self.corpse_value = corpse_value
        
        self.level = level
        self.level_up_base = 0
        self.current_xp = 0
        self.level_up_factor = level_up_factor
        self.xp_given = xp_given
        self.needs_level_up = False
        
        # Attr Guide: 1: Ant | 10: Average Human | 100: Dragon
        # Visible Attributes
        self.base_CON = base_CON # constitution(CON) -> HP, phys resist
        self.base_STR = base_STR # strength(STR) -> phys atk, restrained resist
        self.base_END = base_END # endurance(END) -> SP, fatigue resist
        self.base_DEX = base_DEX # dexterity(DEX) -> hit/dodge chance
        self.base_FOC = base_FOC # focus(FOC) -> MP/strain, magic resist
        self.base_INT = base_INT # Intelligence(INT) -> magc atk, mental resist
        # Hidden Attributes
        self.base_WIL = base_WIL # will(WIL) -> spirit resist, limit break
        self.base_WGT = base_WGT # weight[conceptual](WGT) -> conceptual atk/resist
        self.base_LCK = base_LCK # luck(LCK) -> effects chance
        
        self.equipment: Dict[str, Optional[Item]] = {'Head': None, 'Chest': None, 'Legs': None, 'Boots': None, 'Gloves': None, 'Ring': None, 'Right Hand': None, 'Left Hand': None}
        self.equip(starting_equipment, silent=True)
        
        super().__init__(name=name, description=description, value=0)
        self.update_stats()
        
    
    # Attributes
    @property
    def CON(self) -> int:
        return self.base_CON + self.CON_intrinsic_bonus + self.CON_extrinsic_bonus
    @property
    def CON_intrinsic_bonus(self) -> int:
        total = self.race.attribute_bonuses['CON']
        for effect in self.effects:
            total += effect.attribute_bonuses['CON']
        return total
    @property
    def CON_extrinsic_bonus(self) -> int:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.attribute_bonuses['CON']
        return total
    
    @property
    def STR(self) -> int:
        return self.base_STR + self.STR_intrinsic_bonus + self.STR_extrinsic_bonus
    @property
    def STR_intrinsic_bonus(self) -> int:
        total = self.race.attribute_bonuses['STR']
        for effect in self.effects:
            total += effect.attribute_bonuses['STR']
        return total
    @property
    def STR_extrinsic_bonus(self) -> int:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.attribute_bonuses['STR']
        return total
    
    @property
    def END(self) -> int:
        return self.base_END + self.END_intrinsic_bonus + self.END_extrinsic_bonus
    @property
    def END_intrinsic_bonus(self) -> int:
        total = self.race.attribute_bonuses['END']
        for effect in self.effects:
            total += effect.attribute_bonuses['END']
        return total
    @property
    def END_extrinsic_bonus(self) -> int:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.attribute_bonuses['END']
        return total
    
    @property
    def DEX(self) -> int:
        return self.base_DEX + self.DEX_intrinsic_bonus + self.DEX_extrinsic_bonus
    @property
    def DEX_intrinsic_bonus(self) -> int:
        total = self.race.attribute_bonuses['DEX']
        for effect in self.effects:
            total += effect.attribute_bonuses['DEX']
        return total
    @property
    def DEX_extrinsic_bonus(self) -> int:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.attribute_bonuses['DEX']
        return total
    
    @property
    def FOC(self) -> int:
        return self.base_FOC + self.FOC_intrinsic_bonus + self.FOC_extrinsic_bonus
    @property
    def FOC_intrinsic_bonus(self) -> int:
        total = self.race.attribute_bonuses['FOC']
        for effect in self.effects:
            total += effect.attribute_bonuses['FOC']
        return total
    @property
    def FOC_extrinsic_bonus(self) -> int:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.attribute_bonuses['FOC']
        return total
    
    @property
    def INT(self) -> int:
        return self.base_INT + self.INT_intrinsic_bonus + self.INT_extrinsic_bonus
    @property
    def INT_intrinsic_bonus(self) -> int:
        total = self.race.attribute_bonuses['INT']
        for effect in self.effects:
            total += effect.attribute_bonuses['INT']
        return total
    @property
    def INT_extrinsic_bonus(self) -> int:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.attribute_bonuses['INT']
        return total
    
    @property
    def WIL(self) -> int:
        return self.base_WIL + self.WIL_intrinsic_bonus + self.WIL_extrinsic_bonus
    @property
    def WIL_intrinsic_bonus(self) -> int:
        total = self.race.attribute_bonuses['WIL']
        for effect in self.effects:
            total += effect.attribute_bonuses['WIL']
        return total
    @property
    def WIL_extrinsic_bonus(self) -> int:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.attribute_bonuses['WIL']
        return total
    
    @property
    def WGT(self) -> int:
        return self.base_WGT + self.WGT_intrinsic_bonus + self.WGT_extrinsic_bonus
    @property
    def WGT_intrinsic_bonus(self) -> int:
        total = self.race.attribute_bonuses['WGT']
        for effect in self.effects:
            total += effect.attribute_bonuses['WGT']
        return total
    @property
    def WGT_extrinsic_bonus(self) -> int:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.attribute_bonuses['WGT']
        return total
    
    @property
    def LCK(self) -> int:
        return self.base_LCK + self.LCK_intrinsic_bonus + self.LCK_extrinsic_bonus
    @property
    def LCK_intrinsic_bonus(self) -> int:
        total = self.race.attribute_bonuses['LCK']
        for effect in self.effects:
            total += effect.attribute_bonuses['LCK']
        return total
    @property
    def LCK_extrinsic_bonus(self) -> int:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.attribute_bonuses['LCK']
        return total
    
    # Resources
    @property
    def hp(self) -> int:
        return self._hp
    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.parent.ai:
            self.die()
            
    @property
    def mp(self) -> int:
        return self._mp
    @mp.setter
    def mp(self, value: int) -> None:
        self._mp = max(0, min(value, self.max_mp))
        
    @property
    def sp(self) -> int:
        return self._sp
    @sp.setter
    def sp(self, value: int) -> None:
        self._sp = max(0, min(value, self.max_sp))
    
    # Defense/Resistance
    @property
    def phys_defense(self) -> int:
        return self.base_phys_defense + self.phys_defense_intrinsic_bonus + self.phys_defense_extrinsic_bonus
    @property
    def phys_defense_intrinsic_bonus(self) -> int:
        total = 0
        for effect in self.effects:
            total += effect.phys_defense_bonus
        return total
    @property
    def phys_defense_extrinsic_bonus(self) -> int:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.phys_defense_bonus
        return total
        
    @property
    def phys_negation(self) -> float:
        return self.base_phys_negation + self.phys_negation_intrinsic_bonus + self.phys_negation_extrinsic_bonus
    @property
    def phys_negation_intrinsic_bonus(self) -> int:
        total = 0
        for effect in self.effects:
            total += effect.phys_negation_bonus
        return total
    @property
    def phys_negation_extrinsic_bonus(self) -> float:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.phys_negation_bonus
        return total
    
    @property
    def phys_atk(self) -> int:
        return self.base_phys_atk + self.phys_atk_intrinsic_bonus + self.phys_atk_extrinsic_bonus
    @property
    def phys_atk_intrinsic_bonus(self) -> int:
        total = 0
        for effect in self.effects:
            total += effect.phys_atk_bonus
        return total
    @property
    def phys_atk_extrinsic_bonus(self) -> int:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.phys_atk_bonus
        return total
    
    
    @property
    def magc_defense(self) -> int:
        return self.base_magc_defense + self.magc_defense_intrinsic_bonus + self.magc_negation_extrinsic_bonus
    @property
    def magc_defense_intrinsic_bonus(self) -> int:
        total = 0
        for effect in self.effects:
            total += effect.magc_defense_bonus
        return total
    @property
    def magc_defense_extrinsic_bonus(self) -> int:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.magc_defense_bonus
        return total
    
    @property
    def magc_negation(self) -> float:
        return self.base_magc_negation + self.magc_negation_intrinsic_bonus + self.magc_negation_extrinsic_bonus
    @property
    def magc_negation_intrinsic_bonus(self) -> int:
        total = 0
        for effect in self.effects:
            total += effect.magc_negation_bonus
        return total
    @property
    def magc_negation_extrinsic_bonus(self) -> float:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.magc_negation_bonus
        return total
    
    @property
    def magc_atk(self) -> int:
        return self.base_magc_atk + self.magc_atk_intrinsic_bonus + self.magc_atk_extrinsic_bonus
    @property
    def magc_atk_intrinsic_bonus(self) -> int:
        total = 0
        for effect in self.effects:
            total += effect.magc_atk_bonus
        return total
    @property
    def magc_atk_extrinsic_bonus(self) -> int:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.magc_atk_bonus
        return total
    
    
    @property
    def dodge_chance(self) -> float:
        return self.base_dodge_chance + self.dodge_chance_intrinsic_bonus + self.dodge_chance_extrinsic_bonus
    @property
    def dodge_chance_intrinsic_bonus(self) -> int:
        total = 0
        for effect in self.effects:
            total += effect.dodge_chance_bonus
        return total
    @property
    def dodge_chance_extrinsic_bonus(self) -> float:
        total = 0
        for item in self.inventory:
            if item.effect.needs_equipped and not item.equipped:
                continue
            total += item.effect.dodge_chance_bonus
        return total
    
    def update_stats(self) -> None:
        # Resource Stats
        try:
            hp_percent = self._hp/self.max_hp
        except:
            # This happens on character creation
            hp_percent = 1
        self.max_hp = (self.CON*self.level)//1.5
        self._hp = int(self.max_hp * hp_percent)
        
        try:
            mp_percent = self._mp/self.max_mp
        except:
            # This happens on character creation
            mp_percent = 1
        self.max_mp = (self.FOC*self.level)//1.5
        self._mp = int(self.max_mp * mp_percent)
        
        try:
            sp_percent = self._sp/self.max_sp
        except:
            # This happens on character creation
            sp_percent = 1
        self.max_sp = (self.END*self.level)//2
        self._sp = int(self.max_sp * sp_percent)
        
        # Attack Stats
        self.base_phys_atk = self.STR
        self.base_magc_atk = self.INT
        
        #Resistance Stats
        self.base_phys_defense = int(self.CON/3)
        self.base_phys_negation = 0
        self.base_magc_defense = int(self.FOC/3)
        self.base_magc_negation = 0
        
        self.base_dodge_chance = self.DEX * .01
    
    # XP/Level
    @property
    def xp_for_next_level(self) -> int:
        return self.level_up_base + self.level * self.level_up_factor
    @property
    def xp_to_next_level(self) -> int:
        return self.xp_for_next_level - self.current_xp
    
    def add_xp(self, xp:int):
        if xp < 0:
            return
        if self.current_xp + xp >= self.xp_for_next_level:
            leftover = self.current_xp + xp - self.xp_for_next_level
            self.current_xp = 0
            self.level += 1
            print('Level Up')
            self.update_stats()
            self.needs_level_up = True
            self.add_xp(leftover)
        else:
            self.current_xp += xp
    
    # Inventory and Weight
    @property
    def carry_weight(self) -> int:
        return self.STR*15

    @property
    def weight(self) -> int:
        total = 0
        for item in self.inventory:
            total += item.weight
        return total
        
    def add_inventory(self, item: Item, silent: bool = False) -> None:
        if self.weight + item.weight > self.carry_weight:
            if not silent: print(f'{item} is to heavy to add to inventory.')
            return
        self.inventory.append(item)
        item.holder = self
        if not silent: print(f'{item} added to inventory.')
        
    def drop_inventory(self, item: str | Item, silent: bool = False) -> None:
        """ `silent` to not print messages. """
        if isinstance(item, str):
            item = self.get_with_name(item)
        if item not in self.inventory:
            if not silent: print(f'{item} not in inventory.')
            return
        if self.is_equipped(item):
            self.unequip(item)
        self.inventory.remove(item)
        item.holder = None
        if not silent: print(f'{item} dropped.')
        #TODO place item on ground under character
        
    def get_with_name(self, name: str) -> Item:
        """ Returns Item in inventory with name `name`. """
        return [item for item in self.inventory if item.name == name][0]
    
    def in_inventory(self, item: str | Item) -> bool:
        if isinstance(item, str):
            return bool(self.get_with_name(item))
        return item in self.inventory
    
    def is_equipped(self, item: str | Item) -> bool:
        if isinstance(item, str):
            return bool(self.get_with_name(item))
        return item in self.equipment.values()
        
    def equip(self, items: Item | str | List[Item|str], slot: Optional[str] = None, silent: bool = False) -> None:
        """ Equips a single `Item` or multiple. Adds item to inventory if it isn't already present.\n\n`slot` only used on single equip.\n\n`silent` to not print messages."""
        if not isinstance(items, list):
            items:List[Item|str] = [items]
        else:
            slot = None
        items: List[Item] = [self.get_with_name(item) if isinstance(item, str) else item for item in items]
        
        for item in items:
            if not item in self.inventory:
                # Add item to inventory if it isn't already
                self.add_inventory(item, silent)
            
            if not any(item.equippable.values()):
                if not silent: print(f'Cannot equip {item.name}')
                break
            
            if slot:
                if self.equipment[slot]:
                    if not silent: print(f'{slot} already equipped.')
                    break
                if not silent: print(f'Equipped {item} on {slot}.')
                self.equipment[slot] = item
                item.equipped = True
                break
            
            for slot_val in item.equippable.items():
                if not slot_val[1]:
                    continue
                if self.equipment[slot_val[0]]:
                    if not silent: print(f'{slot_val[0]} already equipped.')
                    continue
                
                if not silent: print(f'Equipped {item} on {slot_val[0]}.')
                self.equipment[slot_val[0]] = item
                item.equipped = True
                break
    
    def unequip(self, items: Item | str | List[Item | str], silent: bool = False) -> None:
        """ `silent` to not print messages. """
        if not isinstance(items, list):
            items: List[Item|str] = [items]
        items: List[Item] = [self.get_with_name(item) if isinstance(item, str) else item for item in items]
            
        for item in items:
            if not item in self.equipment.values():
                if not silent: print(f'{item} not equipped.')
                
            self.equipment[list(self.equipment.keys())[list(self.equipment.values()).index(item)]] = None
            item.equipped = False
            if not silent: print(f'Unequipped {item}.')
            
    def toggle_equip(self, items: Item | str | List[Item | str], silent: bool = False):
        """ `silent` to not print messages. """
        if not isinstance(items, list):
            items: List[Item|str] = [items]
        items: List[Item] = [self.get_with_name(item) if isinstance(item, str) else item for item in items]
        
        for item in items:
            if item.equipped:
                self.unequip(item, silent)
            else:
                self.equip(item, silent)
    
        
    def die(self) -> None:
        self.value = self.corpse_value
        
        self.parent.char = "%"
        self.parent.color = (191, 0, 0)
        self.parent.blocks_movement = False
        self.parent.ai = None
        self.name = f"remains of {self.name}"
        self.parent.render_order = RenderOrder.CORPSE
        
    def heal(self, amount: int) -> int:
        if self.hp == self.max_hp:
            return 0

        new_hp_value = self.hp + int(amount*self.race.heal_effectiveness)

        if new_hp_value > self.max_hp:
            new_hp_value = self.max_hp

        amount_recovered = new_hp_value - self.hp

        self.hp = new_hp_value

        return amount_recovered

    def take_damage(self, amount: int) -> None:
        self.hp -= amount