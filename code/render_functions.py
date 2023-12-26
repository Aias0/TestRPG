from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, List

import color, math

import numpy as np

if TYPE_CHECKING:
    from tcod.console import Console
    from engine import Engine
    from game_map import GameMap
    

def get_names_at_location(x: int, y: int, game_map: GameMap) -> list[str]:
    if game_map.engine.wallhacks:
        pass
    elif not game_map.in_bounds(x, y) or not game_map.visible[x, y]:
        return []
    
    names = [sprite.entity.name.capitalize() for sprite in game_map.sprites if sprite.x == x and sprite.y == y]
    
    return names

def render_names_at_mouse_location(
    console: Console, x: int, y: int, engine: Engine
) -> None:
    mouse_x, mouse_y = engine.mouse_location
    
    names_at_mouse_location = get_names_at_location(
        x=mouse_x, y=mouse_y, game_map=engine.game_map
    )
    engine.hover_range = len(names_at_mouse_location)

    extra_after = {True: '...', False: ''}
    extra_before = {True: '...', False: ''}
    if not names_at_mouse_location:
        engine.hover_depth = 0
    else:
        try:
            console.print(x=x, y=y, string=f'{extra_before[engine.hover_depth>0]}{names_at_mouse_location[engine.hover_depth]}{extra_after[len(names_at_mouse_location)-1>engine.hover_depth]}', fg=color.ui_text_color)
        except IndexError:
            engine.hover_depth = 0

resource_colors = {'hp': (color.hp_bar_filled, color.hp_bar_empty), 'mp': (color.mp_bar_filled, color.mp_bar_empty), 'sp': (color.sp_bar_filled, color.sp_bar_empty)}

def render_resource_bar(
    x: int,
    y: int,
    resource: str,
    console: Console,
    current_val: int,
    maximum_val: int,
    total_width: int,
    height: int = 1
) -> None:
    bar_width = int(float(current_val) / maximum_val * total_width)
    
    console.draw_rect(x=x, y=y, width=total_width, height=height, ch=1, bg=resource_colors[resource][1])
    
    if bar_width > 0:
        console.draw_rect(
            x=x, y=y, width=bar_width, height=height, ch=1, bg=resource_colors[resource][0]
        )
        
    console.print(
        x=x+1, y=y, string=f'{resource.upper()}: {current_val}/{maximum_val}', fg=color.bar_text
    )

def circle(console: Console, char: str, x: int, y: int, radius: int) -> List[Tuple[int, int]]:
    points: List[Tuple[int, int]]= []
    if radius == 1:
        points = [(x-1, y), (x, y-1), (x, y+1), (x+1, y)]
        for i in points:
            console.print(*i, string=char, fg=color.ui_color)
        return points
    
    # draw the circle
    for angle in range(0, 180, 5):
        xx = radius * math.sin(math.radians(angle)) + y
        yy = radius * math.cos(math.radians(angle)) + x
        console.print(x=int(round(xx)), y=int(round(yy)), string=char, fg=color.ui_color)
        console.print(x=int(round(x-xx-x)), y=int(round(yy)), string=char, fg=color.ui_color)
 
    return points


if __name__ == '__main__':
    s = circle(10, 10, 5)
    map_print = [[' ' for _ in range(16)] for _ in range(16)]

    for point in s:
        map_print[point[1]][point[0]] = '*'

    for r in map_print:
        print(' '.join(r))