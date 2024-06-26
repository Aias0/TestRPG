from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Dict, List, Callable, Tuple

import tcod
from tcod import libtcodpy

import numpy as np

import glob, os, exceptions

from tcod.event import KeyDown

import textwrap, math, time, configparser

import pyperclip
from tcod.console import Console
import actions

import render_functions

from datetime import datetime

from actions import (
    Action,
    DropItem,
    EffectAction,
    BumpAction,
    PickupAction,
    WaitAction,
)

import color, exceptions, copy
from game_types import ItemTypes

from message_log import MessageLog

import numpy as np

from config import SETTINGS, refresh_settings, tryeval

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item
    from sprite import Sprite, Actor
    from magic import AOESpell, AttackSpell
    from entity_effect import BaseEffect, CharacterEffect
    
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

class BaseEventHandler(tcod.event.EventDispatch[Action]):
    def handle_event(self, event: tcod.event.Event):
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self
    
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()
    
    def change_handler(self, new_handler: BaseEventHandler):
        self.engine.event_handler = new_handler

class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.engine.wait = True
    
    def handle_event(self, event: tcod.event.Event) -> None:
        self.handle_action(self.dispatch(event))
        
    def handle_action(self, action: Optional[Action]) -> bool:
        """ Handle actions return from event methods.
        
        Returns True if the action will advance a turn. """
        if hasattr(self.engine, 'update_fov'):
            self.engine.update_fov()
        
        if action is None:
            return False
        
        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False # Skip enemy turn on exceptions.
        
        self.engine.handle_npc_turns()
        
        for sprite in self.engine.game_map.sprites:
            sprite.entity.update()
        
        
        self.engine.turn_count += 1
        return True
            
    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        self.engine.mouse_location = event.tile.x, event.tile.y
    
    def on_render(self, console: tcod.console.Console) -> None:
        self.engine.render(console)
        
    def message(self, text: str, fg: tuple[int, int, int] = color.white):
        self.engine.message(text=text, fg=fg)


class LoadHandler(EventHandler):
    def __init__(self, engine: Engine, parent: EventHandler) -> None:
        self.engine = engine
        self.parent = parent
        
        self.selected_index = 0
        
        self.saved_games: list[str] = []
        for file in glob.glob("data\\user_data\\save_data\\*.sav"):
            self.saved_games.append(file)
        sg_sorted = sorted(self.saved_games, key=os.path.getctime, reverse=True)
        self.saved_games = [sg.replace('data\\user_data\\', '').replace('.sav', '') for sg in sg_sorted]
        self.create_times = [datetime.utcfromtimestamp(os.path.getctime(sg)).strftime('%Y-%m-%d %H:%M:%S') for sg in sg_sorted]
    
    def popup_result(self, result) -> None:
        if not result:
            return
        os.remove(f'data\\user_data\\{self.saved_games[self.selected_index]}.sav')
        self.selected_index = 0
        
    def on_render(self, console: tcod.console.Console) -> None:
        self.saved_games = []
        for file in glob.glob("data\\user_data\\*.sav"):
            self.saved_games.append(file)
        sg_sorted = sorted(self.saved_games, key=os.path.getctime, reverse=True)
        self.saved_games = [sg.replace('data\\user_data\\', '').replace('.sav', '') for sg in sg_sorted]
        self.create_times = [datetime.utcfromtimestamp(os.path.getctime(sg)).strftime('%Y-%m-%d %H:%M:%S') for sg in sg_sorted]
        
        saved_games_list_console = tcod.console.Console(25, 48)
        
        saved_games_list_console.draw_frame(0, 0, width=saved_games_list_console.width, height=saved_games_list_console.height, fg=color.ui_color)
        render_functions.draw_border_detail(saved_games_list_console)
        render_functions.draw_inner_border_detail(saved_games_list_console)

        saved_games_list_console.print(x=saved_games_list_console.width//2-len('Select Saved Game')//2, y=2, string='Select Saved Game', fg=color.ui_text_color)

        if not self.saved_games:
            saved_games_list_console.print(x=1, y=saved_games_list_console.height//2, string='No Saved Games Detected', fg=color.ui_text_color)

        sg_y = 5
        y_limit = saved_games_list_console.height - 10
        scroll_factor = max(self.selected_index-y_limit, 0)

        for i, save_game in enumerate(self.saved_games[scroll_factor:]):
            if i > y_limit:
                continue
            text_color = color.ui_text_color
            if i+scroll_factor == self.selected_index:
                text_color = color.ui_cursor_text_color
            
            saved_games_list_console.print(x=2, y=sg_y, string=save_game, fg=text_color)
            
            sg_y+=1
        
        saved_games_list_console.blit(console, dest_x=5, dest_y=1)
        
        saved_game_info_console = tcod.console.Console(24, 30)
        
        saved_game_info_console.draw_frame(0, 0, width=saved_game_info_console.width, height=saved_game_info_console.height, fg=color.ui_color)
        render_functions.draw_border_detail(saved_game_info_console)
        render_functions.draw_inner_border_detail(saved_game_info_console)
        
        saved_game_info_console.print(x=0, y=10, string=f'╠{"".join(["─"]*(saved_game_info_console.width-2))}╣')
        
        if self.saved_games:
            tileset = tcod.tileset.load_tilesheet(
                SETTINGS['tileset_file'], 16, 16, tcod.tileset.CHARMAP_CP437
            )
            from setup_game import load_game
            preview_engine = load_game(f'{self.saved_games[self.selected_index]}.sav')

            tile = tileset.get_tile(ord(preview_engine.player.char))[:, :, 3:]

            new_tile = np.zeros((10, 10, 3), dtype=np.uint8)
            for i, row in enumerate(new_tile):
                for j, col in enumerate(row):
                    for k, a in enumerate(col):
                        if tile[i, j] == 255:
                            new_tile[i, j, k] = preview_engine.player.color[k]
                        else:
                            new_tile[i, j, k] = 0


            img = tcod.image.Image.from_array(new_tile)
            img.blit(saved_game_info_console, x=saved_game_info_console.width//2, y=6, bg_blend=1, scale_x=1, scale_y=1, angle=0)
        
            y_offset = 12
            saved_game_info_console.print(x=2, y=y_offset, string=f'Name: {preview_engine.player.name}', fg=color.ui_text_color)
            saved_game_info_console.print(x=2, y=y_offset+1, string=f'Race: {preview_engine.player.entity.race.name}', fg=color.ui_text_color)
            saved_game_info_console.print(x=2, y=y_offset+2, string=f'Class: {preview_engine.player.entity.job.name} Lv{preview_engine.player.entity.level}', fg=color.ui_text_color)

            saved_game_info_console.print(x=2, y=y_offset+4, string=f'Number of Turns: {preview_engine.turn_count}', fg=color.ui_text_color)

            saved_game_info_console.print(x=2, y=y_offset+6, string=f'Save Created: \n{self.create_times[self.selected_index]}', fg=color.ui_text_color)
        
        saved_game_info_console.blit(console, dest_x=console.width-saved_game_info_console.width-5, dest_y=10)
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.ESCAPE:
                self.change_handler(self.parent)
            
            case tcod.event.KeySym.DOWN | tcod.event.KeySym.s:
                self.selected_index = min(self.selected_index+1, len(self.saved_games)-1)
            case tcod.event.KeySym.UP | tcod.event.KeySym.w:
                self.selected_index = max(self.selected_index-1, 0)
                
            case tcod.event.KeySym.BACKSPACE:
                self.change_handler(YNPopUp(self.engine, self))
                
            case tcod.event.KeySym.RETURN if self.saved_games:
                from setup_game import load_game
                self.engine = load_game(f'{self.saved_games[self.selected_index]}.sav')
                self.message('loaded game', color.valid)


class YNPopUp(EventHandler):
    def __init__(self, engine: Engine, parent: EventHandler, title: str | None = None, x: int | None = None, y: int | None = None):
        super().__init__(engine)
        self.x = x
        self.y = y
        self.title = title
        self.parent = parent
        
        self.selected_index = 0
        
    def on_render(self, console: tcod.console.Console):
        self.parent.on_render(console)
        
        popup_console = tcod.console.Console(7, 6)
        popup_console.draw_frame(0, 0, popup_console.width, popup_console.height)
        render_functions.draw_border_detail(popup_console)
        render_functions.draw_inner_border_detail(popup_console)
        
        yes_color = color.ui_text_color
        no_color = color.ui_text_color
        if self.selected_index == 0:
            yes_color = color.ui_cursor_text_color
        else:
            no_color = color.ui_cursor_text_color

        popup_console.print(x=2, y=2, string='Yes', fg=yes_color)
        popup_console.print(x=2, y=3, string='No', fg=no_color)
        
        if self.x is None:
            self.x = console.width//2-popup_console.width//2
        if self.y is None:
            self.y = console.height//2-popup_console.height//2
        popup_console.blit(console, dest_x=self.x, dest_y=self.y)
        
    def ev_keydown(self, event: tcod.event.KeyDown):
        match event.sym:
            case tcod.event.KeySym.DOWN | tcod.event.KeySym.s:
                self.selected_index = min(self.selected_index+1, 1)
            case tcod.event.KeySym.UP | tcod.event.KeySym.w:
                self.selected_index = max(self.selected_index-1, 0)
            
            case tcod.event.KeySym.RETURN:
                if self.selected_index == 0:
                    self.return_result(True)
                else:
                    self.return_result(False)
                    
            case tcod.event.KeySym.y:
                self.return_result(True)
            case tcod.event.KeySym.n:
                self.return_result(False)
    
    def return_result(self, result: bool):
        self.parent.popup_result(result)
        self.change_handler(self.parent)


class MenuCollectionEventHandler(EventHandler):
    def __init__(self, engine: Engine, submenu: int = 0) -> None:
        """ Stats: 0\n\nEquipment: 1\n\nInventory: 2\n\nAbilities: 3\n\nSpellbook: 4\n\n"""
        super().__init__(engine)
        self.menus: list[SubMenuEventHandler] = [
            StatusMenuEventHandler(engine, engine.player.char),
            EquipmentEventHandler(engine, 'Equipment'),
            InventoryEventHandler(engine, 'Inventory'),
            SubMenuEventHandler(engine, 'Abilities'),
        ]
        if engine.player.entity.spell_book:
            self.menus.append(SpellbookMenuHandler(engine, 'Spellbook'))
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
            menu_x+=len(title_border)
            if len(self.menus) ==4 or not (self.engine.player.entity.max_sp > 9 and self.engine.player.entity.max_mp > 9 and self.engine.player.entity.max_hp > 9):
                menu_x+=1
        
        console.print(x=console.width-2, y=0, string='├', fg=color.ui_color)
        
        sp_string = f'SP:{self.engine.player.entity.sp}/{self.engine.player.entity.max_sp}'
        console.print(x=console.width-len(sp_string)-2, y=0, string=sp_string, fg=color.ui_text_color)
        console.print(x=console.width-len(sp_string)-3, y=0, string='│', fg=color.ui_color)
        
        mp_string = f'MP:{self.engine.player.entity.mp}/{self.engine.player.entity.max_mp}'
        console.print(x=console.width-len(mp_string)-len(sp_string)-3, y=0, string=mp_string, fg=color.ui_text_color)
        console.print(x=console.width-len(mp_string)-len(sp_string)-4, y=0, string='│', fg=color.ui_color)
        
        hp_string = f'HP:{self.engine.player.entity.hp}/{self.engine.player.entity.max_hp}'
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
        match event.sym:
            case tcod.event.KeySym.ESCAPE:
                self.engine.event_handler = MainGameEventHandler(self.engine)

            case tcod.event.KeySym(sym) if sym in range(49, 49+len(self.parent.menus)) and not tcod.event.get_keyboard_state()[tcod.event.KeySym.f.scancode]:
                i = sym - 49
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
        self.selected_slot = 0
        self.slots = ['Head', 'Chest', 'Hand', 'Legs', 'Foot', 'Amulet', 'Right Ring', 'Left Ring', 'Right Hand', 'Left Hand']
    
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
            
        title += ':'
            
        slot_color = {True: color.ui_cursor_text_color, False: color.ui_text_color}
        
        console.print(x=x, y=y, string=title, fg=slot_color[index==self.selected_slot])
        
        if item_in_slot:
            item_name = f'({item_in_slot.char}){item_in_slot.name.capitalize()}'
            render_functions.print_color(console, x=x+len(title)+1, y=y, string=item_name, fg=color.ui_text_color, specific_color={1: item_in_slot.color})
        else:
            item_name = ''
        
        console.print(x=x-1, y=y+1, string=f'╘{"".join(["═"]*(len(title)))+"".join(["─"]*(max(10, len(item_name)+2)))}', fg=color.ui_color)
        
        """ console.print(x=x, y=y, string=title, fg=slot_color[index==self.selected_slot])
        console.print_box(x=x-1, y=y+1, width=len(title)+2, height=1, string=f'╘{"".join(["═"]*(len(title)))}╛', fg=color.ui_color)
        console.print(x=x, y=y+1, string='╤', fg=color.ui_color)
        
        console.print(x=x+2, y=y+2, string=item_name, fg=color.ui_text_color)
        console.print(x=x, y=y+2, string='│', fg=color.ui_color)
        console.print(x=x, y=y+3, string='└', fg=color.ui_color)
        console.print(x=x+1, y=y+3, string=f'{"".join(["─"]*(max(len(item_name), 11)))}', fg=color.ui_color) """
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        super().ev_keydown(event)
        match event.sym:
            
            case tcod.event.KeySym.DOWN:
                self.selected_slot = min(self.selected_slot+1, len(self.slots)-1)
            case tcod.event.KeySym.UP:
                self.selected_slot = max(self.selected_slot-1, 0)
            case tcod.event.KeySym.HOME:
                self.selected_slot = 0
            case tcod.event.KeySym.END:
                self.selected_slot = len(self.slots)-1
                
            case tcod.event.KeySym.BACKSPACE if self.selected_slot != -1:
                self.engine.player.entity.unequip(list(self.engine.player.entity.equipment.values())[self.selected_slot])
            case tcod.event.KeySym.RETURN if self.selected_slot != -1:
                equip_handle = EquipEventHandler(self.engine, self.slots[self.selected_slot])
                equip_handle.parent = self
                self.engine.event_handler = equip_handle

class EquipEventHandler(EventHandler):
    parent: EquipmentEventHandler
    def __init__(self, engine: Engine, slot: str) -> None:
        super().__init__(engine)
        self.slot = slot
        self.selected_item = 0
        self.engine.wait = False
        
    def on_render(self, console: tcod.console.Console) -> None:
        self.parent.on_render(console)
        
        self.items_for_slot = list({item for item in self.engine.player.entity.inventory if item.equippable[self.slot]})
        for item in self.items_for_slot:
            if self.engine.player.entity.is_equipped(item, self.slot):
                self.items_for_slot.remove(item)
                self.items_for_slot.insert(0, item)
        
        equip_console = tcod.console.Console(30, len(self.items_for_slot)+8)
        equip_console.draw_frame(0, 0, width=equip_console.width, height=equip_console.height, fg=color.ui_color)
        
        equip_title = f'Currently Equipped'
        equip_console.print_box(
            0, 0, equip_console.width, 1, f'┤{"".join([" "]*len(equip_title))}├', alignment=libtcodpy.CENTER, fg=color.ui_color
        )
        equip_console.print_box(
            0, 0, equip_console.width, 1, equip_title, alignment=libtcodpy.CENTER, fg=color.ui_text_color
        )
        
        
        equip_console.print(x=0, y=4, string=f'├{"".join(["─"]*(equip_console.width-2))}┤')
        
        
        equip_title = f'Equip {self.slot}'
        equip_console.print_box(
            0, 4, equip_console.width, 1, f'┤{"".join([" "]*len(equip_title))}├', alignment=libtcodpy.CENTER, fg=color.ui_color
        )
        equip_console.print_box(
            0, 4, equip_console.width, 1, equip_title, alignment=libtcodpy.CENTER, fg=color.ui_text_color
        )
        
        
        acronym = {'Head': 'H', 'Chest': 'C', 'Legs': 'L', 'Foot': 'F', 'Hand': 'H', 'Amulet': 'A', 'Left Ring': 'LR', 'Right Ring': 'RR', 'Right Hand': 'RH', 'Left Hand': 'LH'}
        y=6
        for i, item in enumerate(self.items_for_slot):
            text_color = color.ui_text_color
            extra = ''
            if i == self.selected_item:
                text_color = color.ui_cursor_text_color
            #elif self.engine.player.entity.is_equipped(item):
            #    text_color = color.ui_selected_text_color
                
            if self.engine.player.entity.is_equipped(item) and self.engine.player.entity.equipment[self.slot] != item:
                extra = f'[{[acronym[j[0]] for j in self.engine.player.entity.equipment.items() if j[1] == item][0]}]'
                
            if len(item.name) % 2 != 0:
                extra += ' '
                
            if self.engine.player.entity.is_equipped(item, self.slot):
                render_functions.print_color(equip_console, x=equip_console.width//2, y=2, string=f'({item.char}){item.name}{extra}', fg=text_color, alignment=tcod.constants.CENTER,  specific_color={1: item.color})
                #equip_console.print(x=equip_console.width//2, y=2, string=f'{item.name}{extra}', fg=text_color, alignment=tcod.constants.CENTER)
            else:
                render_functions.print_color(equip_console, x=2, y=y, string=f'({item.char}){item.name}{extra}', fg=text_color, specific_color={1: item.color})
                #equip_console.print(x=2, y=y, string=f'{item.name}{extra}', fg=text_color)
                y+=1
        
        equip_console.blit(console, dest_x=console.width-equip_console.width-4, dest_y=4)
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.ESCAPE:
                self.engine.event_handler = self.parent
            
            case tcod.event.KeySym.DOWN:
                self.selected_item = min(self.selected_item+1, len(self.items_for_slot)-1)
            case tcod.event.KeySym.UP:
                self.selected_item = max(self.selected_item-1, 0)
            case tcod.event.KeySym.HOME:
                self.selected_item = 0
            case tcod.event.KeySym.END:
                self.selected_item = len(self.items_for_slot)-1
                
            case tcod.event.KeySym.RETURN if self.selected_item != -1:
                self.engine.player.entity.equip(self.items_for_slot[self.selected_item], self.slot)
        
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
                    item_amount = f'(x{len(stack)})'
                if self.engine.player.entity.is_equipped(stack[0]):
                    equipped = '[E]'
                favorite = ''
                if [i for i in self.engine.player.entity.favorites.items.values() if i == stack]:
                    favorite = f'(F{list(self.engine.player.entity.favorites.items.values()).index(stack)+1})'
                
                menu_console.print(x=5, y=y, string=f'{chr(i+65)} - ({stack[0].parent.char}){stack[0].name}{equipped}{favorite} {item_amount}', fg=text_color)
                item_color = stack[0].parent.color
                if item_color == (0, 0, 0):
                    menu_console.print(x=5+len(f'{chr(i+65)} - ('), y=y, string=f' ', bg=(155,)*3)
                menu_console.print(x=5+len(f'{chr(i+65)} - ('), y=y, string=f'{stack[0].parent.char}', fg=item_color)
                weight_text = f'[{stack[0].weight*len(stack)}]'
                menu_console.print(x=menu_console.width-5-len(weight_text), y=y, string=weight_text, fg=text_color)
                y+=1
            
            if page_num < self.page_amount:
                menu_console.print(x=menu_console.width-10, y=7+max(len(self.items_on_page), 1), string='...>', fg=color.ui_text_color)
            if page_num > 1:
                menu_console.print(x=6, y=7+max(len(self.items_on_page), 1), string='<...', fg=color.ui_text_color)
                
        if self.selected_item in range(0, len(self.items_on_page)):
            desc_console = tcod.console.Console(35, 10)
            desc_console.draw_frame(0, 0, desc_console.width, desc_console.height, fg=color.ui_color)
            
            desc = self.items_on_page[self.selected_item][0].description
            
            desc_lines = desc.replace('\n', '\n').split('\n')
            
            current_line = 0
            for i, l_line in enumerate(desc_lines):
                for j, line in enumerate(textwrap.wrap(l_line, desc_console.width-2, expand_tabs=True)):
                    desc_console.print(x=1, y=current_line+1, string=line, fg=color.ui_text_color)
                    current_line += 1
                current_line += 1
                    

            desc_console.blit(menu_console, dest_x=menu_console.width-4-desc_console.width, dest_y=37)

        self.display_latest_message(menu_console)
        menu_console.blit(console, dest_x=0, dest_y=1)
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        super().ev_keydown(event)
        
        key = event.sym
        match event.sym:
            case tcod.event.KeySym(key) if key in range(tcod.event.KeySym.a, min(tcod.event.KeySym.a+self.current_page_num_items, tcod.event.KeySym.z+1)) and (event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT)):
                self.selected_item = key - tcod.event.KeySym.a

            case tcod.event.KeySym.DOWN if not event.mod:
                self.selected_item = min(self.selected_item + 1, self.current_page_num_items)
            case tcod.event.KeySym.UP if not event.mod:
                    self.selected_item = max(self.selected_item-1, -1)
            case tcod.event.KeySym.HOME if not event.mod:
                self.selected_item = 0
            case tcod.event.KeySym.END if not event.mod:
                self.selected_item = self.current_page_num_items-1

            case tcod.event.KeySym.RIGHT if not event.mod:
                self.selected_item = -1
                if self.current_page+1 <= self.page_amount:
                    self.current_page += 1
            case tcod.event.KeySym.LEFT if not event.mod:
                self.selected_item = -1
                if self.current_page-1 >= 1:
                    self.current_page -= 1

            case tcod.event.KeySym.BACKSPACE if self.selected_item != -1 and not event.mod:
                if len(self.items_on_page[self.selected_item]) > 1:
                    handle_drop = DropAmountEventHandler(self.engine, self.items_on_page[self.selected_item])
                    handle_drop.parent = self
                    self.engine.event_handler = handle_drop
                else:
                    self.engine.player.entity.drop_inventory(self.items_on_page[self.selected_item][0])

            case tcod.event.KeySym.RETURN if not event.mod and self.selected_item != -1:
                try:
                    action = self.items_on_page[self.selected_item][-1].effect.get_action()
                    return action
                except NotImplementedError:
                    pass
                except exceptions.Impossible as exc:
                    self.engine.message_log.add_message(exc.args[0], color.impossible)
                    
            case tcod.event.KeySym.e if not event.mod and self.selected_item != -1:
                if self.items_on_page[self.selected_item][-1].edible:
                    return actions.EatAction(self.engine.player, self.items_on_page[self.selected_item][-1].effect)
                self.engine.message_log.add_message(f'{self.items_on_page[self.selected_item][-1].name} is not edible.', color.impossible)
                
            case tcod.event.KeySym(sym) if sym in range(tcod.event.KeySym.N0, tcod.event.KeySym.N9+1) and tcod.event.get_keyboard_state()[tcod.event.KeySym.f.scancode] and self.selected_item != -1:
                stack = self.items_on_page[self.selected_item]
                self.engine.player.entity.favorites.add_fav(sym, stack)
            
            case tcod.event.KeySym(sym) if event.scancode == tcod.event.Scancode.GRAVE and not event.mod:
                stack = self.items_on_page[self.selected_item]
                self.engine.player.entity.favorites.remove_fav(item=stack)
                
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
        drop_console.blit(console, dest_x=4, dest_y=43)
        
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
                self.engine.event_handler = self.parent
                return DropItem(self.engine.player, self.stack)
                
            case tcod.event.KeySym.RETURN:
                self.engine.event_handler = self.parent
                return DropItem(self.engine.player, self.stack[:self.amount])

class AbilitiesMenuHandler(SubMenuEventHandler):
    pass

class SpellbookMenuHandler(SubMenuEventHandler):
    def __init__(self, engine: Engine, title: str):
        super().__init__(engine, title)

        self.selected_spell = -1

    def on_render(self, console: tcod.console.Console) -> None:
        self.parent.on_render(console)
        menu_console = tcod.console.Console(console.width, console.height-1)
        
        y = 4
        for i, spell in enumerate(self.engine.player.entity.spell_book):
            single_aoe = '•'
            if hasattr(spell, 'radius'):
                single_aoe = '○'
            text_color = color.ui_text_color
            if i == self.selected_spell:
                text_color = color.ui_cursor_text_color
            favorite = ''
            if [i for i in self.engine.player.entity.favorites.items.values() if i == spell]:
                favorite = f'(F{list(self.engine.player.entity.favorites.items.values()).index(spell)+1})'
                
            menu_console.print(x=5, y=y, string=f'{single_aoe} - [{spell.cost}]:{spell.name}{favorite}', fg=text_color)
            y+=1
        
        self.display_latest_message(menu_console)
        menu_console.blit(console, dest_x=0, dest_y=1)
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        super().ev_keydown(event)
        
        match event.sym:
            case tcod.event.KeySym.DOWN:
                self.selected_spell = min(self.selected_spell + 1, len(self.engine.player.entity.spell_book)-1)
            case tcod.event.KeySym.UP:
                self.selected_spell = max(self.selected_spell-1, -1)
            case tcod.event.KeySym.HOME:
                self.selected_spell = 0
            case tcod.event.KeySym.END:
                self.selected_spell = len(self.engine.player.entity.spell_book)-1
                
            case tcod.event.KeySym.RETURN:
                try:
                    return self.engine.player.entity.spell_book[self.selected_spell].get_action(self.engine)
                except exceptions.Impossible as exc:
                    self.engine.message_log.add_message(exc.args[0], color.impossible)
                    
            case tcod.event.KeySym(sym) if sym in range(tcod.event.KeySym.N0, tcod.event.KeySym.N9+1) and tcod.event.get_keyboard_state()[tcod.event.KeySym.f.scancode] and self.selected_spell != -1:
                spell = self.engine.player.entity.spell_book[self.selected_spell]
                self.engine.player.entity.favorites.add_fav(sym, spell)



class SettingsMenuHandler(MenuCollectionEventHandler):
    def __init__(self, engine: Engine, main_menu: bool = False):
        self.engine = engine
        self.menus: list[SubMenuEventHandler] = [
            SubSettingsHandler(engine, 'Graphics'),
            SubSettingsHandler(engine, 'Display'),
            SubSettingsHandler(engine, 'Controls'),
            SubSettingsHandler(engine, 'Gameplay'),
            SubSettingsHandler(engine, 'Other'),
        ]
        for menu in self.menus:
            menu.parent = self
        self.selected_menu = 0
        
        self.longest_menu_name_len = max([len(menu.title) for menu in self.menus])
        
        self.main_menu = main_menu
        
        self.engine.wait = False
        self.engine.event_handler = self.menus[self.selected_menu]
        
    def on_render(self, console: tcod.console.Console) -> None:
        if isinstance(self.engine.event_handler, MenuCollectionEventHandler):
            self.engine.event_handler = self.menus[self.selected_menu]
        console.draw_rect(x=0, y=0, width=1, height=console.height, ch=ord('│'), fg=color.ui_color)
        console.draw_rect(x=self.longest_menu_name_len+1, y=0, width=1, height=console.height, ch=ord('│'), fg=color.ui_color)
        menu_y = 5
        for i, menu in enumerate(self.menus):
            title = menu.title
            if len(title) % 2 != 0:
                title = f'{title} '
            if i == self.selected_menu:
                title_color = color.ui_cursor_text_color
                console.print_box(x=0, y=menu_y-1, width=self.longest_menu_name_len+2, height=1, string=f'╘{"".join(["═",]*self.longest_menu_name_len)}╛', fg=color.ui_color)
                console.print_box(x=0, y=menu_y, width=self.longest_menu_name_len+2, height=1, string=f'{"".join([" ",]*(self.longest_menu_name_len+2))}', fg=color.ui_color)
                console.print_box(x=0, y=menu_y+1, width=self.longest_menu_name_len+2, height=1, string=f'╒{"".join(["═",]*self.longest_menu_name_len)}╕', fg=color.ui_color)
            else:
                console.print_box(x=0, y=menu_y-1, width=self.longest_menu_name_len+2, height=1, string=f'├{"".join(["─",]*self.longest_menu_name_len)}┤', fg=color.ui_color)
                console.print_box(x=0, y=menu_y+1, width=self.longest_menu_name_len+2, height=1, string=f'├{"".join(["─",]*self.longest_menu_name_len)}┤', fg=color.ui_color)
                title_color = color.ui_text_color
            
            console.print_box(x=1,y=menu_y, width=self.longest_menu_name_len+1, height=1, string=title, fg=title_color, alignment=libtcodpy.CENTER)
             
            menu_y+=5
            
class SubSettingsHandler(SubMenuEventHandler):
    parent: SettingsMenuHandler
    def __init__(self, engine: Engine, title: str):
        super().__init__(engine, title)
        self.selected_setting = -1
        self.parser = configparser.ConfigParser()
        self.parser.read('settings.ini')
        
        self.settings_section = self.parser[self.title.lower()]
        
    def return_text(self, text) -> None:
        self.parser.set(self.title.lower(), list(self.settings_section.keys())[self.selected_setting], text)
        with open('settings.ini', 'w') as file:
            self.parser.write(file)
        refresh_settings()
        
    def on_render(self, console: tcod.console.Console):
        self.parent.on_render(console)
        menu_console = tcod.console.Console(console.width-(self.parent.longest_menu_name_len+2), console.height)
        y = 4
        for i, item in enumerate(self.settings_section.items()):
            title, value = item
            if i == self.selected_setting:
                title_color = color.ui_cursor_text_color
            else:
                title_color = color.ui_text_color
            menu_console.print(x=4, y=y, string=f'{title.replace("_", " ").title()}: {value}', fg=title_color)
            y+=3
        
        menu_console.blit(console, self.parent.longest_menu_name_len+3, 0)
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.UP:
                self.selected_setting = max(self.selected_setting-1, -1)
            case tcod.event.KeySym.DOWN:
                self.selected_setting = min(self.selected_setting+1, len(self.settings_section.keys())-1)
            case tcod.event.KeySym.HOME:
                self.selected_setting = 0
            case tcod.event.KeySym.END:
                self.selected_setting = len(self.settings_section.keys())-1
                
            case tcod.event.KeySym.RETURN if self.selected_setting != -1:
                current_val = tryeval(list(self.settings_section.values())[self.selected_setting])
                print(current_val)
                if isinstance(current_val, bool):
                    self.return_text(str(not current_val))
                    return
                
                self.engine.event_handler = SettingsTextInputHandler(
                    self.engine,
                    x=self.parent.longest_menu_name_len+9+len(list(self.settings_section.keys())[self.selected_setting]),
                    y=4+self.selected_setting*3,
                    width=50,
                    parent=self,
                    default_text=list(self.settings_section.values())[self.selected_setting],
                    expected_type=type(current_val),
                )
                
            case tcod.event.KeySym.ESCAPE if self.parent.main_menu:
                from setup_game import MainMenu
                self.change_handler(MainMenu(self.engine))
                return
        super().ev_keydown(event)
    

class LevelUpMenuHandler(MenuCollectionEventHandler):
    def __init__(self, engine: Engine, main_menu: bool = False):
        self.engine = engine
        self.menus: list[SubLevelUpHandler] = [
            AttributesHandler(engine, self, 'Attributes'),
            #SubLevelUpHandler(engine, self, 'Skills'),
            #SubLevelUpHandler(engine, self, 'Other'),
        ]
        self.selected_menu = 0
        self.change_handler(self.menus[self.selected_menu])
        
        self.all_complete = all([menu.completed for menu in self.menus])
        
    def on_render(self, console: tcod.console.Console) -> None:
        self.all_complete = all([menu.completed for menu in self.menus])

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
            else:
                title_border = f'┤{"".join([" "]*len(title))}├'
                title_color = color.ui_text_color
            console.print_box(x=menu_x,y=0, width=len(title_border), height=1, string=title_border, fg=color.ui_color)
            console.print_box(x=menu_x+1,y=0, width=len(title), height=1, string=title, fg=title_color)
            menu_x+=len(title_border)+1
            
        player_info_console = tcod.console.Console(24, 30)
        
        player_info_console.draw_frame(0, 0, width=player_info_console.width, height=player_info_console.height, fg=color.ui_color)
        render_functions.draw_border_detail(player_info_console)
        render_functions.draw_inner_border_detail(player_info_console)
        
        player_info_console.print(x=0, y=10, string=f'╠{"".join(["─"]*(player_info_console.width-2))}╣')
        
        tileset = tcod.tileset.load_tilesheet(
            SETTINGS['tileset_file'], 16, 16, tcod.tileset.CHARMAP_CP437
        )
        tile = tileset.get_tile(ord(self.engine.player.char))[:, :, 3:]
        new_tile = np.zeros((10, 10, 3), dtype=np.uint8)
        for i, row in enumerate(new_tile):
            for j, col in enumerate(row):
                for k, a in enumerate(col):
                    if tile[i, j] == 255:
                        new_tile[i, j, k] = self.engine.player.color[k]
                    else:
                        new_tile[i, j, k] = 0
        img = tcod.image.Image.from_array(new_tile)
        img.blit(player_info_console, x=player_info_console.width//2, y=6, bg_blend=1, scale_x=1, scale_y=1, angle=0)
    
        y_offset = 12
        player_info_console.print(x=2, y=y_offset, string=f'Name: {self.engine.player.name}', fg=color.ui_text_color)
        player_info_console.print(x=2, y=y_offset+1, string=f'Level: {self.engine.player.entity.level}→{self.engine.player.entity.level+self.engine.player.entity.level_awaiting}', fg=color.ui_text_color)
        player_info_console.print(x=2, y=y_offset+3, string=f'Race: {self.engine.player.entity.race.name}', fg=color.ui_text_color)
        player_info_console.print(x=2, y=y_offset+4, string=f'Class: {self.engine.player.entity.job.name}', fg=color.ui_text_color)
        player_info_console.print(x=2, y=y_offset+6, string=f'Attributes:', fg=color.ui_text_color)
        attr_y = y_offset+7
        for i, attr in enumerate([
            'CON', 'STR', 'END', 'DEX', 'FOC', 'INT'
        ]):
            player_info_console.print(x=3, y=attr_y+i, string=f'{attr}: {self.engine.player.entity.__getattribute__(f"base_{attr}")} → {self.menus[0].answers[i]}', fg=color.ui_text_color)
        
        player_info_console.blit(console, dest_x=console.width-player_info_console.width-5, dest_y=10)
        self.info_width = player_info_console.width
        
    def finish_levelup(self):
        self.engine.player.entity.level = self.engine.player.entity.level+self.engine.player.entity.level_awaiting
        for i, attr in enumerate([
            'CON', 'STR', 'END', 'DEX', 'FOC', 'INT'
        ]):
            self.engine.player.entity.__setattr__(f"base_{attr}", self.menus[0].answers[i])
        
        self.engine.player.entity.update_stats()
        self.engine.player.entity.level_awaiting = 0
        self.change_handler(MainGameEventHandler(self.engine))

class SubLevelUpHandler(SubMenuEventHandler):
    def __init__(self, engine: Engine, parent: LevelUpMenuHandler, title: str):
        super().__init__(engine, title)
        self.parent: LevelUpMenuHandler = parent
        self.selected_index = 0
        self.menu_items = []
        
        self.completed = False
    def display_latest_message(self, console: Console, x: int = None, y: int = None):
        pass
    def on_render(self, console: Console) -> None:
        self.parent.on_render(console)
        
        if not self.parent.all_complete:
            return
        
        done_console = tcod.console.Console(len('Done')+4, 5)
        render_functions.draw_all_border(done_console)
        
        done_color = color.ui_text_color
        if self.selected_index == len(self.menu_items):
            done_color = color.ui_cursor_text_color
        done_console.print(x=2, y=2, string='Done', fg=done_color)
        
        done_console.blit(console, dest_x=console.width-self.parent.info_width//2-done_console.width//2-5, dest_y=console.height-done_console.height-3)
    
    def ev_keydown(self, event: KeyDown) -> None:
        done_index_extra = 0
        if self.parent.all_complete:
            done_index_extra = 1
        
        match event.sym:
            case tcod.event.KeySym.UP:
                self.selected_index = max(self.selected_index-1, 0)
            case tcod.event.KeySym.DOWN:
                self.selected_index = min(self.selected_index+1, len(self.menu_items)-1+done_index_extra)
                
            case tcod.event.KeySym.RETURN if self.selected_index == len(self.menu_items):
                self.parent.finish_levelup()
                
        
        super().ev_keydown(event)

class AttributesHandler(SubLevelUpHandler):
    def __init__(self, engine, parent: LevelUpMenuHandler, title: str):
        super().__init__(engine, parent, title)
        self.parent: LevelUpMenuHandler
        self.attribute_names = {'CON': 'Constitution', 'STR': 'Strength', 'END': 'Endurance', 'DEX': 'Dexterity', 'FOC': 'Focus', 'INT': 'Intelligence'}
        self.menu_items = list(self.attribute_names.keys())
        self.answers = [None,]*len(self.menu_items)
        for i, attr in enumerate(self.menu_items):
            self.answers[i] = self.engine.player.entity.__getattribute__(f"base_{attr}")
        
        self.selected_attr = None
        
        self.stat_max = 20+self.engine.player.entity.level + self.engine.player.entity.level_awaiting
        self.stat_mins = self.answers[:]
        
        add_points = self.engine.player.entity.level_awaiting*2
        
        self.total_points = sum(self.answers)+add_points
        self.points_remaining = self.total_points-sum(self.answers)
        
    def on_render(self, console: tcod.console.Console) -> None:
        if self.points_remaining == 0:
            self.completed = True
        else:
            self.completed = False
        
        console.print(x=3, y=8, string='Select Attributes:', fg=color.ui_text_color)
        self.points_remaining = self.total_points-sum(self.answers)
        console.print(x=28, y=8, string=f'Points Remaining: {self.points_remaining}', fg=color.ui_text_color)
        attr_y = 11
        for i, item in enumerate(self.menu_items):
            text_color = color.ui_text_color
            text2_color = color.ui_text_color
            if item == self.selected_attr:
                text_color = color.ui_selected_text_color
                text2_color = color.ui_cursor_text_color
            elif i == self.selected_index:
                text_color = color.ui_cursor_text_color
            
            
            console.print(x=5, y=attr_y, string=f'{self.attribute_names[item]}: ', fg=text_color)
            field_text = str(self.answers[i])
            if field_text is None:
                field_text = ''
            console.print(x=5+len(self.attribute_names[item])+2, y=attr_y, string=str(field_text), fg=text2_color)
            
            attr_y+=2
        
        super().on_render(console)
            
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if not self.selected_attr:
            super().ev_keydown(event)
        match event.sym:
            case tcod.event.KeySym.RETURN if not self.selected_attr and self.selected_index < len(self.menu_items):
                self.selected_attr = self.menu_items[self.selected_index]
                self.prev_val = self.answers[self.selected_index]
            
            case tcod.event.KeySym.UP | tcod.event.KeySym.w if self.selected_attr:
                if self.total_points-sum(self.answers) <= 0:
                    return
                self.answers[self.selected_index] = min(self.answers[self.selected_index]+1, self.stat_max)
            case tcod.event.KeySym.DOWN | tcod.event.KeySym.s if self.selected_attr:
                self.answers[self.selected_index] = max(self.answers[self.selected_index]-1, self.stat_mins[self.selected_index])
            case tcod.event.KeySym.HOME if self.selected_attr:
                self.answers[self.selected_index] = self.stat_mins[self.selected_index]
            case tcod.event.KeySym.END if self.selected_attr:
                self.answers[self.selected_index] = min(self.answers[self.selected_index]+self.points_remaining, self.stat_max)
            case tcod.event.KeySym.RETURN if self.selected_attr:
                self.selected_attr = None
            case tcod.event.KeySym.ESCAPE if self.selected_attr:
                self.answers[self.selected_index] = self.prev_val
                self.selected_attr = None
          
          
  
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
        render_functions.draw_border_detail(menu_console, fg=color.ui_color)
        render_functions.draw_inner_border_detail(menu_console, fg=color.ui_color)
        
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
        super().__init__(engine, ['Resume', 'Save Game', 'Load Game', 'Settings', 'Exit to Main Menu', 'Save and Exit', 'Exit'])
            
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.ESCAPE:
                self.engine.event_handler = MainGameEventHandler(self.engine)
                
            case tcod.event.KeySym.q:
                if SETTINGS['dev_mode']:
                    raise exceptions.QuitWithoutSaving()
                
                saves = glob.glob("data\\user_data\\*.sav")
                if saves:
                    sg_sorted = sorted(saves, key=os.path.getctime, reverse=True)
                    from setup_game import load_game
                    temp_load = load_game(sg_sorted[0])
                    if self.engine.turn_count == temp_load.turn_count:
                        raise exceptions.QuitWithoutSaving()
                raise SystemExit()
            
            case tcod.event.KeySym.s | tcod.event.KeySym.DOWN:
                self.selected_index = min(self.selected_index+1, len(self.menu_items)-1)
            case tcod.event.KeySym.w | tcod.event.KeySym.UP:
                self.selected_index = max(self.selected_index-1, 0)
            
            case tcod.event.KeySym.RETURN:
                match self.selected_index:
                    case 0: # Resume
                        self.change_handler(MainGameEventHandler(self.engine))
                    case 1: # Save Game
                        self.change_handler(BorderedTextInputHandler(self.engine, default_text=f'savegame{abs(hash(self.engine)) % (10 ** 5)}', title='Save Name', parent=self))
                    case 2: # Load Game
                        self.change_handler(LoadHandler(self.engine, self))
                    case 3: # Settings
                        self.change_handler(SettingsMenuHandler(self.engine))
                    case 4: # Exit to Main Menu
                        raise exceptions.ExitToMainMenu()
                    case 5: # Exit
                        raise SystemExit()
                    case 6: # Exit w/out save
                        raise exceptions.QuitWithoutSaving()
        
    def return_text(self, text):
        self.engine.save_as(f'{text}.sav')
        self.message('saved game', color.valid)
                
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


class FavoriteHandler(MenuListEventHandler):
    def __init__(self, engine: Engine, parent: EventHandler):
        self.engine = engine
        self.selected_index = 0
        self.menu_items = list(self.engine.player.entity.favorites.items.values())
        self.parent = parent
        self.engine.wait = False
        
    def on_render(self, console: tcod.console.Console):
        self.menu_items = list(self.engine.player.entity.favorites.items.values())
        self.parent.on_render(console)
        from entity import Item
        
        longest_name_len = 1
        for m_item in self.menu_items:
            if m_item is None:
                continue
            elif isinstance(m_item, list):
                if len(m_item) == 1 and len(m_item[0].name) > longest_name_len:
                    longest_name_len = len(m_item[0].name)
                elif len(m_item[0].name)+len(str(len(m_item))) > longest_name_len:
                    longest_name_len = len(m_item[0].name)+1+len(str(len(m_item)))
            else:
                if len(m_item.name) > longest_name_len:
                    longest_name_len = len(m_item.name)
        
        menu_console = tcod.console.Console(
            longest_name_len+3,
            len(self.menu_items)*2+1
        )
        menu_console.draw_frame(0, 0, 4, menu_console.height, fg=color.ui_color)
        
        item_y = 1
        prev_title = None
        for i, item in enumerate(self.menu_items):
            if i==self.selected_index:
                color_choice = color.ui_cursor_text_color
            else:
                color_choice = color.ui_text_color
            title = 'X'
            from entity import Item
            if isinstance(item, list) and all(isinstance(t, Item) for t in item):
                amount = len(item)
                amount_text = ''
                if amount > 1:
                    amount_text = f'x{amount}'
                title = f'{item[0].name}{amount_text}'
            elif hasattr(item, 'name'):
                title = item.name
            
            if len(title) > 1:
                menu_console.draw_rect(x=2, y=item_y-1, width=len(title), height=1, ch=ord('─'), fg=color.ui_color)
                menu_console.print(x=len(title)+2, y=item_y-1, string='┐', fg=color.ui_color)
                if prev_title is not None and len(title) < len(prev_title):
                    menu_console.print(x=len(title)+2, y=item_y-1, string='┬', fg=color.ui_color)
                menu_console.print(x=len(title)+2, y=item_y, string='│', fg=color.ui_color)
                menu_console.print(x=len(title)+2, y=item_y+1, string='┘', fg=color.ui_color)
                menu_console.draw_rect(x=2, y=item_y+1, width=len(title), height=1, ch=ord('─'), fg=color.ui_color)
                
                for j in range(2, 2+len(title)):
                    if i != 0 and menu_console.rgba[item_y-2, j][0] == ord('│'):
                        menu_console.print(y=item_y-1, x=j, string='┴', fg=color.ui_color)
                
                if i != 0 and menu_console.rgba[item_y-1, 3][0] != ord('─'):
                    menu_console.print(y=item_y-1, x=3, string='┴', fg=color.ui_color)
                
                if i != len(self.menu_items)-1:
                    menu_console.print(y=item_y+1, x=3, string='┬', fg=color.ui_color)
            
            menu_console.print(x=2, y=item_y, string=title.replace(' ', '↔'), fg=color_choice)
                    
            if i == 0:
                menu_console.print(y=item_y-1, x=1, string='┬', fg=color.ui_color)
                
            num = i+1
            if num >= 10:
                num = 0
            menu_console.print(y=item_y, x=0, string=f'{num}', fg=color_choice)
            menu_console.print(y=item_y, x=1, string='│', fg=color.ui_color)
            
            if i == len(self.menu_items)-1:
                menu_console.print(y=item_y+1, x=1, string='┴', fg=color.ui_color)
            else:
                menu_console.print(y=item_y+1, x=0, string='├', fg=color.ui_color)
                menu_console.print(y=item_y+1, x=1, string='┼', fg=color.ui_color)
                menu_console.print(y=item_y+1, x=2, string='─', fg=color.ui_color)
                if not len(title) > 1:
                    menu_console.print(y=item_y+1, x=3, string='┤', fg=color.ui_color)
                                
            item_y += 2
            prev_title = title
        
        for i, row in enumerate(menu_console.rgba):
            for j, tile in enumerate(row):
                if tile[0] == ord(' '):
                    menu_console.rgba[i, j] = (
                        ord(" "),
                        (0,)*4,
                        (0,)*4,
                    )
                elif tile[0] == ord('↔'):
                    menu_console.print(x=j, y=i, string=' ', fg=color.ui_text_color)
        
        menu_console.blit(console, dest_x=1, dest_y=10)
        
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
            
            case tcod.event.KeySym(sym) if sym in self.engine.player.entity.favorites.items:
                return self.engine.player.entity.favorites.activate_slot(sym)
            
            case tcod.event.KeySym.RETURN:
                return self.engine.player.entity.favorites.activate_slot(list(self.engine.player.entity.favorites.items.keys())[self.selected_index])


class DirectionInputHandler(EventHandler):
    def __init__(self, engine: Engine, callback: Callable[[Tuple[int, int], Optional[Action]]]):
        super().__init__(engine)
        self.callback = callback
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym(sym) if sym in MOVE_KEY and not event.mod:
                self.change_handler(MainGameEventHandler(self.engine))
                return self.callback(MOVE_KEY[sym])


class SelectTileHandler(EventHandler):
    """Handles asking the user for an tile on the map."""
    def __init__(self, engine: Engine) -> None:
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        """Check for key movement or confirmation keys."""
        match event.sym:
            case tcod.event.KeySym(sym) if sym in MOVE_KEY:
                modifier = 1 # Holding modifier keys will speed up key movement.
                if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                    modifier *= 5
                if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                    modifier *= 5
                if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                    modifier *= 5
                    
                x, y = self.engine.mouse_location
                dx, dy = MOVE_KEY[sym]
                x += dx * modifier
                y += dy * modifier
                # Clamp the cursor index to the map size.
                x = max(0, min(x, self.engine.game_map.width - 1))
                y = max(0, min(y, self.engine.game_map.height - 1))
                self.engine.mouse_location = x, y
                return None
            
            case tcod.event.KeySym.RETURN:
                return self.on_tile_selected(*self.engine.mouse_location)
            
            case tcod.event.KeySym.ESCAPE:
                self.engine.event_handler = MainGameEventHandler(self.engine)
                
            case tcod.event.KeySym(sym) if sym in CURSOR_Y_KEYS and self.engine.hover_depth + CURSOR_Y_KEYS[sym] in range(self.engine.hover_range):
                self.engine.hover_depth += CURSOR_Y_KEYS[sym]
            
            
        return super().ev_keydown(event)
    
    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[Action]:
        """ Left click confirms a selection. """
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_tile_selected(*event.tile)
            
        return super().ev_mousebuttondown(event)
    
    def on_tile_selected(self, x: int, y: int) -> Optional[Action]:
        """ Called when an index is selected. """
        return NotImplementedError()
    
class LookHandler(SelectTileHandler):
    """ Lets the player look around using the keyboard. """
    
    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)
        render_functions.draw_circle(console, '*', *self.engine.mouse_location, 1)
        #render_functions.draw_reticle(console, *self.engine.mouse_location)
        
    def on_tile_selected(self, x: int, y: int) ->None:
        """ Return to main handler. """
        self.engine.event_handler = MainGameEventHandler(self.engine)
        
class InspectHandler(SelectTileHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.show_info = False
        self.entity = None
    
    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)
        if not self.show_info:
            #render_functions.draw_circle(console, '*', *self.engine.mouse_location, 1)
            render_functions.draw_reticle(console, *self.engine.mouse_location)
            return
        
        display_console = tcod.console.Console(25, 11)
        display_console.draw_frame(0, 0, display_console.width, display_console.height, fg=color.ui_color)
        
        display_console.print(1, 1, string=f'Name: {self.entity.name}')
        display_console.print(1, 2, string=f'Age: {self.entity.age}')
        display_console.print(1, 3, string=f'Race: {self.entity.race.name}')
        display_console.print(1, 4, string=f'Job: {self.entity.job.name}')
        display_console.print(1, 5, string=f'Level: {self.entity.level}')
        
        display_console.print(1, 7, string=f'HP: {self.entity.hp}/{self.entity.max_hp}')
        display_console.print(1, 8, string=f'MP: {self.entity.mp}/{self.entity.max_mp}')
        display_console.print(1, 9, string=f'SP: {self.entity.sp}/{self.entity.max_sp}')
        
        display_console.blit(console, 5, 5)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        if not self.show_info:
            super().ev_keydown(event)
            return
        
        match event.sym:
            case tcod.event.KeySym.ESCAPE:
                self.engine.event_handler = MainGameEventHandler(self.engine)

    def on_tile_selected(self, x: int, y: int) ->None:
        """ Return to main handler. """
        actor = self.engine.game_map.get_actor_at_location(x, y)
        if actor:
            self.entity = actor.entity
            self.show_info = True
        else:
            self.engine.event_handler = MainGameEventHandler(self.engine)
        
class RangedAttackHandler(SelectTileHandler):
    """Handles targeting enemies at range. Only the enemies selected will be affected."""
    
    def __init__(self, engine: Engine, callback: Callable[[Tuple[int, int], Optional[Action]]], effect: BaseEffect | None = None, spell: AttackSpell | None = None, delay: float = .5) -> None:
        super().__init__(engine)
        
        self.effect = effect
        self.spell = spell
        if self.effect:
            self.attack = effect.spell
        elif self.spell:
            self.attack = spell
        
        self.callback = callback
        
        self.explosion_radius = 1
        self.radius = 1
        if hasattr(self.attack, 'radius'):
            self.radius = self.attack.radius

        self.attack_sent = False
        
        self.engine.wait = False
        
        self.points: List[Tuple[int, int]] | None = None
        self.prev_time: float | None = None
        
        self.delay = delay
        self.points_on_map = []
    
    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)
        if not self.attack_sent:
            render_functions.draw_circle(console, '*', *self.engine.mouse_location, self.radius, fg=self.attack.color)
            return
        for point in self.points_on_map:
            console.print(*point, '*', fg=self.attack.color)

        if self.points and self.prev_time is None:
            self.prev_time = time.time()
            self.points_on_map.append(self.points.pop(0))
            console.print(*self.points_on_map[0], '*', fg=self.attack.color)
        elif self.points and time.time() - self.prev_time >= self.delay:
            self.points_on_map.append(self.points.pop(0))
            console.print(*self.points_on_map[-1], '*', fg=self.attack.color)
            self.prev_time = time.time()
        
        
        if not self.points and self.radius > 1:
            self.engine.event_handler = ExplosionHandler(self.engine, self, *self.engine.mouse_location, self.radius, self.delay*.75, '*', fg=self.attack.color)
            return
            
        
        if not self.points:
            self.handle_action(self.on_tile_selected(*self.engine.mouse_location))
            self.engine.event_handler = MainGameEventHandler(self.engine)
            self.engine.wait = False
            self.engine.event_handler.on_render(console)
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.RETURN:
                from entity_effect import ScrollEffect
                scroll_cast = isinstance(self.effect, ScrollEffect)
                try:
                    self.attack.check_cast_conditions(self.engine.player.entity, self.engine.mouse_location, scroll_cast)
                except exceptions.Impossible as exc:
                    self.engine.message_log.add_message(exc.args[0], color.impossible)
                    return
                self.points = render_functions.line((self.engine.player.x, self.engine.player.y), self.engine.mouse_location)[1:]
                self.attack_sent = True
            case _:
                super().ev_keydown(event)
    
    def on_tile_selected(self, x: int, y: int) -> Action | None:
        return self.callback((x, y))


class ExplosionHandler(EventHandler):
    def __init__(self, engine: Engine, parent, x: int, y: int, radius: int, delay: float, char: str = '*', fg: Tuple[int, int, int] = [255, 255, 255]) -> None:
        super().__init__(engine)
        self.delay = delay
        self.prev_time = None
        
        self.parent = parent
        
        self.char = char
        self.x = x
        self.y = y
        self.fg = fg
        
        self.radius = radius
        self.current_rad = 1
        
    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)
        
        if self.prev_time is None:
            self.prev_time = time.time()
            
        if self.current_rad < self.radius:
            render_functions.draw_circle(console, self.char, self.x, self.y, self.current_rad, fg=self.fg)
            self.current_rad += 1
        else:
            self.engine.event_handler = MainGameEventHandler(self.engine)
            self.handle_action(self.parent.on_tile_selected(self.x, self.y))
        

class MainGameEventHandler(EventHandler):
    def on_render(self, console: Console) -> None:
        return super().on_render(console)
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None
        
        player = self.engine.player
        key = event.sym
        match event.sym:
            case tcod.event.KeySym.ESCAPE if not event.mod: # Pause
                self.engine.event_handler = PauseMenuEventHandler(self.engine)
            
            case tcod.event.KeySym(sym) if sym in MOVE_KEY and not event.mod: # Move
                dx, dy = MOVE_KEY[sym]
                action = BumpAction(player, dx, dy)
            
            case tcod.event.KeySym(sym) if sym in WAIT_KEY and not event.mod: # Wait
                action = WaitAction(player)
                
            case tcod.event.KeySym(sym) if sym in self.engine.player.entity.favorites.items and not event.mod: # Quick favorite
                return self.engine.player.entity.favorites.activate_slot(sym)
            
            case tcod.event.KeySym.f if not event.mod: # General Interact
                action = actions.InteractAction(player)
                
            case tcod.event.KeySym.PERIOD if (event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT)):
                action = actions.TakeStairsAction(player)
            
            case tcod.event.KeySym.v if not event.mod: # Message History
                self.change_handler(HistoryViewer(self.engine))
        
            case tcod.event.KeySym.p if not event.mod: # Pick Up
                action = PickupAction(player)
                
            case tcod.event.KeySym.e if (event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT)): # Eat/use off ground
                try:
                    sprite_under = self.engine.game_map.get_sprite_at_location(self.engine.player.x, self.engine.player.y, {self.engine.player})
                    from entity import Item
                    if sprite_under is not None and isinstance(sprite_under.entity, Item):
                        item: Item = sprite_under.entity
                        item.holder = self.engine.player.entity
                        action = item.effect.get_action()
                        return action
                except NotImplementedError:
                    pass
                except exceptions.Impossible as exc:
                    self.engine.message_log.add_message(exc.args[0], color.impossible)
            
            case tcod.event.KeySym.N2 if (event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT)): # Stats Menu
                self.change_handler(MenuCollectionEventHandler(self.engine))

            case tcod.event.KeySym.i if not event.mod: # Inventory Menu
                self.change_handler(MenuCollectionEventHandler(self.engine, 2))
                
            case tcod.event.KeySym.TAB if not event.mod: # Equipment Menu
                self.change_handler(MenuCollectionEventHandler(self.engine, 1))
                
            case tcod.event.KeySym.s if (event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT)): # Spellbook
                if self.engine.player.entity.spell_book:
                    self.change_handler(MenuCollectionEventHandler(self.engine, 4))
                
            case tcod.event.KeySym(sym) if event.scancode == tcod.event.Scancode.GRAVE and not event.mod: # Favorites Menu
                self.change_handler(FavoriteHandler(self.engine, self))
            
            case tcod.event.KeySym.BACKSLASH if SETTINGS['dev_mode'] and not event.mod: # Dev console
                self.change_handler(DevConsole(self.engine))
                
            case tcod.event.KeySym.o if SETTINGS['dev_mode'] and not event.mod: # Dev tester
                from sprite_data import door
                from entity import Door
                d: Door = door.spawn(self.engine.game_map, *self.engine.mouse_location).entity
                d.lock(1)
                
            case tcod.event.KeySym.l if not event.mod: # Look/inspect
                if SETTINGS['dev_mode']:
                    self.change_handler(InspectHandler(self.engine))
                else:
                    self.change_handler(LookHandler(self.engine))
            
            case tcod.event.KeySym.l if self.engine.player.entity.level_awaiting and (event.mod & tcod.event.Modifier.SHIFT): # Level up
                self.change_handler(LevelUpMenuHandler(self.engine))
            
            case tcod.event.KeySym(sym) if sym in CURSOR_Y_KEYS and not event.mod:
                if self.engine.hover_depth + CURSOR_Y_KEYS[key] in range(self.engine.hover_range):
                    self.engine.hover_depth += CURSOR_Y_KEYS[key]
            
            case tcod.event.KeySym.F5: # Quick Save
                files = glob.glob("data\\user_data\\quicksave*.sav")
                save_num = 1
                if files:
                    os.remove(files[0])
                    save_num = int(files[0].replace("data\\user_data\\quicksave_", '').replace(".sav", ''))+1
                
                self.engine.save_as(f'quicksave_{save_num}.sav')
                self.message('quick save', color.valid)
                print('quick save')
                
            case tcod.event.KeySym.F9: # Quick load
                from setup_game import load_game
                
                files = glob.glob("data\\user_data\\quicksave*.sav")
                if files:
                    self.engine = load_game(files[0].replace("data\\user_data\\", ''))
                    self.message('quick load', color.valid)
                    print('quick load')
            
        return action

class GameOverEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        match event.sym:
            case tcod.event.KeySym.ESCAPE:
                raise exceptions.QuitWithoutSaving()

            case tcod.event.KeySym.BACKSLASH if SETTINGS['dev_mode']:
                self.engine.event_handler = DevConsole(self.engine)
                    
    def ev_quit(self, event: tcod.event.Quit) -> None:
        raise exceptions.QuitWithoutSaving()

class HistoryViewer(EventHandler):
    """Print the history on a larger window which can be navigated."""
    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1
        
    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console) # Draw the main state as the background.
        
        log_console = tcod.console.Console(console.width - 39, console.height - 2)
        
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
    def __init__(self, engine: Engine, x: int = 20, y: int = 41, width: int = None, parent: EventHandler = None, title: str = 'Input', default_text: str = '', expected_type: type | None = None):
        super().__init__(engine)
        self.text_inputted = str(default_text)
        self.expected_type = expected_type
        self.highlighted_text = 0
        self.cursor_pos = len(self.text_inputted)
        
        self.title = title
        self.input_index = -1
        self._cursor_blink = 40
        self.engine.wait = False
        
        self.x = x
        self.y = y
        self.width = width
        
        self.parent = parent
        if self.parent is None:
            self.parent = MainGameEventHandler(engine)
    
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
        self.parent.on_render(console) # Draw the main state as the background.
        self.engine.wait = False
        if self.width is None:
            self.width = console.width - 41
            
        input_console = tcod.console.Console(self.width, 1)
        # Draw inputted text
        input_console.print(0, 0, self.text_inputted, fg=color.ui_text_color)
        # Highlight Text
        if self.highlighted_text != 0:
            input_console.print(len(self.text_inputted)-len(self.text_inputted[self.highlighted_text:]), 0, self.text_inputted[self.highlighted_text:], fg=color.black, bg=color.ui_text_color)

        # Draw blinking cursor
        elif not len(self.text_inputted) >= self.width-2:
            if self.cursor_blink >= 40:
                input_console.print(x=self.cursor_pos, y=0, string='▌', fg=color.ui_text_color)
            self.cursor_blink += 1
        input_console.blit(console, self.x, self.y)
            
    def ev_textinput(self, event: tcod.event.TextInput) -> None:
        self.highlighted_text = 0
        if not self.width:
            return # When first opening input box text can be inputted before render causing width to be None
        self.cursor_blink = 55
        if len(self.text_inputted) + len(event.text) > self.width-2:
            return
        #self.text_inputted += event.text
        self.text_inputted = self.text_inputted[:self.cursor_pos] + event.text + self.text_inputted[self.cursor_pos:]
        self.cursor_pos += 1
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.RETURN:
                if self.expected_type and not isinstance(tryeval(self.text_inputted), self.expected_type):
                    raise TypeError(f'Expected {self.expected_type.__name__} got {type(tryeval(self.text_inputted)).__name__}')
                self.use_input()
                
                if len(self.engine.input_log) == 0 or self.engine.input_log[0] != self.text_inputted:
                    self.engine.input_log.insert(0, self.text_inputted)
                self.engine.event_handler = self.parent
            case tcod.event.KeySym.BACKSPACE:
                self.cursor_blink = 55
                if self.highlighted_text != 0 and self.text_inputted[self.highlighted_text:]:
                    self.text_inputted = self.text_inputted[:self.highlighted_text]
                    self.highlighted_text = 0
                elif self.cursor_pos != 0:
                    self.text_inputted = self.text_inputted[:self.cursor_pos-1] + self.text_inputted[self.cursor_pos:]
                    self.input_index = -1
                    self.cursor_pos -= 1
                
            case tcod.event.KeySym.UP:
                self.highlighted_text = 0
                if len(self.engine.input_log) > self.input_index+1:
                    self.input_index +=1
                    self.text_inputted = self.engine.input_log[self.input_index]
                    self.cursor_pos = len(self.text_inputted)
                        
            case tcod.event.KeySym.DOWN:
                self.highlighted_text = 0
                self.input_index -=1
                if self.input_index > 0:
                    self.text_inputted = self.engine.input_log[self.input_index]
                else:
                    self.text_inputted = ''
                self.cursor_pos = len(self.text_inputted)
            
            case tcod.event.KeySym.ESCAPE:
                self.engine.event_handler = self.parent
    
            case tcod.event.KeySym.v if (event.mod & tcod.event.Modifier.CTRL):
                self.text_inputted += pyperclip.paste()
                self.cursor_pos = len(self.text_inputted)
            case tcod.event.KeySym.c if (event.mod & tcod.event.Modifier.CTRL):
                pyperclip.copy(self.text_inputted[self.highlighted_text:])
                
            case tcod.event.KeySym.LEFT:
                self.cursor_blink = 55
                if (event.mod & tcod.event.Modifier.SHIFT):
                    self.highlighted_text = max(self.highlighted_text-1, -len(self.text_inputted))
                self.cursor_pos = max(self.cursor_pos-1, 0)
            case tcod.event.KeySym.RIGHT:
                self.cursor_blink = 55
                if (event.mod & tcod.event.Modifier.SHIFT):
                    self.highlighted_text = min(self.highlighted_text+1, 0)
                else:
                    self.highlighted_text = 0
                self.cursor_pos = min(self.cursor_pos+1, len(self.text_inputted))
            case tcod.event.KeySym.a if (event.mod & tcod.event.Modifier.CTRL):
                self.highlighted_text = -len(self.text_inputted)
                self.cursor_pos = 0
                
            
                    
    def use_input(self) -> None:
        self.parent.return_text(self.text_inputted)

class SettingsTextInputHandler(TextInputHandler):
    parent: SubSettingsHandler
    def use_input(self):
        self.parent.return_text(self.text_inputted)

class BorderedTextInputHandler(TextInputHandler):
    def on_render(self, console: tcod.console.Console):
        self.parent.on_render(console) # Draw the main state as the background.
        self.engine.wait = False
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
        # Highlight Text
        if self.highlighted_text != 0:
            input_console.print(len(self.text_inputted)-len(self.text_inputted[self.highlighted_text:])+1, 1, self.text_inputted[self.highlighted_text:], fg=color.black, bg=color.ui_text_color)

        # Draw blinking cursor
        elif not len(self.text_inputted) >= self.width-2:
            if self.cursor_blink >= 40:
                input_console.print(x=self.cursor_pos+1, y=1, string='▌', fg=color.ui_text_color)
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
                
class DevConsole(BorderedTextInputHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.title = 'Dev Console'

    def use_input(self):
        from dev_tools import dev_command
        self.engine.message_log.add_message(dev_command(self.text_inputted, self.engine))
