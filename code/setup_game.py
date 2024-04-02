"""Handle the loading and initialization of game sessions."""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from config import SETTINGS

import copy, color, time
import tcod, libtcodpy
import lzma, dill, pickle

import glob, os

import numpy as np
from numpy.typing import NDArray

import traceback

from world import GameLocation
import input_handler
import render_functions

from engine import Engine
import item_data
from magic import SPELLS

from races import RACES
from jobs import JOBS

from config import tryeval

if TYPE_CHECKING:
    from races import BaseRace
    from jobs import BaseJob
    from sprite import Actor

background_image = None
#try:
#    background_image = tcod.image.load("menu_background.png")[:, :, :3]
#except:
#    pass
    
def new_game(player: Actor) -> Engine:
    """Return a brand new game session as an Engine instance."""
    map_width = 80
    map_height = 43
    
    room_max_size = 10
    room_min_size = 6
    max_rooms = [20, 30]
    
    max_enemies_per_room = (0, 2)
    max_items_per_room = (0, 2)
    
    for i in range(2):
        player.entity.add_inventory(copy.deepcopy(item_data.health_potion), silent=True)
    
    engine = Engine(player=player)
    
    engine.game_location = GameLocation(
        max_room_range=max_rooms,
        room_min_size= room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        max_enemies_per_room=max_enemies_per_room,
        max_items_per_room=max_items_per_room,
        engine=engine
    )
    #engine.player.parent = engine.game_map
    
    engine.game_location.generate_floor()
    engine.update_fov()
    engine.message_log.add_message(
        "Hello and welcome, adventurer, to yet another dungeon!", color.welcome_text
    )
    return engine

def load_game(filename: str) -> Engine:
    """ Load an Engine instance from a file. """
    with open(f'data/user_data/{filename}', 'rb') as f:
        engine = pickle.loads(lzma.decompress(f.read()))
    assert isinstance(engine, Engine)
    engine.event_handler = input_handler.MainGameEventHandler(engine)
    return engine

class MainMenu(input_handler.EventHandler):
    """Handle the main menu rendering and input."""
    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        self.engine.wait = False
        self.selected_index = 0
        if glob.glob("data\\user_data\\*.sav"):
            self.selected_index = 1

    def on_render(self, console: tcod.console.Console) -> None:
        if background_image:
            console.draw_semigraphics(background_image, 0, 0)
        
        console.print(
            console.width // 2,
            console.height // 4,
            '[PLACEHOLDER]',
            fg=color.menu_title,
            alignment=libtcodpy.CENTER
        )
        console.print(
            console.width // 2,
            console.height - 2,
            'By Quentin Balestri',
            fg=color.menu_title,
            alignment=libtcodpy.CENTER
        )
        
        self.options = ['New game', 'Continue last game', 'Load Game', 'Settings', 'Quit']
        selection_console = tcod.console.Console(max(len(op) for op in self.options)+4, len(self.options)+4)
        render_functions.draw_border(selection_console)
        render_functions.draw_border_detail(selection_console)
        render_functions.draw_inner_border_detail(selection_console)
        
        option_y = 2
        for i, text in enumerate(self.options):
            text_color = color.menu_text
            if self.selected_index == i:
                text_color = color.ui_cursor_text_color
            selection_console.print(
                selection_console.width//2,
                option_y + i,
                text,
                fg=text_color,
                alignment=libtcodpy.CENTER
            )
            
        selection_console.blit(console, dest_x=console.width//2-selection_console.width//2, dest_y=console.height//2-selection_console.height//2)
            
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[input_handler.EventHandler]:
        match event.sym:
            
            case tcod.event.KeySym.DOWN:
                self.selected_index = min(self.selected_index+1, len(self.options)-1)
            case tcod.event.KeySym.UP:
                self.selected_index = max(self.selected_index-1, 0)
            
            case tcod.event.KeySym.RETURN:
                keys = [
                    tcod.event.KeyDown(0, tcod.event.KeySym.n, 0), #New Game
                    tcod.event.KeyDown(0, tcod.event.KeySym.c, 0), #Continue Game
                    tcod.event.KeyDown(0, tcod.event.KeySym.l, 0), #Load Game
                    tcod.event.KeyDown(0, tcod.event.KeySym.s, 0), #Settings
                    tcod.event.KeyDown(0, tcod.event.KeySym.q, 0), #Quit
                ]
                self.ev_keydown(keys[self.selected_index])
            
            case tcod.event.KeySym.q | tcod.event.KeySym.ESCAPE:
                raise SystemExit()
            
            case tcod.event.KeySym.c:
                try:
                    save_files = glob.glob("data\\user_data\\*.sav")
                    if not save_files:
                        raise FileNotFoundError()
                    latest_file = max(save_files, key=os.path.getctime).replace('data\\user_data\\', '')
                    saved_engine = load_game(latest_file)
                    
                except FileNotFoundError:
                    print('No save File')
                    return
                except Exception as exc:
                    traceback.print_exc()
                self.change_handler(input_handler.MainGameEventHandler(saved_engine))
            
            case tcod.event.KeySym.l:
                self.change_handler(input_handler.LoadHandler(self.engine, self))
            
            case tcod.event.KeySym.s:
                self.change_handler(input_handler.SettingsMenuHandler(self.engine, True))
            
            case tcod.event.KeySym.n:
                print('New Game')
                self.change_handler(CharacterCreatorHandler(self.engine))
                
            case tcod.event.KeySym.d if SETTINGS['dev_mode']:
                from sprite_data import dev_player
                self.change_handler(input_handler.MainGameEventHandler(new_game(dev_player)))
 
 
               
class CharacterCreatorHandler(input_handler.EventHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.sub_menus: list[SubCharacterCreatorHandler] = [
            OriginHandler(engine, self, 'Origin'),
            RaceHandler(engine, self, 'Race'),
            JobHandler(engine, self, 'Class'),
            AttributesHandler(engine, self, 'Attributes'),
            SubCharacterCreatorHandler(engine, self, 'Skills'),
            AppearanceHandler(engine, self, 'Appearance'),
        ]
        self.selected_menu = 0
        self.engine.wait = False
        self.change_handler(self.sub_menus[self.selected_menu])
        self.player_info = []
        
    def on_render(self, console: tcod.console.Console) -> None:
        if isinstance(self.engine.event_handler, CharacterCreatorHandler):
            self.change_handler(self.sub_menus[self.selected_menu])
        header_console = tcod.console.Console(width=sum(len(_.title)+3 for _ in self.sub_menus)+1, height=5)
        header_console.draw_frame(0, 0, width=header_console.width, height=header_console.height, fg=color.ui_color)
        
        title_x = 2
        for i, menu in enumerate(self.sub_menus):
            if i != 0:
                header_console.print_box(x=title_x-3, y=2, width=3, height=1, string='───', fg=color.ui_color)
                header_console.print_box(x=title_x-2, y=0, width=1, height=5, string='┬\n│\n╪\n│\n┴', fg=color.ui_color)
            elif i != len(self.sub_menus)-1:
                header_console.print_box(x=title_x-2, y=2, width=2, height=1, string='╞─', fg=color.ui_color)
                
            if i == len(self.sub_menus)-1:
                header_console.print_box(x=header_console.width-2, y=2, width=2, height=1, string='─╡', fg=color.ui_color)
            
            color_text = color.ui_text_color
            if i == self.selected_menu:
                color_text = color.ui_cursor_text_color
            header_console.print(x=title_x, y=2, string=menu.title, fg=color_text)
            
            title_x += len(menu.title)+3
            
        header_console.blit(console, dest_x=console.width//2-header_console.width//2, dest_y=1)
        
        info_console = tcod.console.Console(20, 40)
        
        info_console.draw_frame(0, 0, width=info_console.width, height=info_console.height, fg=color.ui_color)
        render_functions.draw_border_detail(info_console)
        render_functions.draw_inner_border_detail(info_console)
        
        #info_console.print(x=info_console.width//2, y=2, string=self.sub_menus[5].answers[0], fg=self.sub_menus[5].answers[1])
        tileset = tcod.tileset.load_tilesheet(
            SETTINGS['tileset_file'], 16, 16, tcod.tileset.CHARMAP_CP437
        )
        tile = tileset.get_tile(ord(self.sub_menus[5].answers[0]))[:, :, 3:]
        new_tile = np.zeros((10, 10, 3), dtype=np.uint8)
        for i, row in enumerate(new_tile):
            for j, col in enumerate(row):
                for k, a in enumerate(col):
                    if tile[i, j] == 255:
                        new_tile[i, j, k] = self.sub_menus[5].answers[1][k]
                    else:
                        new_tile[i, j, k] = 0
        
        
        img = tcod.image.Image.from_array(new_tile)
        img.blit(info_console, x=info_console.width//2, y=6, bg_blend=1, scale_x=1, scale_y=1, angle=0)
        
        info_console.print(x=0, y=10, string=f'╠{"".join(["─"]*(info_console.width-2))}╣')
        
        y_offset = 12
        name = self.sub_menus[0].answers[0]
        display_name = name
        if display_name is None:
            display_name = ''
        info_console.print(x=2, y=y_offset, string=f'Name: {display_name}', fg=color.ui_text_color)
        gender = self.sub_menus[0].answers[1]
        display_gender = gender
        if display_gender is None:
            display_gender = ''
        info_console.print(x=2, y=y_offset+1, string=f'Gender: {display_gender.capitalize()}', fg=color.ui_text_color)
        age = self.sub_menus[0].answers[2]
        display_age = age
        if display_age is None:
            display_age = ''
        info_console.print(x=2, y=y_offset+2, string=f'Age: {display_age}', fg=color.ui_text_color)
        
        race: BaseRace = self.sub_menus[1].answer
        display_race = race
        if display_race is None:
            display_race = ''
        else:
            display_race = race.name
        info_console.print(x=2, y=y_offset+4, string=f'Race: {display_race}', fg=color.ui_text_color)
        job: BaseJob = self.sub_menus[2].answer
        display_job = job
        if display_job is None:
            display_job = ''
        else:
            display_job = job.name
        info_console.print(x=2, y=y_offset+5, string=f'Class: {display_job}', fg=color.ui_text_color)
        
        info_console.print(x=2, y=y_offset+7, string=f'Attributes:', fg=color.ui_text_color)
        for i, attr in enumerate(self.sub_menus[3].answers):
            info_console.print(x=3, y=y_offset+9+i, string=f'{self.sub_menus[3].menu_items[i]}: {attr}', fg=color.ui_text_color)
        
        info_console.print(x=2, y=y_offset+17, string=f'Skills:', fg=color.ui_text_color)
        
        info_console.blit(console, dest_x=console.width-info_console.width-2, dest_y=console.height-info_console.height-2)
        
        self.player_info = [name, gender, age, race, job, dict(zip(self.sub_menus[3].menu_items, self.sub_menus[3].answers))]
        
    def create_player(self) -> Actor:
        CON = self.player_info[5]['CON']
        STR = self.player_info[5]['STR']
        END = self.player_info[5]['END']
        DEX = self.player_info[5]['DEX']
        FOC = self.player_info[5]['FOC']
        INT = self.player_info[5]['INT']
        
        from entity import Character
        from sprite import Actor
        from ai import HostileEnemy
        
        player = Actor(
            Character(
                name=self.player_info[0],
                corpse_value=0,
                race=self.player_info[3],
                gender=self.player_info[1],
                job=self.player_info[4],
                base_CON=CON,
                base_STR=STR,
                base_END=END,
                base_DEX=DEX,
                base_FOC=FOC,
                base_INT=INT,
                tags=set('player'),
                dominant_hand=self.sub_menus[0].answers[3],
                age=self.sub_menus[0].answers[2]
            ),
           char= self.sub_menus[5].answers[0],
           color=self.sub_menus[5].answers[1],
           ai_cls=HostileEnemy
        )
        
        return player
            

class SubCharacterCreatorHandler(input_handler.EventHandler):
    def __init__(self, engine, parent: CharacterCreatorHandler, title: str):
        super().__init__(engine)
        self.title = title
        self.parent = parent
        self.engine.wait = False
        
        self.selected_index = 0
        self.menu_items = []
        self.selected_item = None
        
        self.answer = None
        self.answers = None
        
        self.start_new_game = False
    
    def popup_result(self, result: bool):
        self.start_new_game = result
        
    def on_render(self, console: tcod.console.Console) -> None:
        if self.start_new_game:
            print('Start Game')
            self.change_handler(input_handler.MainGameEventHandler(new_game(self.parent.create_player())))
            return
        
        self.parent.on_render(console)
        
        text_color = color.ui_text_color
        if self.selected_index == len(self.menu_items):
            text_color = color.ui_cursor_text_color
        
        start_game_console = tcod.console.Console(len('Start Game')+4, 5)
        start_game_console.draw_frame(0, 0, start_game_console.width, start_game_console.height)
        render_functions.draw_border_detail(start_game_console)
        render_functions.draw_inner_border_detail(start_game_console)
        
        start_game_console.print(x=2, y=2, string='Start Game', fg=text_color)
        
        if all(self.parent.player_info) and self.parent.sub_menus[3].points_remaining == 0:
            start_game_console.blit(console, dest_x=console.width//2-start_game_console.width//2, dest_y=console.height-7)

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.ESCAPE:
                self.change_handler(MainMenu(self.engine))
            
            case tcod.event.KeySym(sym) if sym in range(49, 49+len(self.parent.sub_menus)):
                i = sym - 49
                self.parent.selected_menu = i
                self.change_handler(self.parent.sub_menus[self.parent.selected_menu])
                
            case tcod.event.KeySym.DOWN | tcod.event.KeySym.s:
                if not all(self.parent.player_info):
                    self.selected_index = min(self.selected_index+1, len(self.menu_items)-1)
                else:
                    self.selected_index = min(self.selected_index+1, len(self.menu_items))

            case tcod.event.KeySym.UP | tcod.event.KeySym.w:
                self.selected_index = max(self.selected_index-1, 0)
                
class OriginHandler(SubCharacterCreatorHandler):
    def __init__(self, engine, parent: CharacterCreatorHandler, title: str):
        super().__init__(engine, parent, title)
        self.menu_items = ['Name: ', 'Gender: ', 'Age: ', 'Dominant Hand: ']
        self.answers = [None,]*len(self.menu_items)
        self.answers[1] = 'male'
        self.answers[3] = 'right'
        
    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)
        
        console.print(x=4, y=8, string='Input Info:', fg=color.ui_text_color)
        item_y = 11
        for i, item in enumerate(self.menu_items):
            text_color = color.ui_text_color
            if i == self.selected_index:
                text_color = color.ui_cursor_text_color
            
            field_text = self.answers[i]
            if field_text is None:
                field_text = ''
            elif i == 1 or i == 3:
                field_text = str(field_text).capitalize()

            console.print(x=6, y=item_y, string=f'{"".join([" "*len(item)])}{str(field_text)}', fg=color.ui_text_color)
            console.print(x=6, y=item_y, string=f'{item}', fg=text_color)
            item_y +=2
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        male_female_other = {'male': 'female', 'female': 'other', 'other': 'male'}
        hand_dom = {'right': 'left', 'left': 'right'}
        match event.sym:
            case tcod.event.KeySym.RETURN if self.selected_index == len(self.menu_items):
                self.change_handler(input_handler.YNPopUp(self.engine, self))
                return
            
            case tcod.event.KeySym.RETURN:
                if self.selected_index == 1:
                    self.answers[1] = male_female_other[self.answers[1]]
                elif self.selected_index == 3:
                    self.answers[3] = hand_dom[self.answers[3]]
                else:
                    def_text = self.answers[self.selected_index]
                    if def_text is None:
                        def_text = ''
                    self.change_handler(input_handler.TextInputHandler(self.engine, x=len(self.menu_items[self.selected_index])+6, y=self.selected_index*2+11, parent=self, default_text=def_text))
                    
        super().ev_keydown(event)
        
    def return_text(self, text):
        self.answers[self.selected_index] = tryeval(text)
      
class RaceHandler(SubCharacterCreatorHandler):
    def __init__(self, engine, parent: CharacterCreatorHandler, title: str):
        super().__init__(engine, parent, title)
        self.menu_items = RACES
        self.answer = None
    
    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)
        
        console.print(x=4, y=8, string='Select Race:', fg=color.ui_text_color)
        race_y = 11
        for i, item in enumerate(self.menu_items):
            text_color = color.ui_text_color
            if i == self.selected_index:
                text_color = color.ui_cursor_text_color
            elif item == self.answer:
                text_color = color.ui_selected_text_color
            
            console.print(x=6, y=race_y, string=item.name, fg=text_color)
            
            race_y+=2
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.RETURN if self.selected_index == len(self.menu_items):
                self.change_handler(input_handler.YNPopUp(self.engine, self))
                return
            
            case tcod.event.KeySym.RETURN:
                self.answer = self.menu_items[self.selected_index]
                
        super().ev_keydown(event)
        
class JobHandler(SubCharacterCreatorHandler):
    def __init__(self, engine, parent: CharacterCreatorHandler, title: str):
        super().__init__(engine, parent, title)
        self.menu_items = JOBS
        self.answer = None
    
    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)
        
        console.print(x=4, y=8, string='Select Class:', fg=color.ui_text_color)
        race_y = 11
        for i, item in enumerate(self.menu_items):
            text_color = color.ui_text_color
            if i == self.selected_index:
                text_color = color.ui_cursor_text_color
            elif item == self.answer:
                text_color = color.ui_selected_text_color
            
            console.print(x=6, y=race_y, string=item.name, fg=text_color)
            
            race_y+=2
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.RETURN if self.selected_index == len(self.menu_items):
                self.change_handler(input_handler.YNPopUp(self.engine, self))
                return
            
            case tcod.event.KeySym.RETURN:
                self.answer = self.menu_items[self.selected_index]
                
        super().ev_keydown(event)
        
class AttributesHandler(SubCharacterCreatorHandler):
    def __init__(self, engine, parent: CharacterCreatorHandler, title: str):
        super().__init__(engine, parent, title)
        self.attribute_names = {'CON': 'Constitution', 'STR': 'Strength', 'END': 'Endurance', 'DEX': 'Dexterity', 'FOC': 'Focus', 'INT': 'Intelligence'}
        self.menu_items = list(self.attribute_names.keys())
        self.answers = [10,]*len(self.menu_items)
        self.selected_attr = None
        
        self.stat_max = 20
        self.stat_min = 8
        
        self.total_points = 75
        self.points_remaining = self.total_points-sum(self.answers)
        
    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)
        
        console.print(x=4, y=8, string='Select Attributes:', fg=color.ui_text_color)
        self.points_remaining = self.total_points-sum(self.answers)
        console.print(x=30, y=8, string=f'Points Remaining: {self.points_remaining}', fg=color.ui_text_color)
        attr_y = 11
        for i, item in enumerate(self.menu_items):
            text_color = color.ui_text_color
            text2_color = color.ui_text_color
            if item == self.selected_attr:
                text_color = color.ui_selected_text_color
                text2_color = color.ui_cursor_text_color
            elif i == self.selected_index:
                text_color = color.ui_cursor_text_color
            
            
            console.print(x=6, y=attr_y, string=f'{self.attribute_names[item]}: ', fg=text_color)
            field_text = str(self.answers[i])
            if field_text is None:
                field_text = ''
            console.print(x=6+len(self.attribute_names[item])+2, y=attr_y, string=str(field_text), fg=text2_color)
            
            attr_y+=2
            
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.RETURN if self.selected_index == len(self.menu_items) and not self.selected_attr:
                self.change_handler(input_handler.YNPopUp(self.engine, self))
                return
            
            case tcod.event.KeySym.RETURN if not self.selected_attr:
                self.selected_attr = self.menu_items[self.selected_index]
                self.prev_val = self.answers[self.selected_index]
            
            case tcod.event.KeySym.UP | tcod.event.KeySym.w if self.selected_attr:
                if self.total_points-sum(self.answers) <= 0:
                    return
                self.answers[self.selected_index] = min(self.answers[self.selected_index]+1, self.stat_max)
            case tcod.event.KeySym.DOWN | tcod.event.KeySym.s if self.selected_attr:
                self.answers[self.selected_index] = max(self.answers[self.selected_index]-1, self.stat_min)
            case tcod.event.KeySym.HOME if self.selected_attr:
                self.answers[self.selected_index] = self.stat_min
            case tcod.event.KeySym.END if self.selected_attr:
                self.answers[self.selected_index] = min(self.answers[self.selected_index]+self.points_remaining, self.stat_max)
            case tcod.event.KeySym.RETURN if self.selected_attr:
                self.selected_attr = None
            case tcod.event.KeySym.ESCAPE if self.selected_attr:
                self.answers[self.selected_index] = self.prev_val
                self.selected_attr = None
        
        if not self.selected_attr:
            super().ev_keydown(event)
            
class AppearanceHandler(SubCharacterCreatorHandler):
    def __init__(self, engine, parent: CharacterCreatorHandler, title: str):
        super().__init__(engine, parent, title)
        self.menu_items = ['Display Char: ', 'Char Color: ']
        self.answers = [None,]*len(self.menu_items)
        self.answers[0] = '@'
        self.answers[1] = (255, 255, 255)
        
    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)
        
        console.print(x=4, y=8, string='Input Appearance:', fg=color.ui_text_color)
        item_y = 11
        for i, item in enumerate(self.menu_items):
            text_color = color.ui_text_color
            if i == self.selected_index:
                text_color = color.ui_cursor_text_color
            
            field_text = self.answers[i]
            if field_text is None:
                field_text = ''
            elif i == 1:
                field_text = str(field_text).capitalize()

            console.print(x=6, y=item_y, string=f'{"".join([" "*len(item)])}{str(field_text)}', fg=color.ui_text_color)
            console.print(x=6, y=item_y, string=f'{item}', fg=text_color)
            item_y +=2
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        chars = {'@': '☺', '☺': '☻', '☻': '@'}
        match event.sym:
            case tcod.event.KeySym.RETURN if self.selected_index == len(self.menu_items):
                self.change_handler(input_handler.YNPopUp(self.engine, self))
                return
            
            case tcod.event.KeySym.RETURN:
                if self.selected_index == 0:
                    self.answers[0] = chars[self.answers[0]]
                else:
                    self.engine.event_handler = input_handler.TextInputHandler(self.engine, x=len(self.menu_items[self.selected_index])+6, y=self.selected_index*2+11, parent=self)
                    
        super().ev_keydown(event)
        
    def return_text(self, text):
        text = tryeval(text)
        if self.selected_index == 1 and not isinstance(text, tuple) and len(text) != 3:
            print(text, type(text))
            return
        self.answers[self.selected_index] = text