import tcod

def main() -> None:
    screen_width = 80
    screen_height = 50
    tileset_file = 'assets/textures/dejavu10x10_gs_tc.png'
    
    tileset = tcod.tileset.load_tilesheet(
        tileset_file, 32, 8, tcod.tileset.CHARMAP_TCOD
    )
    
    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title='TestRPG',
        vsync=True,
    ) as context:
        root_console = tcod.Console(screen_width, screen_height, order='F')
        while True:
            root_console.print(x=1, y=1, string='@')
            
            context.present(root_console)
            
            for event in tcod.event.wait():
                if event.type == 'QUIT':
                    exit()
    