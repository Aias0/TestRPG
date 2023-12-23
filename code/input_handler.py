from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Dict, List

import tcod
from tcod import libtcodpy

import textwrap, math, time

from actions import (
    Action,
    EscapeAction,
    BumpAction,
    PickupAction,
    WaitAction,
)

import color, exceptions
from item_types import ItemTypes

from message_log import MessageLog

from config import SETTINGS

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item
    from sprite import Sprite, Actor
    
KEY_ACTION = {
    'move_up': (0, -1),
    'move_down': (0, 1),
    'move_left': (-1, 0),
    'move_right': (1, 0),
    'move_up_right': (1, -1),
    'move_up_left': (-1, -1),
    'move_down_right': (1, 1),
    'move_down_left': (-1, 1),
    'wait': None
}

MOVE_KEY = {
    tcod.event.KeySym.w: KEY_ACTION['move_up'],
    tcod.event.KeySym.s: KEY_ACTION['move_down'],
    tcod.event.KeySym.a: KEY_ACTION['move_left'],
    tcod.event.KeySym.d: KEY_ACTION['move_right'],
    tcod.event.KeySym.e: KEY_ACTION['move_up_right'],
    tcod.event.KeySym.q: KEY_ACTION['move_up_left'],
    tcod.event.KeySym.x: KEY_ACTION['move_down_right'],
    tcod.event.KeySym.z: KEY_ACTION['move_down_left'],
}

WAIT_KEY = {
    tcod.event.KeySym.PERIOD: KEY_ACTION['wait'],
}

CURSOR_Y_KEYS = {
    tcod.event.KeySym.UP: -1,
    tcod.event.KeySym.DOWN: 1,
}

class EventHandler(tcod.event.EventDispatch[Action]):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.engine.wait = True
    
    def handle_events(self, event: tcod.event.Event) -> None:
        self.handle_action(self.dispatch(event))
        
    def handle_action(self, action: Optional[Action]) -> bool:
        """ Handle actions return from event methods.
        
        Returns True if the action will advance a turn. """
        
        if action is None:
            return False
        
        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False # Skip enemy turn on exceptions.
        
        self.engine.handle_npc_turns()
        
        self.engine.update_fov()
        return True
            
    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y
    
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()
    
    def on_render(self, console: tcod.console.Console) -> None:
        self.engine.render(console)
    
class AskUserEventHandler(EventHandler):
    """ Handles user input for actions which require special input. """
    def handle_action(self, action: Action | None) -> bool:
        """ Returns to the main event handler when a valid action is performed. """
        if super().handle_action(action):
            self.engine.event_handler = MainGameEventHandler(self.engine)
            return True
        return False
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        """ By default any key exits this input handler. """
        if event.sym in { # Ignore modifier keys.
            tcod.event.KeySym.LSHIFT,
            tcod.event.KeySym.RSHIFT,
            tcod.event.KeySym.LCTRL,
            tcod.event.KeySym.RCTRL,
            tcod.event.KeySym.LALT,
            tcod.event.KeySym.RALT,
        }:
            return None
        return self.on_exit()
    
    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[Action]:
        """ By default any mouse click exits this input handler. """
        return self.on_exit()
    
    def on_exit(self) -> Optional[Action]:
        """ Called when the user is trying to exit or cancel an action.
        
        By default this returns to the main event handler. """
        self.engine.event_handler = MainGameEventHandler(self.engine)
        return None


class MenuCollectionEventHandler(EventHandler):
    def __init__(self, engine: Engine, submenu: int = 0) -> None:
        super().__init__(engine)
        self.menus: list[SubMenuEventHandler] = [
            StatusMenuEventHandler(engine, '@'),
            EquipmentEventHandler(engine, 'Equipment'),
            InventoryEventHandler(engine, 'Inventory'),
        ]
        for menu in self.menus:
            menu.parent = self
        self.selected_menu = submenu
        self.engine.wait = False
        self.engine.event_handler = self.menus[self.selected_menu]
        self.latest_message = self.engine.message_log.messages[-1]
        self.latest_message_count = self.engine.message_log.messages[-1].count

    def on_render(self, console: tcod.console.Console) -> None:
        if isinstance(self.engine.event_handler, MenuCollectionEventHandler):
            self.engine.event_handler = self.menus[self.selected_menu]
        console.draw_rect(x=0, y=0, width=console.width, height=1, ch=ord('─'), fg=color.ui_color)
        menu_x = 1
        for i, menu in enumerate(self.menus):
            title = menu.title
            menu.menu_x = menu_x
            if i == self.selected_menu:
                title_border = f'╢{"".join([" "]*len(title))}╟'
                title_color = color.ui_cursor_text_color
                
                if self.latest_message != self.engine.message_log.messages[-1] or self.latest_message_count != self.engine.message_log.messages[-1].count:
                    menu.display_message = True
                    self.latest_message = self.engine.message_log.messages[-1]
                    self.latest_message_count = self.engine.message_log.messages[-1].count
                
            else:
                title_border = f'┤{"".join([" "]*len(title))}├'
                title_color = color.ui_text_color
            console.print_box(x=menu_x,y=0, width=len(title_border), height=1, string=title_border, fg=color.ui_color)
            console.print_box(x=menu_x+1,y=0, width=len(title), height=1, string=title, fg=title_color)
            menu_x+=len(title_border)+1
        
        console.print(x=console.width-2, y=0, string='├', fg=color.ui_color)
        
        sp_string = f'SP: {self.engine.player.entity.sp}/{self.engine.player.entity.max_sp}'
        console.print(x=console.width-len(sp_string)-2, y=0, string=sp_string, fg=color.ui_text_color)
        console.print(x=console.width-len(sp_string)-3, y=0, string='│', fg=color.ui_color)
        
        mp_string = f'MP: {self.engine.player.entity.mp}/{self.engine.player.entity.max_mp}'
        console.print(x=console.width-len(mp_string)-len(sp_string)-3, y=0, string=mp_string, fg=color.ui_text_color)
        console.print(x=console.width-len(mp_string)-len(sp_string)-4, y=0, string='│', fg=color.ui_color)
        
        hp_string = f'HP: {self.engine.player.entity.hp}/{self.engine.player.entity.max_hp}'
        console.print(x=console.width-len(hp_string)-len(mp_string)-len(sp_string)-4, y=0, string=hp_string, fg=color.ui_text_color)
        
        console.print(x=console.width-len(hp_string)-len(mp_string)-len(sp_string)-5, y=0, string='┤', fg=color.ui_color)
        
            
class SubMenuEventHandler(EventHandler):
    parent: MenuCollectionEventHandler
    def __init__(self, engine: Engine, title: str):
        self.engine = engine
        self.title = title
        self.menu_x = None
        self.engine.wait = False
        
        self.message_max_time = 150
        self.message_time = None
        self.display_message = False
        self.allow_display_message = True
        
    def on_render(self, console: tcod.console.Console) -> None:
        self.parent.on_render(console)
        menu_console = tcod.console.Console(console.width, console.height-1)
        
        
        
        self.display_latest_message(menu_console)
        menu_console.blit(console, dest_x=0, dest_y=1)
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        key = event.sym
        if key == tcod.event.KeySym.ESCAPE:
            self.engine.event_handler = MainGameEventHandler(self.engine)
        
        elif key in range(49, 49+len(self.parent.menus)):
            i = key - 49
            self.parent.selected_menu = i
            self.engine.event_handler = self.parent.menus[i]
            
        #elif key in [tcod.event.KeySym.d, tcod.event.KeySym.RIGHT]:
        #    if self.parent.selected_menu + 1 < len(self.parent.menus):
        #        self.parent.selected_menu += 1
        #        self.engine.event_handler = self.parent.menus[self.parent.selected_menu]
        #elif key in [tcod.event.KeySym.a, tcod.event.KeySym.LEFT]:
        #    if self.parent.selected_menu - 1 >= 0:
        #        self.parent.selected_menu -= 1
        #        self.engine.event_handler = self.parent.menus[self.parent.selected_menu]
    
    def display_latest_message(self, console: tcod.console.Console, x:int = None, y: int = None):

        if not self.display_message and self.allow_display_message:
            return
        
        message = self.engine.message_log.messages[-1]
        message_text = list(MessageLog.wrap(message.plain_text, 36))
        
        message_console = tcod.console.Console(width=min(len(message.plain_text)+2, 38), height=len(message_text)+2)
        
        message_console.draw_frame(x=0, y=0, width=message_console.width, height=message_console.height, fg=color.ui_color)
        
        loc_x = x or int(console.width/2)-int(message_console.width/2)
        loc_y= y or console.height-message_console.height-2
        
        y=1
        for line in message_text:
            message_console.print(x=1, y=y, string=line, fg=message.fg)
            y += 1
            
        message_console.blit(console, dest_x=loc_x, dest_y=loc_y)
        if self.message_time is None:
            self.message_time = time.time()

        time_clear = len(message.plain_text.split())*1/(SETTINGS['words_per_minute']/60 + .5)
        if time.time() - self.message_time >= time_clear:
            self.display_message = False
            self.message_time = None
        
        
        
        
        
class StatusMenuEventHandler(SubMenuEventHandler):
    def on_render(self, console: tcod.console.Console) -> None:
        self.parent.on_render(console)
        menu_console = tcod.console.Console(console.width, console.height-1)
        
        player = self.engine.player.entity
        
        x_offset = 5
        
        name_bar_text = f'Name: {player.name}'
        menu_console.print(x=x_offset, y=3, string=name_bar_text, fg=color.ui_text_color)
        menu_console.print_box(x=x_offset-1, y=4, width=len(name_bar_text)+2, height=1, string=f'╘{"".join(["═"]*(len(name_bar_text)))}╛', fg=color.ui_color)
        
        race_text = f'Race: {player.race.name}'
        menu_console.print(x=len(name_bar_text)+x_offset+4, y=3, string=race_text, fg=color.ui_text_color)
        menu_console.print_box(x=len(name_bar_text)+x_offset+3, y=4, width=len(race_text)+2, height=1, string=f'╘{"".join(["═"]*(len(race_text)))}╛', fg=color.ui_color)
        
        job_text = f'Job: {player.job.name}'
        menu_console.print(x=len(name_bar_text)+len(race_text)+x_offset+8, y=3, string=job_text, fg=color.ui_text_color)
        menu_console.print_box(x=len(name_bar_text)+len(race_text)+x_offset+7, y=4, width=len(job_text)+2, height=1, string=f'╘{"".join(["═"]*(len(job_text)))}╛', fg=color.ui_color)
        
        attr_title_y = 7
        if player.titles:
            attr_title_y = 11
            title_text = f'Title: {player.titles[0]}'
            menu_console.print(x=x_offset, y=6, string=title_text, fg=color.ui_text_color)
            menu_console.print_box(x=x_offset-1, y=7, width=len(title_text)+2, height=1, string=f'└{"".join(["─"]*(len(title_text)))}└', fg=color.ui_color)
        
        
        menu_console.print(x=x_offset, y=attr_title_y, string='Attributes', fg=color.ui_text_color)
        menu_console.print_box(x=x_offset-1, y=attr_title_y+1, width=len('Attributes')+2, height=1, string=f'╘{"".join(["═"]*(len("Attributes")))}╛', fg=color.ui_color)
        menu_console.print(x=x_offset, y=attr_title_y+1, string='╤', fg=color.ui_color)
        
        
        attr_y = attr_title_y + 3
        attrs = {'CON': player.CON, 'STR': player.STR, 'END': player.END, 'DEX': player.DEX, 'FOC': player.FOC, 'INT': player.INT}
        for attr in attrs:
            menu_console.print(x=x_offset, y=attr_y-1, string='├', fg=color.ui_color)
            menu_console.print(x=x_offset, y=attr_y, string='│', fg=color.ui_color)
            player.INT_intrinsic_bonus
            
            attr_string = f'{attr}: {attrs[attr]}'

            extrinsic_bonus = getattr(player, f'{attr}_extrinsic_bonus')
            intrinsic_bonus = getattr(player, f'{attr}_intrinsic_bonus')
            if extrinsic_bonus or intrinsic_bonus:
                attr_string += f' ({getattr(player, f"base_{attr}")} + '
            
                if extrinsic_bonus:
                    attr_string += f'{extrinsic_bonus}'
                if extrinsic_bonus and intrinsic_bonus:
                    attr_string += ' + '
                if intrinsic_bonus:
                    attr_string += f'{intrinsic_bonus}'

                attr_string += ')'
            
            menu_console.print(x=x_offset+1, y=attr_y, string=attr_string, fg=color.ui_text_color)
            
            attr_y+=2
        menu_console.print(x=x_offset, y=attr_y-1, string='└', fg=color.ui_color)
            
        self.display_latest_message(menu_console)
        menu_console.blit(console, dest_x=0, dest_y=1)
        
class EquipmentEventHandler(SubMenuEventHandler):
    def __init__(self, engine, title: str):
        super().__init__(engine, title)
        self.selected_slot = -1
        self.slots = ['Head', 'Chest', 'Gloves', 'Legs', 'Boots', 'Amulet', 'Right Ring', 'Left Ring', 'Right Hand', 'Left Hand']
    
    def on_render(self, console: tcod.console.Console) -> None:
        self.parent.on_render(console)
        menu_console = tcod.console.Console(console.width, console.height-1)
        
        slot_y = 3
        for i, slot in enumerate(self.slots):
            self.equip_slot(menu_console, x=5, y=slot_y, title=slot, index=i)
            slot_y += 4
            if slot in ['Boots', 'Left Ring']:
                slot_y += 1
        
        self.display_latest_message(menu_console)
        menu_console.blit(console, dest_x=0, dest_y=1)
        
    def equip_slot(self, console: tcod.console.Console, x: int, y: int, title: str, index: int) -> None:
        item_in_slot = self.engine.player.entity.equipment[title]
        if item_in_slot:
            item_name = item_in_slot.name.capitalize()
        else:
            item_name = ''
            
        slot_color = {True: color.ui_cursor_text_color, False: color.ui_text_color}
        console.print(x=x, y=y, string=title, fg=slot_color[index==self.selected_slot])
        console.print_box(x=x-1, y=y+1, width=len(title)+2, height=1, string=f'╘{"".join(["═"]*(len(title)))}╛', fg=color.ui_color)
        console.print(x=x, y=y+1, string='╤', fg=color.ui_color)
        
        console.print(x=x+2, y=y+2, string=item_name, fg=color.ui_text_color)
        console.print(x=x, y=y+2, string='│', fg=color.ui_color)
        console.print(x=x, y=y+3, string='└', fg=color.ui_color)
        console.print(x=x+1, y=y+3, string=f'{"".join(["─"]*(max(len(item_name), 11)))}', fg=color.ui_color)
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        super().ev_keydown(event)
        match event.sym:
            
            case tcod.event.KeySym.DOWN:
                self.selected_slot = min(self.selected_slot+1, len(self.slots)-1)
            case tcod.event.KeySym.UP:
                self.selected_slot = max(self.selected_slot-1, -1)
            case tcod.event.KeySym.HOME:
                self.selected_slot = 0
            case tcod.event.KeySym.END:
                self.selected_slot = len(self.slots)-1
                
            case tcod.event.KeySym.BACKSPACE:
                self.engine.player.entity.unequip(list(self.engine.player.entity.equipment.values())[self.selected_slot])
            case tcod.event.KeySym.RETURN:
                # Choose compatible item to equip.
                pass
        
    
class InventoryEventHandler(SubMenuEventHandler):
    def __init__(self, engine: Engine, title: str):
        super().__init__(engine, title)
        self.item_stacks = self.engine.player.entity.inventory_as_stacks
        self.selected_item = -1
        self.page_amount = max(math.ceil(len(self.item_stacks)/33), 1)
        self.current_page = 1
        self.current_page_num_items = None
        self.items_on_page = None
        self.max_items_on_page = 26
    
    def on_render(self, console: tcod.console.Console) -> None:
        self.parent.on_render(console)
        menu_console = tcod.console.Console(console.width, console.height-1)
        self.item_stacks = self.engine.player.entity.inventory_as_stacks
        self.page_amount = max(math.ceil(len(self.item_stacks)/33), 1)
        
        weight = self.engine.player.entity.weight
        weight_text = f'Total Weight: {weight}'
        menu_console.print_box(x=5, y=3, width=len(weight_text), height=1, string=weight_text, fg=color.ui_text_color)
        menu_console.print_box(x=4, y=4, width=len(weight_text)+2, height=1, string=f'╘{"".join(["═"]*(len(weight_text)))}╛', fg=color.ui_color)
        
        carry_weight = self.engine.player.entity.carry_weight
        carry_weight_text = f'Carrying Capacity: {carry_weight}'
        menu_console.print_box(x=menu_console.width-len(carry_weight_text)-5, y=3, width=len(carry_weight_text), height=1, string=carry_weight_text, fg=color.ui_text_color)
        menu_console.print_box(x=menu_console.width-len(carry_weight_text)-6, y=4, width=len(carry_weight_text)+2, height=1, string=f'╘{"".join(["═"]*(len(carry_weight_text)))}╛', fg=color.ui_color)

        for page_num in range(1, self.page_amount+1):
            if self.current_page != page_num:
                continue
            self.items_on_page = self.item_stacks[(self.max_items_on_page)*(page_num-1):(self.max_items_on_page)*page_num]
            self.current_page_num_items = len(self.items_on_page)
            if self.selected_item not in range(-1, len(self.items_on_page)):
                self.selected_item = len(self.items_on_page)-1
            
            menu_console.print(x=4, y=6, string='┌', fg=color.ui_color)
            menu_console.print(x=menu_console.width-5, y=6, string='┐', fg=color.ui_color)
            for i in range(max(len(self.items_on_page), 1)):
                menu_console.print(x=4, y=7+i, string='│', fg=color.ui_color)
                menu_console.print(x=menu_console.width-5, y=7+i, string='│', fg=color.ui_color)
            menu_console.print(x=4, y=7+max(len(self.items_on_page), 1), string='└', fg=color.ui_color)
            menu_console.print(x=menu_console.width-5, y=7+max(len(self.items_on_page), 1), string='┘', fg=color.ui_color)
                
            y = 7
            for i, stack in enumerate(self.items_on_page):
                item_amount = ''
                equipped = ''
                if i == self.selected_item:
                    text_color = color.ui_cursor_text_color
                else:
                    text_color = color.ui_text_color
                
                if len(stack) > 1:
                    item_amount = f'({len(stack)})'
                if self.engine.player.entity.is_equipped(stack[0]):
                    equipped = '[E]'
                
                menu_console.print(x=5, y=y, string=f'{chr(i+65)} - {stack[0].name}{equipped} {item_amount}', fg=text_color)
                weight_text = f'[{stack[0].weight*len(stack)}]'
                menu_console.print(x=menu_console.width-5-len(weight_text), y=y, string=weight_text, fg=text_color)
                y+=1
            
            if page_num < self.page_amount:
                menu_console.print(x=menu_console.width-10, y=7+max(len(self.items_on_page), 1), string='...>', fg=color.ui_text_color)
            if page_num > 1:
                menu_console.print(x=6, y=7+max(len(self.items_on_page), 1), string='<...', fg=color.ui_text_color)
                
        if self.selected_item in range(0, len(self.items_on_page)):
            desc_console = tcod.console.Console(22, 5)
            desc_console.draw_frame(0, 0, desc_console.width, desc_console.height, fg=color.ui_color)
            for i, line in enumerate(textwrap.wrap(self.items_on_page[self.selected_item][0].description, desc_console.width-2, expand_tabs=True)):
                desc_console.print(x=1, y=i+1, string=line, fg=color.ui_text_color)

            desc_console.blit(menu_console, dest_x=menu_console.width-4-22, dest_y=43)

        self.display_latest_message(menu_console)
        menu_console.blit(console, dest_x=0, dest_y=1)
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        super().ev_keydown(event)
        
        key = event.sym
        if key in range(tcod.event.KeySym.a, min(tcod.event.KeySym.a+self.current_page_num_items, tcod.event.KeySym.z+1)):
            self.selected_item = key - tcod.event.KeySym.a
        
        elif key == tcod.event.KeySym.DOWN:
            if self.selected_item + 1 < self.current_page_num_items:
                self.selected_item += 1
        elif key  == tcod.event.KeySym.UP:
            if self.selected_item - 1 >= -1:
                self.selected_item -= 1
        
        elif key == tcod.event.KeySym.RIGHT:
            self.selected_item = -1
            if self.current_page+1 <= self.page_amount:
                self.current_page += 1
        elif key == tcod.event.KeySym.LEFT:
            self.selected_item = -1
            if self.current_page-1 >= 1:
                self.current_page -= 1
        
        elif key == tcod.event.KeySym.BACKSPACE and self.selected_item != -1:
            if len(self.items_on_page[self.selected_item]) > 1:
                handle_drop = DropAmountEventHandler(self.engine, self.items_on_page[self.selected_item])
                handle_drop.parent = self
                self.engine.event_handler = handle_drop
            else:
                self.engine.player.entity.drop_inventory(self.items_on_page[self.selected_item][0])
                
        elif key == tcod.event.KeySym.RETURN:
            try:
                self.items_on_page[self.selected_item][0].effect.activate()
            except NotImplementedError:
                pass
            except exceptions.Impossible as exc:
                self.engine.message_log.add_message(exc.args[0], color.impossible)
                
            
class DropAmountEventHandler(EventHandler):
    parent: InventoryEventHandler
    def __init__(self, engine: Engine, stack: list[Item]):
        super().__init__(engine)
        self.stack = stack
        self.amount = 1
        self.engine.wait = False
    
    def on_render(self, console: tcod.console.Console) -> None:
        

        drop_console = tcod.console.Console(22, 5)

        drop_console.draw_frame(0, 0, drop_console.width, drop_console.height, fg=color.ui_color)
        drop_console.print(x=2, y=2, string= 'Drop Amount:', fg=color.ui_text_color)
        amount_max = f'/{len(self.stack)}'
        drop_console.print(x=drop_console.width-len(amount_max)-2, y=2, string=amount_max, fg=color.ui_text_color)
        amount_current = f'{self.amount}'
        drop_console.print(x=drop_console.width-len(amount_max)-len(amount_current)-2, y=2, string=amount_current, fg=color.ui_cursor_text_color)

        self.parent.on_render(console)
        drop_console.blit(console, dest_x=4, dest_y=44)
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.ESCAPE:
                self.engine.event_handler = self.parent
                
            case tcod.event.KeySym.UP:
                self.amount = min(self.amount+1, len(self.stack))
            case tcod.event.KeySym.DOWN:
                self.amount = max(self.amount-1, 1)
                
            case tcod.event.KeySym.HOME:
                self.amount = len(self.stack)
            case tcod.event.KeySym.END:
                self.amount = 1
                
            case tcod.event.KeySym.t:
                for item in self.stack:
                    self.engine.player.entity.drop_inventory(item)
                self.engine.event_handler = self.parent
                
            case tcod.event.KeySym.RETURN:
                for item in self.stack[:self.amount]:
                    self.engine.player.entity.drop_inventory(item)
                self.engine.event_handler = self.parent
        
        
class MenuListEventHandler(EventHandler):
    def __init__(self, engine: Engine, menu_items):
        super().__init__(engine)
        self.selected_index = 0
        self.menu_items = menu_items
        self.selected_items: list = []
        
    def on_render(self, console: tcod.console.Console):
        super().on_render(console)
        
        menu_console = tcod.console.Console(len(max(self.menu_items, key=len))+2, len(self.menu_items)+4)
        
        menu_console.draw_frame(0, 0, menu_console.width, menu_console.height, fg=color.ui_color)
        menu_console.print(x=menu_console.width-2, y=0, string='╥', fg=color.ui_color)
        menu_console.print(x=menu_console.width-2, y=1, string='╚', fg=color.ui_color)
        menu_console.print(x=menu_console.width-1, y=1, string='╡', fg=color.ui_color)
        
        menu_console.print(x=1, y=0, string='╥', fg=color.ui_color)
        menu_console.print(x=1, y=1, string='╝', fg=color.ui_color)
        menu_console.print(x=0, y=1, string='╞', fg=color.ui_color)
        
        menu_console.print(x=1, y=menu_console.height-1, string='╨', fg=color.ui_color)
        menu_console.print(x=1, y=menu_console.height-2, string='╗', fg=color.ui_color)
        menu_console.print(x=0, y=menu_console.height-2, string='╞', fg=color.ui_color)
        
        menu_console.print(x=menu_console.width-2, y=menu_console.height-1, string='╨', fg=color.ui_color)
        menu_console.print(x=menu_console.width-2, y=menu_console.height-2, string='╔', fg=color.ui_color)
        menu_console.print(x=menu_console.width-1, y=menu_console.height-2, string='╡', fg=color.ui_color)
        
        item_y = 2
        for i, item in enumerate(self.menu_items):
            if i==self.selected_index:
                color_choice = color.ui_cursor_text_color
            elif i in self.selected_items:
                color_choice = color.ui_selected_text_color
            else:
                color_choice = color.ui_text_color
            
            menu_console.print_box(x=1, y=item_y, width=menu_console.width-2, height=menu_console.height-2, string=item, fg=color_choice, alignment=libtcodpy.CENTER)
            item_y+=1
        
        menu_console.blit(console, dest_x=40-menu_console.width//2, dest_y=25-menu_console.height//2)
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.ESCAPE:
                self.engine.event_handler = MainGameEventHandler(self.engine)
            
            case tcod.event.KeySym.s | tcod.event.KeySym.DOWN:
                if  len(self.menu_items) > self.selected_index + 1:
                    self.selected_index +=1
                else:
                    self.selected_index = len(self.menu_items)-1
                    #self.selected_index = 0
            case tcod.event.KeySym.w | tcod.event.KeySym.UP:
                if  0 <= self.selected_index - 1:
                    self.selected_index -=1
                else:
                    self.selected_index = 0
                    #self.selected_index = len(self.menu_items)-1
            
            case tcod.event.KeySym.RETURN:
                match self.selected_index:
                    case 0: #
                        raise NotImplementedError()
                    case 1: #
                        raise NotImplementedError()
                    case 2: #
                        raise NotImplementedError()
                    case 3: #
                        raise NotImplementedError()
                    case 4: #
                        raise NotImplementedError()
        
class PauseMenuEventHandler(MenuListEventHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine, ['Resume', 'Save Game', 'Load Game', 'Settings', 'Exit to Main Menu', 'Exit'])
            
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.ESCAPE:
                self.engine.event_handler = MainGameEventHandler(self.engine)
                
            case tcod.event.KeySym.q:
                raise SystemExit()
            
            case tcod.event.KeySym.s | tcod.event.KeySym.DOWN:
                if  len(self.menu_items) > self.selected_index + 1:
                    self.selected_index +=1
                else:
                    self.selected_index = len(self.menu_items)-1
                    #self.selected_index = 0
            case tcod.event.KeySym.w | tcod.event.KeySym.UP:
                if  0 <= self.selected_index - 1:
                    self.selected_index -=1
                else:
                    self.selected_index = 0
                    #self.selected_index = len(self.menu_items)-1
            
            case tcod.event.KeySym.RETURN:
                match self.selected_index:
                    case 0: # Resume
                        self.engine.event_handler = MainGameEventHandler(self.engine)
                    case 1: # Save Game
                        raise NotImplementedError()
                    case 2: # Load Game
                        raise NotImplementedError()
                    case 3: # Settings
                        raise NotImplementedError()
                    case 4: # Exit to Main Menu
                        raise NotImplementedError()
                    case 5: # Exit
                        raise SystemExit()
                
class MultiPickupHandler(MenuListEventHandler):
    def __init__(self, engine: Engine, items: list[Sprite], actor: Actor):
        super().__init__(engine, [item.entity.name.title() for item in items])
        self.items = items
        self.actor = actor

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        def pickup(indexes):
            for i in indexes:
                result = self.actor.entity.add_inventory(self.items[i].entity)
                if not result:
                    self.engine.game_map.sprites.remove(self.items[i])
                    continue
                self.engine.message_log.add_message(result.args[0], color.impossible)
        match event.sym:
            case tcod.event.KeySym.ESCAPE:
                self.engine.event_handler = MainGameEventHandler(self.engine)
            
            case tcod.event.KeySym.s | tcod.event.KeySym.DOWN:
                if  len(self.menu_items) > self.selected_index + 1:
                    self.selected_index +=1
                else:
                    self.selected_index = len(self.menu_items)-1
                    #self.selected_index = 0
            case tcod.event.KeySym.w | tcod.event.KeySym.UP:
                if  0 <= self.selected_index - 1:
                    self.selected_index -=1
                else:
                    self.selected_index = 0
                    #self.selected_index = len(self.menu_items)-1
            
            case tcod.event.KeySym.t:
                pickup(list(range(len(self.items))))
                self.engine.event_handler = MainGameEventHandler(self.engine)
            case tcod.event.KeySym.g:
                if self.selected_index not in self.selected_items:
                    self.selected_items.append(self.selected_index)
                else:
                    self.selected_items.remove(self.selected_index)
            
            case tcod.event.KeySym.RETURN:
                if not self.selected_items:
                    self.selected_items = [self.selected_index]
                pickup(self.selected_items)
                self.engine.event_handler = MainGameEventHandler(self.engine)

class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None
        
        key = event.sym
        
        player = self.engine.player
        
        if key in MOVE_KEY:
            dx, dy = MOVE_KEY[key]
            action = BumpAction(player, dx, dy)
            
        elif key in WAIT_KEY:
            action = WaitAction(player)
            
        elif key == tcod.event.KeySym.ESCAPE:
            self.engine.event_handler = PauseMenuEventHandler(self.engine)
            
        elif key == tcod.event.KeySym.v:
            self.engine.event_handler = HistoryViewer(self.engine)
        
        elif key == tcod.event.KeySym.g:
            action = PickupAction(player)
            
        elif key == tcod.event.KeySym.m:
            self.engine.event_handler = MenuCollectionEventHandler(self.engine)
            
        elif key == tcod.event.KeySym.i:
            self.engine.event_handler = MenuCollectionEventHandler(self.engine, 2)
            
        elif key == tcod.event.KeySym.BACKSLASH and SETTINGS['dev_console']:
            self.engine.event_handler = DevConsole(self.engine)
            
        elif key in CURSOR_Y_KEYS:
            if self.engine.hover_depth + CURSOR_Y_KEYS[key] in range(self.engine.hover_range):
                self.engine.hover_depth += CURSOR_Y_KEYS[key]
            
        return action
    
class GameOverEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        if event.sym == tcod.event.KeySym.ESCAPE:
            raise SystemExit()
    
class HistoryViewer(EventHandler):
    """Print the history on a larger window which can be navigated."""
    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1
        
    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console) # Draw the main state as the background.
        
        log_console = tcod.console.Console(console.width - 41, console.height - 2)
        
        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height, fg=color.ui_color)
        log_console.print_box(
            0, 0, log_console.width, 1, '┤               ├', alignment=libtcodpy.CENTER, fg=color.ui_color
        )
        log_console.print_box(
            0, 0, log_console.width, 1, 'Message history', alignment=libtcodpy.CENTER, fg=color.ui_text_color
        )
        log_console.print(x=0, y=40, string='┤', fg=color.ui_color)
        log_console.print(x=log_console.width-1, y=40, string='├', fg=color.ui_color)
        
        # Render the message log using the cursor parameter.
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[:self.cursor+1],
        )
        log_console.blit(console, 20, 3)
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you're on the edge.
                #self.cursor = self.log_length - 1
                pass
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                #self.cursor = 0
                pass
            else:
                # Otherwise move while staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.KeySym.HOME:
            self.cursor = 0 # Move directly to the top message.
        elif event.sym == tcod.event.KeySym.END:
            self.cursor = self.log_length - 1 # Move directly to the last message.
        else: # Any other key moves back to the main game state.
            self.engine.event_handler = MainGameEventHandler(self.engine)
            
class TextInputHandler(EventHandler):
    def __init__(self, engine: Engine, x: int = 20, y: int = 41, width: int = None):
        super().__init__(engine)
        self.text_inputted = ''
        self.title = 'Input'
        self.input_index = -1
        self._cursor_blink = 40
        self.engine.wait = False
        
        self.x = x
        self.y = y
        self.width = width
    
    @property
    def cursor_blink(self) -> int:
        return self._cursor_blink
    @cursor_blink.setter
    def cursor_blink(self, amount: int) -> None:
        if self.cursor_blink >= 70:
            self._cursor_blink = 0
        else:
            self._cursor_blink = amount
            
    def on_render(self, console: tcod.console.Console):
        super().on_render(console) # Draw the main state as the background.
        if self.width is None:
            self.width = console.width - 41
            
        input_console = tcod.console.Console(self.width, 3)
        
        # Draw a frame with a custom banner title.
        input_console.draw_frame(0, 0, input_console.width, input_console.height, fg=color.ui_color)
        input_console.print_box(
            0, 0, input_console.width, 1, f'┤{"".join([" "]*len(self.title))}├', alignment=libtcodpy.CENTER, fg=color.ui_color
        )
        input_console.print_box(
            0, 0, input_console.width, 1, f'{self.title}', alignment=libtcodpy.CENTER, fg=color.ui_text_color
        )
        
        # Draw inputted text
        input_console.print(1, 1, self.text_inputted, fg=color.ui_text_color)
        # Draw blinking cursor
        if not len(self.text_inputted) >= self.width-2:
            if self.cursor_blink >= 40:
                input_console.print(x=1+len(self.text_inputted), y=1, string='▌', fg=color.ui_text_color)
            self.cursor_blink += 1
        
        # Connect to other ui elements
        if self.y+3 == 44:
            if self.x == 20:
                input_console.print(x=0, y=input_console.height-1, string='┼', fg=color.ui_color)
            else:
                input_console.print(x=0, y=input_console.height-1, string='┴', fg=color.ui_color)
                if self.x < 20:
                    input_console.print(x=20-self.x, y=input_console.height-1, string='┬', fg=color.ui_color)
            
            if self.x + input_console.width - 1 == 58:
                input_console.print(x=input_console.width-1, y=input_console.height-1, string='┼', fg=color.ui_color)
            else:
                input_console.print(x=input_console.width-1, y=input_console.height-1, string='┴', fg=color.ui_color)
                if self.x + self.width > 58:
                    input_console.print(x=58-self.x, y=input_console.height-1, string='┬', fg=color.ui_color)
        
        input_console.blit(console, self.x, self.y)
                
    def ev_textinput(self, event: tcod.event.TextInput) -> None:
        if not self.width:
            return # When first opening input box text can be inputted before render causing width to be None
        self.cursor_blink = 55
        if len(self.text_inputted) + len(event.text) > self.width-2:
            return
        self.text_inputted += event.text
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.RETURN:
    
                self.use_input()
                
                if len(self.engine.input_log) == 0 or self.engine.input_log[0] != self.text_inputted:
                    self.engine.input_log.insert(0, self.text_inputted)
                self.engine.event_handler = MainGameEventHandler(self.engine)
            case tcod.event.KeySym.BACKSPACE:
                self.cursor_blink = 55
                self.text_inputted = self.text_inputted[:-1]
                self.input_index = -1
                
            case tcod.event.KeySym.UP:
                if len(self.engine.input_log) > self.input_index+1:
                    self.input_index +=1
                    self.text_inputted = self.engine.input_log[self.input_index]
                        
            case tcod.event.KeySym.DOWN:
                self.input_index -=1
                if self.input_index > 0:
                    self.text_inputted = self.engine.input_log[self.input_index]
                else:
                    self.text_inputted = ''
            
            case tcod.event.KeySym.ESCAPE:
                self.engine.event_handler = MainGameEventHandler(self.engine)
                
    def use_input(self) -> None:
        raise NotImplementedError()
                
class DevConsole(TextInputHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.title = 'Dev Console'

    def use_input(self):
        from dev_tools import dev_command
        self.engine.message_log.add_message(dev_command(self.text_inputted, self.engine))
