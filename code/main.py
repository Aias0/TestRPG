#!/usr/bin/env python3
import tcod
import traceback

from config import SETTINGS
import color
import exceptions
import input_handler
import setup_game


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
    screen_width = SETTINGS['screen_width']
    screen_height = SETTINGS['screen_height']
    
    tileset = tcod.tileset.load_tilesheet(
        tileset_file, 16, 16, tcod.tileset.CHARMAP_CP437
    )

    handler: input_handler.BaseEventHandler = setup_game.MainMenu()
    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title='TestRPG',
        vsync=True,
    ) as context:
        root_console = tcod.console.Console(screen_width, screen_height, order='F')
        try:
            while True:
                if hasattr(handler, 'engine'):
                    handler = handler.engine.event_handler
                root_console.clear()
                handler.on_render(console=root_console)
                context.present(root_console)

                try:
                    if hasattr(handler, 'engine') and handler.engine.wait:
                        for event in tcod.event.wait():
                            context.convert_event(event)
                            handler.handle_events(event)
                    else:
                        for event in tcod.event.get():
                            context.convert_event(event)
                            handler.handle_events(event)
                except Exception: # Handle exceptions in game.
                    traceback.print_exc() # Print error to stderr
                    # Then print to the message log.
                    handler: input_handler.EventHandler
                    handler.engine.message_log.add_message(traceback.format_exc(), color.error)
        except exceptions.QuitWithoutSaving:
            raise
        except SystemExit: # Save and Quit
            save_game(handler, 'savegame.sav')
            raise
        except BaseException: # Save on any other unexpected exception.
            save_game(handler, 'savegame.sav')
            raise
if __name__ == '__main__':
    main()
