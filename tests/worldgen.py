import tcod

import numpy as np
from numpy.typing import NDArray

from colour import Color

import random
import opensimplex

seed = None

if seed is None:
    seed = random.randint(0, 636413622)
opensimplex.seed(seed)

b_w_grad = [tuple(map(lambda x: int(x*255), color.rgb)) for color in Color('black').range_to(Color('white'), 100)]

def normalized_noise2(x, y):
    """ Opensimplex noise normalized to 0-1. """
    noise = (opensimplex.noise2(x, y)/.86591+1)/2
    assert 0 <= noise <= 1
    return noise


def noise_array(shape: tuple, frequency: float = 1, octave_blend: list[float] = [1], redistribution: float = 1) -> NDArray:
    arr = np.zeros(shape)
    
    for i, row in enumerate(arr):
        for j, _ in enumerate(row):
            nx = frequency*(j/arr.shape[1] -.5)
            ny = frequency*(i/arr.shape[0] -.5)
            
            total = 0
            for octave in octave_blend:
                total += octave*normalized_noise2(1/octave*nx, 1/octave*ny)
            
            arr[i, j] = total/sum(octave_blend)**redistribution
    
    #print(np.min(arr), np.max(arr), octave_blend, sep=' | ')
    return arr

def main():
    map_width = 100
    map_height = 100
    tileset = tcod.tileset.load_tilesheet(
    'assets\\textures\\rexpaint_cp437_10x10.png', 16, 16, tcod.tileset.CHARMAP_CP437
    )
    with tcod.context.new_terminal(
        map_width,
        map_height+1,
        tileset=tileset,
        title='WorldGen',
        vsync=True,
    ) as context:
        console = tcod.console.Console(map_width, map_height, order='F')
        
        frequency = 8
        octaves = [1, .5, .25]
        octaves = [1.5]
        
        water_level = 0
        
        elevation = noise_array((map_width, map_height), frequency, octaves)
        while True:
            console.clear()
            for i, row in enumerate(elevation):
                for j, val in enumerate(row):
                    console.print(i, j, ' ', bg=b_w_grad[min(int(val*100), 99)])
                    if val < water_level:
                        console.print(i, j, ' ', bg=(0, 0, 255))
                        
            context.present(console)
            
            for event in tcod.event.get():
                context.convert_event(event)

                if isinstance(event, tcod.event.KeyDown):
                    match event.sym:
                        case tcod.event.KeySym.ESCAPE:
                            exit()
                        
                        case tcod.event.KeySym.SPACE:
                            seed = random.randint(0, 636413622)
                            opensimplex.seed(seed)
                            elevation = noise_array((map_width, map_height), frequency, octaves)
                            
                        case tcod.event.KeySym.DOWN:
                            frequency+=.5
                            print(f'Frequency: {frequency}')
                            elevation = noise_array((map_width, map_height), frequency, octaves)
                        case tcod.event.KeySym.UP:
                            frequency-=.5
                            print(f'Frequency: {frequency}')
                            elevation = noise_array((map_width, map_height), frequency, octaves)
                        case tcod.event.KeySym.LEFT:
                            water_level = min(water_level+.01, 1)
                            print(f'Water level: {water_level}')
                        case tcod.event.KeySym.RIGHT:
                            water_level = max(water_level-.01, 0)
                            print(f'Water level: {water_level}')
            
if __name__ == '__main__':
    main()