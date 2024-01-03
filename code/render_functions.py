from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, List

import color, math, time

import numpy as np

import bresenham

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

def draw_circle(console: Console, char: str, x: int, y: int, radius: int, fg: Tuple[int, int, int] | None = None) -> List[Tuple[int, int]]:
    points: List[Tuple[int, int]]= []
    if not fg:
        fg = color.ui_color
    
    if radius == 1:
        points = [(x-1, y), (x, y-1), (x, y+1), (x+1, y)]
        for i in points:
            if i[1] < 42:
                console.print(*i, string=char, fg=fg)
        return points
    
    # draw the circle
    for angle in range(0, 180, 5):
        xx = radius * math.sin(math.radians(angle)) + x
        yy = radius * math.cos(math.radians(angle)) + y
        if yy < 42:
            console.print(x=int(round(xx)+.5), y=int(round(yy)+.5), string=char, fg=fg)
            console.print(x=int(round(x-(xx-x))+.5), y=int(round(yy)+.5), string=char, fg=fg)
 
    return points

def draw_line(
    console: Console, char: str, start_coord: tuple[int, int], end_coord: tuple[int, int], color: Tuple[int, int, int], print_start: bool = True, delay: float = 0
) -> List[Tuple[int, int]]:
    points = line(start_coord, end_coord)
    
    for i, point in enumerate(points):
        if not print_start and i == 0:
            continue
        console.print(*point, string=char, fg=color)
        
def line(start_coord: tuple[int, int], end_coord: tuple[int, int]) -> None:
    return list(bresenham.bresenham(*start_coord, *end_coord))

def draw_reticle(console: Console, x: int, y: int, fg: Tuple[int, int, int] | None = None) -> None:
    if fg is None:
        fg = color.ui_color
    
    console.print(x=x, y=y-1, string='│', fg=fg)
    console.print(x=x-1, y=y+1, string='/', fg=fg)
    console.print(x=x+1, y=y+1, string='\\', fg=fg)
    