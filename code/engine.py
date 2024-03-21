from __future__ import annotations
from typing import TYPE_CHECKING, Set, Iterable, Any

import tcod
from tcod.console import Console
from tcod.map import compute_fov

import exceptions
from input_handler import MainGameEventHandler
from message_log import MessageLog
from render_functions import render_resource_bar, render_names_at_mouse_location

import numpy as np
import color

import glob, os

from sprite import Actor
from favorites import PlayerFavorites

import dill
import lzma
import pickle

if TYPE_CHECKING:
    from game_map import GameMap, GameLocation
    from input_handler import EventHandler
    from entity import Item
    from sprite import Sprite, Actor
    from magic import AOESpell, AttackSpell
    from entity_effect import BaseEffect, CharacterEffect
    
class MainMenuEngine:
    def __init__(self):
        from setup_game import MainMenu
        self.event_handler: EventHandler = MainMenu(self)
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.wait = False
        self.input_log = []
        
    def render(self, console: Console) -> None:
        pass
    

class Engine:
    game_map: GameMap
    game_location: GameLocation
    
    def __init__(self, player: Actor):
        self.event_handler: EventHandler = MainGameEventHandler(self)
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        
        self.player = player
        self.player.entity.favorites = PlayerFavorites(self.player.entity)
        
        self.input_log = []
        self.wait = True
        self.hover_depth = 0
        self.hover_range = 1
        self.old_hover_range = 1
        
        # DEV Stuff
        self.wallhacks = False
        self.omniscient = False
        self.ai_on = True
        self.no_clip = False
        
        self.turn_count = 0
        self._blink_counter = 0
        
    def message(self, text: str, fg: tuple[int, int, int] = color.white):
        self.message_log.add_message(text=text, fg=fg)
        
    def handle_npc_turns(self) -> None:
        for sprite in self.game_map.sprites - {self.player} - {sprite for sprite in self.game_map.sprites if not isinstance(sprite, Actor)}:
            sprite: Actor
            sprite.entity.update()
            if sprite.ai and self.ai_on:
                try:
                    sprite.ai.perform()
                except exceptions.Impossible:
                    pass # Ignore impossible action exceptions from AI.
            
    def update_fov(self) -> None:
        """ Recompute the visible area based on the players point of view. """
        
        visible = np.copy(self.game_map.tiles['transparent'])

        for sprite in self.game_map.sprites:
            if sprite.blocks_fov:
                visible[sprite.x, sprite.y] = False

        self.game_map.visible[:] = compute_fov(
            visible,
            (self.player.x, self.player.y),
            radius=8,
        )
        if self.omniscient:
            self.game_map.visible = np.full(self.game_map.visible.shape, True)
        
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible
        
    @property
    def blink_counter(self) -> int:
        return self._blink_counter
    @blink_counter.setter
    def blink_counter(self, amount: int) -> None:
        self._blink_counter = amount
        if self.blink_counter >= 70:
            self._blink_counter = 0
            
    
    def render(self, console: Console) -> None:
        self.game_map.render(console)
        
        console.draw_rect(x=0, y=43, width=console.width, height=1, ch=ord('─'), fg=color.ui_color)
        #console.print(x=0, y=43, string='╟', fg=color.ui_color)
        #console.print(x=console.width-1, y=43, string='╢', fg=color.ui_color)
        console.print(x=1, y=43, string=f'┤{"".join([" "]*len(self.player.entity.name))}├', fg=color.ui_color)
        console.print(x=2, y=43, string=f'{self.player.entity.name}', fg=color.ui_text_color)
        
        level_border = f'┤{"".join([" "]*(len(str(self.player.entity.level))+3))}├'
        level_text = self.player.entity.level
        level_color = color.ui_text_color
        if self.player.entity.level_awaiting:
            level_border = f'┤{"".join([" "]*(len(str(self.player.entity.level))+3))}├'
            level_text = '↑'
            
            level_color = color.ui_text_color
            if self.blink_counter >= 40:
                level_color = color.ui_selected_text_color
            self.blink_counter += 1
            
        console.print(x=19-len(level_border), y=43, string=level_border, fg=color.ui_color)
        console.print(x=20-len(level_border), y=43, string=f'Lv:{level_text}', fg=level_color)
        
        self.message_log.render(console=console, x=21, y=45, width=console.width-41, height=5)
        console.print(x=20, y=43, string='┬', fg=color.ui_color)
        console.draw_rect(x=20, y=44, width=1, height=40, ch=ord('│'), fg=color.ui_color)
        console.print(x=console.width-20, y=43, string='┬', fg=color.ui_color)
        console.draw_rect(x=console.width-20, y=44, width=1, height=40, ch=ord('│'), fg=color.ui_color)
        
        #console.print(x=20+(console.width-40)//2, y=43, string='┼', fg=color.ui_color)
        
        render_resource_bar(
            x=0,
            y=45,
            resource='hp',
            console=console,
            current_val=self.player.entity.hp,
            maximum_val=self.player.entity.max_hp,
            total_width=20
        )
        render_resource_bar(
            x=0,
            y=47,
            resource='mp',
            console=console,
            current_val=self.player.entity.mp,
            maximum_val=self.player.entity.max_mp,
            total_width=20
        )
        render_resource_bar(
            x=0,
            y=49,
            resource='sp',
            console=console,
            current_val=self.player.entity.sp,
            maximum_val=self.player.entity.max_sp,
            total_width=20
        )
        
        if self.hover_range != self.old_hover_range:
            self.hover_depth = 0
        render_names_at_mouse_location(console=console, x=20+(console.width-40)//2, y=44, engine=self, alignment=tcod.constants.CENTER)
        self.old_hover_range = self.hover_range
        
    def save_as(self, filename: str) -> None:
        """ Save this instance as a compressed file. """
        save_data = lzma.compress(pickle.dumps(self))
        
        with open(f'data/user_data/{filename}', 'wb') as f:
            f.write(save_data)