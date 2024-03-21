#!/usr/bin/env python3
from __future__ import annotations
from typing import TYPE_CHECKING

import tcod
import os, win32api

import traceback
import exceptions

import logging
logger = logging.getLogger(__name__)
log_file='data\game_data\logs\myapp.log'
logging.basicConfig(filename=None, level=logging.INFO)
class MessageLogLogging(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        pass
logger.addHandler(MessageLogLogging())


if TYPE_CHECKING:
    from engine import Engine

def main() -> None:
    # Window size in tiles
    window_width = 80
    window_height = 50
    
    tileset_file = 'assets\\textures\\rexpaint_cp437_10x10.png'
    
    tileset = tcod.tileset.load_tilesheet(
        tileset_file, 16, 16, tcod.tileset.CHARMAP_CP437
    )
    
    # See if a reboot save exists and reload if it does. If it doesn't go to main menu.
    engine: Engine
    if os.path.exists('data\\user_data\\TempRebootSave.sav'):
        engine = None # Load saved engine
    else:
        engine = None # Make new Engine
    
    # Create tcod terminal
    with tcod.context.new_terminal(
        window_width,
        window_height,
        tileset=tileset,
        title='TestRPG',
        vsync=True,
        sdl_window_flags=None,
    ) as context:
        root_console = tcod.console.Console(window_width, window_height, order='F')
        
        # Resize and center window
        context.sdl_window.size = int(window_width*20), int(window_height*20)
        
        screen_width = win32api.GetSystemMetrics(0)
        screen_height = win32api.GetSystemMetrics(1)
        context.sdl_window.position = screen_width//2-context.sdl_window.size[0]//2, screen_height//2-context.sdl_window.size[1]//2
        
        # Catch all game ending exceptions
        try:
            # Main game loop
            while True:
                # Rendering
                root_console.clear()
                
                # Render new screen
                context.present(root_console)
                
                # Logic
                try:
                    for event in tcod.event.get():
                        context.convert_event(event)
                        engine.event_handler.handle_event(event)
                
                except exceptions.ExitToMainMenu:
                    # Save here
                    pass
                
                except Exception: # Handle non-fatal exceptions
                    traceback.print_exc()
        
        except exceptions.QuitWithoutSaving: # Quit
            raise
        
        except SystemExit: # Save and Quit
            # Save here
            raise
            
        except BaseException: # Save on fatal exceptions
            # Save here
            raise

if __name__ == '__main__':
    main()