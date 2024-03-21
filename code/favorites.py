from __future__ import annotations
from typing import TYPE_CHECKING
import tcod, copy

if TYPE_CHECKING:
    from entity import Item, Character
    from entity_effect import CharacterEffect
    from magic import Spell
    from actions import Action

class PlayerFavorites:
    def __init__(self, parent) -> None:
        self.parent: Character = parent
        
        self.items: dict[tcod.event.KeySym, list[Item] | CharacterEffect | Spell | None] = {
            tcod.event.KeySym.N1: None,
            tcod.event.KeySym.N2: None,
            tcod.event.KeySym.N3: None,
            tcod.event.KeySym.N4: None,
            tcod.event.KeySym.N5: None,
            tcod.event.KeySym.N6: None,
            tcod.event.KeySym.N7: None,
            tcod.event.KeySym.N8: None,
            tcod.event.KeySym.N9: None,
            tcod.event.KeySym.N0: None,
        }
        
        self._mem: dict[tcod.event.KeySym, list[Item] | CharacterEffect | Spell | None] = self.items.copy()
        
    def add_fav(self, slot: tcod.event.KeySym, item: list[Item] | CharacterEffect | Spell) -> None:
        for s, i in self.items.items():
            if i == item:
                self.items[s] = None
                self._mem[s] = None
        
        self.items[slot] = item
        self._mem[slot] = copy.deepcopy(item)
        
    def remove_fav(self, slot: tcod.event.KeySym | None = None, item: list[Item] | CharacterEffect | Spell | None = None) -> None:
        if slot:
            self.items[slot] = None
            self._mem[slot] = None
        elif item:
            i = list(self.items.keys())[list(self.items.values()).index(item)]
            self.items[i] = None
            self._mem[i] = None
            
        
    def activate_slot(self, slot) -> Action | None:
        from entity import Item
        from entity_effect import CharacterEffect
        from magic import Spell
        
        thing = self.items[slot]
        if isinstance(thing, list) and all(isinstance(t, Item) for t in thing):
            return thing[0].effect.get_action()
        elif isinstance(thing, CharacterEffect):
            return thing.get_action()
        elif isinstance(thing, Spell):
            return thing.get_action(self.parent.engine)
        
    def update(self) -> None:
        from entity import Item
        
        
        for slot, item in self.items.items():
            # If new items get added that are the same add them to favorites
            if isinstance(item, list) and all(isinstance(t, Item) for t in item):
                for i in self.parent.inventory_as_stacks:
                    if item[0].similar(i[0]):
                        self.add_fav(slot, i)
                        
            # Look to see if favorites items are no longer in inventory and remove
            if isinstance(item, list) and all(isinstance(t, Item) for t in item) and item not in self.parent.inventory_as_stacks:
                self.items[slot] = None
            
        # Look in mem to see if new items should be added to favorites
        for slot, item in self._mem.items():
            if not item:
                continue
            if not self.items[slot] and isinstance(item, list) and all(isinstance(t, Item) for t in item):
                for i in self.parent.inventory_as_stacks:
                    if item[0].similar(i[0]):
                        self.add_fav(slot, i)
                        
        
        
        