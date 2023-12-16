from __future__ import annotations
from typing import TYPE_CHECKING

import color

if TYPE_CHECKING:
    from tcod.console import Console

resource_colors = {'hp': (color.hp_bar_filled, color.hp_bar_empty), 'mp': (color.mp_bar_filled, color.mp_bar_empty), 'sp': (color.sp_bar_filled, color.sp_bar_empty)}

def render_resource_bar(
    x: int, y: int, resource: str, console: Console, current_val: int, maximum_val: int, total_width: int, height: int = 1
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