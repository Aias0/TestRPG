from __future__ import annotations
from typing import Optional, TYPE_CHECKING

import tcod, color
from tcod import libtcodpy

from actions import Action, EscapeAction, BumpAction, WaitAction

if TYPE_CHECKING:
    from engine import Engine
    
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

text_input = ''

class EventHandler(tcod.event.EventDispatch[Action]):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
    
    def handle_events(self, context: tcod.context.Context) -> None:
        for event in tcod.event.wait():
            context.convert_event(event)
            self.dispatch(event)
            
    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y
    
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()
    
    def on_render(self, console: tcod.console.Console) -> None:
        self.engine.render(console)
    
class MainGameEventHandler(EventHandler):
    def handle_events(self, context: tcod.context.Context) -> None:
        for event in tcod.event.wait():
            context.convert_event(event)
            
            action = self.dispatch(event)
                
            if action is None:
                continue
            
            action.perform()
            
            self.engine.handle_npc_turns()
            
            self.engine.update_fov() # Update the FOV before the players next action.
        
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
            action = EscapeAction(player)
            
        elif key == tcod.event.KeySym.v:
            self.engine.event_handler = HistoryViewer(self.engine)
            
        elif key == tcod.event.KeySym.BACKSLASH:
            self.engine.event_handler = DevConsole(self.engine)
            
        return action
    
class GameOverEventHandler(EventHandler):
    def handle_events(self, context: tcod.context.Context) -> None:
        for event in tcod.event.wait():
            action = self.dispatch(event)
                
            if action is None:
                continue
            
            action.perform()
            
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None
        
        key = event.sym
        
        if key == tcod.event.KeySym.ESCAPE:
            action = EscapeAction(self.engine.player)
            
        # No valid key was pressed
        return action
    
CURSOR_Y_KEYS = {
    tcod.event.KeySym.UP: -1,
    tcod.event.KeySym.DOWN: 1,
}

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
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
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
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log.
                self.cursor = 0 # Move directly to the top message.
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
        self._cursor_blink = 0
        
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
            
    def handle_events(self, context: tcod.context.Context) -> None:
        for event in tcod.event.get():
            context.convert_event(event)
            
            action = self.dispatch(event)
                
            if action is None:
                continue
            
            action.perform()
            
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
        if len(self.text_inputted) + len(event.text) > self.width-2:
            return
        self.text_inputted += event.text
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        match event.sym:
            case tcod.event.KeySym.RETURN:
                self.cursor_blink = 40
    
                self.use_input()
                
                if len(self.engine.input_log) == 0 or self.engine.input_log[0] != self.text_inputted:
                    self.engine.input_log.insert(0, self.text_inputted)
                self.engine.event_handler = MainGameEventHandler(self.engine)
            case tcod.event.KeySym.BACKSPACE:
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