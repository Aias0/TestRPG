from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, List

import color, math, time

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

def draw_circle(console: Console, char: str, x: int, y: int, radius: int) -> List[Tuple[int, int]]:
    points: List[Tuple[int, int]]= []
    if radius == 1:
        points = [(x-1, y), (x, y-1), (x, y+1), (x+1, y)]
        for i in points:
            if i[1] < 42:
                console.print(*i, string=char, fg=color.ui_color)
        return points
    
    # draw the circle
    for angle in range(0, 180, 5):
        xx = radius * math.sin(math.radians(angle)) + x
        yy = radius * math.cos(math.radians(angle)) + y
        if yy < 42:
            console.print(x=int(round(xx)+.5), y=int(round(yy)+.5), string=char, fg=color.ui_color)
            console.print(x=int(round(x-(xx-x))+.5), y=int(round(yy)+.5), string=char, fg=color.ui_color)
 
    return points

def draw_line(
    console: Console, char: str, start_coord: tuple[int, int], end_coord: tuple[int, int], color: Tuple[int, int, int], print_start: bool = True, delay: float = 0
) -> List[Tuple[int, int]]:
    points = line(start_coord, end_coord, print_start)
    
    for x, y in points:
        console.print(x=x, y=y, string=char, fg=color)
        
def line(
    start_coord: tuple[int, int], end_coord: tuple[int, int], start: bool = True,
) -> None:
    x1, y1 = start_coord
    x2, y2 = end_coord
    x, y = x1, y1
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    gradient = dy/float(dx)
    
    if gradient > 1:
        dx, dy = dy, dx
        x, y = y, x
        x1, y1 = y1, x1
        x2, y2 = y2, x2
        
    p = 2*dy - dx
    # Initialize the plotting points
    points: List[Tuple[int, int]] = []
    if start:
        points.append((x, y))

    for k in range(2, dx + 2):
        if p > 0:
            y = y + 1 if y < y2 else y - 1
            p = p + 2 * (dy - dx)
        else:
            p = p + 2 * dy

        x = x + 1 if x < x2 else x - 1

        points.append((x, y))
    
    return points
    