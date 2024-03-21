from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar
from main import logger

import tcod
from tcod.event import KeyDown

import actions, exceptions

if TYPE_CHECKING:
    from engine import Engine
    from sprite import Actor
    
T = TypeVar('T')
def all_subclasses(cls : T) -> set[T]:
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])

class BaseEventHandler(tcod.event.EventDispatch[actions.Action]):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
    
    def handle_event(self, event: tcod.event.Event) -> None:
        state = self.dispatch(event)
        assert not isinstance(state, actions.Action), f'{self!r} can not handle actions.'
        
    def ev_quit(self, event: tcod.event.Quit) -> None:
        raise SystemExit()
    
    def ev_keydown(self, event: KeyDown) -> actions.Action | None:
        match event.sym:
            case tcod.event.KeySym.s if (event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT) & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL)):
                #Take screenshot
                pass
    
    def change_handler(self, new_handler: BaseEventHandler):
        self.engine.event_handler = new_handler
        
    @property
    def is_active_handler(self) -> bool:
        return self == self.engine.event_handler

class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        self.actor_queue: list[Actor] = []
        
    def handle_event(self, event: tcod.event.Event, scope: str = 'local') -> None:
        # Update actor queue
        
        # Determine actors and sprites in scope
        match scope:
            case 'local':
                actors = self.engine.game_map.actors
                sprites = self.engine.game_map.sprites
            case 'global':
                actors = self.engine.game_world.actors
                sprites = self.engine.game_world.sprites
            case 'player':
                actors = {self.engine.player}
            case 'local_not_player':
                actors = self.engine.game_map.actors - {self.engine.player}
                sprites = self.engine.game_map.sprites - {self.engine.player}
            case 'global_not_player':
                actors = self.engine.game_world.actors - {self.engine.player}
                sprites = self.engine.game_world.sprites - {self.engine.player}
            
            case _:
                logger.warning(f'Scope: {scope} not recognized. Defaulting to scope: local.')
                actors = self.engine.game_map.actors
                sprites = self.engine.game_map.sprites

        
        # Add/remove actors from queue to match scope
        self.actor_queue.extend(set(actors).difference(self.actor_queue))
        self.actor_queue = [i for i in self.actor_queue if i in actors]
        
        current_actor = self.actor_queue[0]
        
        # If player, process input and handle actions
        if current_actor == self.engine.player:
            end_turn = self.handle_actions(self.dispatch(event))
        # If not player, prompt ai for action
        elif current_actor.entity.ai and self.engine.ai_on:
            end_turn = current_actor.entity.ai.perform()
            
        
        # End turn if actor can no longer take any actions or took a wait action
        if current_actor.entity.sp <= 0 or end_turn or all([current_actor.entity.sp < i.cost for i in all_subclasses(actions.Action) if i.cost > 0]):
            # Move actor to end of queue
            self.actor_queue.append(self.actor_queue.pop(0))
            # Handle end of turn logic/effects
            current_actor.entity.turn_end()
            # Update all entities in scope after turn ends
            for sprite in sprites:
                sprite.entity.update()
        
        
    def handle_actions(self, action: actions.Action | None) -> bool:
        if action is None:
            return False
        try:
            return action.perform()
        except exceptions.Impossible as exc:
            # Print Impossible to message log
            return False

      