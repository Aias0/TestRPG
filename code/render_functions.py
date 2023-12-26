from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, List

import color

from bitmap import BitMap
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

def circle(x: int, y: int, radius: int) -> List[Tuple[int, int]]:
    #(x-x1)**2 + (y+y1)**2 = radius
    #y=\pm\sqrt{1-\left(x-3\right)^{2}}+4
    points: List[Tuple[int, int]]= []
    
    xx = radius
    yy = 0
    
    points.append((xx+x, yy+y))
    
    if radius > 0:
        points.append((xx+x, -yy+y))
        points.append((yy+x, xx+y))
        points.append((-yy+x, xx+y))
    
    P = 1 - radius
    while xx > y:
        
        yy += 1
        
        if P <= 0:
            P = P + 2 * yy + 1
        else:
            xx -= 1
            P = P + 2 * yy - 2 * xx + 1
            
        if xx < yy:
            break
        
        points.append((xx+x, yy+y))
        points.append((-xx+x, yy+y))
        points.append((xx+x, -yy+y))
        points.append((-x+xx, -y+yy))
        
        if xx != yy:
            points.append((yy+x, xx+y))
            points.append((-yy+x, xx+y))
            points.append((yy+x, -xx+y))
            points.append((-yy+x, -xx+y))
            
    return points

s = circle(10, 10, 5)
print(s)
map_print = [[' ' for _ in range(30)] for _ in range(30)]

for point in s:
    print(point)
    map_print[point[0]][point[1]] = '*'
    
for r in map_print:
    print(r)