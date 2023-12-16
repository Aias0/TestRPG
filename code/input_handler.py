from __future__ import annotations
from typing import Optional, TYPE_CHECKING

import tcod
import tcod.event

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

class EventHandler(tcod.event.EventDispatch[Action]):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
    
    def handle_events(self) -> None:
        raise NotImplementedError()
    
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()
    
class MainGameEventHandler(EventHandler):
    def handle_events(self) -> None:
        for event in tcod.event.wait():
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
            
        return action
    
class GameOverEventHandler(EventHandler):
    def handle_events(self) -> None:
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