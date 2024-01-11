#!/usr/bin/env python3
import tcod
import traceback

from config import SETTINGS
import color
import exceptions
import input_handler

import os

import imageio.v3 as iio

tileset_file = SETTINGS['tileset_file']
def refresh_tileset() -> None:
    global tileset_file
    tileset_file = SETTINGS['tileset_file']


def save_game(handler: input_handler.EventHandler, filename: str) -> None:
    """ If the current event handler has an active Engine then save it. """
    if isinstance(handler, input_handler.EventHandler):
        handler.engine.save_as(filename)
        print('Game Saved')
        
def main() -> None:
    screen_width = 80
    screen_height = 50
    
    tileset = tcod.tileset.load_tilesheet(
        tileset_file, 16, 16, tcod.tileset.CHARMAP_CP437
    )
    from engine import MainMenuEngine
    # See if a reboot save exists and reload if if it does. If it doesn't go to main menu.
    if os.path.exists('data\\user_data\\TempRebootSave.sav'):
        from setup_game import load_game
        handler = load_game('TempRebootSave.sav').event_handler
        os.remove('data\\user_data\\TempRebootSave.sav')
    else:
        handler = MainMenuEngine().event_handler
    
    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title='TestRPG',
        vsync=True,
    ) as context:
        root_console = tcod.console.Console(screen_width, screen_height, order='F')
        
        context.sdl_window.fullscreen = SETTINGS['full_screen']
        context.sdl_window.maximize()
        try:
            while True:
                context.sdl_window.fullscreen = SETTINGS['full_screen']
                handler = handler.engine.event_handler
                
                root_console.clear()
                handler.on_render(console=root_console)
                context.present(root_console)

                try:
                    if False: # hasattr(handler, 'engine') and handler.engine.wait
                        for event in tcod.event.wait():
                            context.convert_event(event)
                            handler.handle_events(event)
                    else:
                        for event in tcod.event.get():
                            context.convert_event(event)
                            handler.handle_events(event)
                except exceptions.ExitToMainMenu:
                    if not isinstance(handler.engine, MainMenuEngine):
                        save_game(handler, f'exitsave{abs(hash(handler.engine)) % (10 ** 5)}.sav')
                    handler = MainMenuEngine().event_handler
                except Exception: # Handle exceptions in game.
                    traceback.print_exc() # Print error to stderr
                    # Then print to the message log.
                    handler.engine.message_log.add_message(traceback.format_exc(), color.error)
        except exceptions.QuitWithoutSaving:
            raise
        
        except SystemExit: # Save and Quit
            if not isinstance(handler.engine, MainMenuEngine):
                save_game(handler, f'exitsave{abs(hash(handler.engine)) % (10 ** 5)}.sav')
            raise
        except BaseException: # Save on any other unexpected exception.
            if not isinstance(handler.engine, MainMenuEngine):
                save_game(handler, f'savegame{abs(hash(handler.engine)) % (10 ** 5)}.sav')
            raise
if __name__ == '__main__':
    main()
