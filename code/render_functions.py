from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, List

import color, math, time, tcod

import numpy as np

import bresenham

if TYPE_CHECKING:
    from tcod.console import Console
    from engine import Engine
    from world import GameMap
    

def get_names_at_location(x: int, y: int, game_map: GameMap) -> list[str]:
    if game_map.engine.wallhacks:
        pass
    elif not game_map.in_bounds(x, y) or not game_map.visible[x, y]:
        return []
    
    names = [sprite.entity.display_name.title() for sprite in game_map.sprites - {game_map.engine.player} if sprite.x == x and sprite.y == y]
    
    return names

def render_names_at_mouse_location(
    console: Console, x: int, y: int, engine: Engine, alignment = tcod.constants.LEFT
) -> None:
    mouse_x, mouse_y = engine.mouse_location
    
    names_at_mouse_location = get_names_at_location(
        x=mouse_x, y=mouse_y, game_map=engine.game_map
    )
    engine.hover_range = len(names_at_mouse_location)

    extra_after = ''
    extra_before = ''
    if not names_at_mouse_location:
        engine.hover_depth = 0
    else:
        try:
            names = names_at_mouse_location[engine.hover_depth]
        except IndexError:
            engine.hover_depth = 0
            names = names_at_mouse_location[engine.hover_depth]
        
        if engine.hover_depth>0:
            extra_before = '...'
            x-=3
        if len(names_at_mouse_location)-1>engine.hover_depth:
            extra_after = '...'
            
        if alignment == tcod.constants.CENTER:
            console.print(x=x-len(names)//2, y=y, string=f'{extra_before}{names}{extra_after}', fg=color.ui_text_color)
        elif alignment == tcod.constants.LEFT:
            console.print(x=x, y=y, string=f'{extra_before}{names}{extra_after}', fg=color.ui_text_color)
        elif alignment == tcod.constants.RIGHT:
            console.print(x=x-len(names), y=y, string=f'{extra_before}{names}{extra_after}', fg=color.ui_text_color)

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
        fg = fg
    
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

def draw_reticle(console: Console, x: int, y: int, fg: Tuple[int, int, int] = None) -> None:
    if fg is None:
        fg = color.ui_color
    console.print(x=x, y=y-1, string='│', fg=fg)
    console.print(x=x-1, y=y+1, string='/', fg=fg)
    console.print(x=x+1, y=y+1, string='\\', fg=fg)
    
    
def draw_border_detail(console: Console, chars: str = '╔╗╚╝', fg: tuple[int, int, int] = None) -> None:
    if fg is None:
        fg = color.ui_color
    chars = list(chars)
    console.print(x=0, y=0, string=chars[0], fg=fg)
    console.print(x=0, y=console.height-1, string=chars[2], fg=fg)
    console.print(x=console.width-1, y=0, string=chars[1], fg=fg)
    console.print(x=console.width-1, y=console.height-1, string=chars[3], fg=fg)
    
def draw_inner_border_detail(console: Console, chars: str = '╥╚╡╥╝╞╨╗╞╨╔╡', fg: tuple[int, int, int] = None) -> None:
    if fg is None:
        fg = color.ui_color
    console.print(x=console.width-2, y=0, string=chars[0], fg=fg)
    console.print(x=console.width-2, y=1, string=chars[1], fg=fg)
    console.print(x=console.width-1, y=1, string=chars[2], fg=fg)
    
    console.print(x=1, y=0, string=chars[3], fg=fg)
    console.print(x=1, y=1, string=chars[4], fg=fg)
    console.print(x=0, y=1, string=chars[5], fg=fg)
    
    console.print(x=1, y=console.height-1, string=chars[6], fg=fg)
    console.print(x=1, y=console.height-2, string=chars[7], fg=fg)
    console.print(x=0, y=console.height-2, string=chars[8], fg=fg)
    
    console.print(x=console.width-2, y=console.height-1, string=chars[9], fg=fg)
    console.print(x=console.width-2, y=console.height-2, string=chars[10], fg=fg)
    console.print(x=console.width-1, y=console.height-2, string=chars[11], fg=fg)
    
def draw_border(console: Console, fg: tuple[int, int, int] = None, chars: str = "┌─┐│ │└─┘"):
    if fg is None:
        fg = color.ui_color
    console.draw_frame(x=0, y=0, width=console.width, height=console.height, decoration=chars, fg=fg)
    
def draw_all_border(console: Console, fg: tuple[int, int, int] = None) -> None:
    if fg is None:
        fg = color.ui_color
    draw_border(console)
    draw_border_detail(console)
    draw_inner_border_detail(console)

def print_color(
    console: Console,
    x: int,
    y: int,
    string: str,
    fg: tuple[int, int, int] | None = None,
    bg: tuple[int, int, int] | None = None,
    specific_color: dict[int | str, tuple[int, int, int]] | None = None,
    bg_blend: int = tcod.constants.BKGND_SET,
    alignment: int = tcod.constants.LEFT
):
    if not specific_color:
        console.print(x, y, string, fg, bg, bg_blend, alignment)
        return
    
    specific_color = {string.index(_[0]) if isinstance(_[0], str) else _[0]: _[1] for _ in specific_color.items()}
    
    char_color = {i: fg for i in range(len(string))} | specific_color
    
    if alignment == tcod.constants.CENTER:
        for i, char in enumerate(string):
            console.print(x=x+i-len(string)//2, y=y, string=char, fg=char_color[i], bg=bg, bg_blend=bg_blend)
    elif alignment == tcod.constants.LEFT:
        for i, char in enumerate(string):
            console.print(x=x+i, y=y, string=char, fg=char_color[i], bg=bg, bg_blend=bg_blend)
    elif alignment == tcod.constants.RIGHT:
        for i, char in enumerate(string):
            console.print(x=x+i-len(string), y=y, string=char, fg=char_color[i], bg=bg, bg_blend=bg_blend)