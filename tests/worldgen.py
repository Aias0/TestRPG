import tcod, time, keyboard
import numpy as np
import random

from colour import Color

import opensimplex

from multiprocessing.pool import Pool
from multiprocessing import freeze_support
from functools import partial

def lerp(start, end, amt):
  return (1-amt)*start+amt*end

map_height = 50 #50
map_width = 80 #80
seed = None

if seed is None:
    seed = random.randint(0, 636413622)
gen = opensimplex.OpenSimplex(seed)

n=.5
water_level = .1
formula = 2
frequency = 8

def opensim_noise(x, y):
    return (gen.noise2(x, y)*(1/.86591)+1)/2

def noise(tup):
    loc, val = tup
    x, y = val
    e = (1*opensim_noise(1*frequency*x, 1*frequency*y) +
         .5*opensim_noise(.5*frequency*x, .5*frequency*y) +
         .25*opensim_noise(.25*frequency*x, .25*frequency*y))
    
    return loc, e/(1 + 0.5 + 0.25)

def gen_noise():
    global seed, gen
    gen = opensimplex.OpenSimplex(seed)
    
    arr = np.zeros((map_height, map_width))
    
    calc_nums = []
    for i, row in enumerate(arr):
        for j, val in enumerate(row):
            nx = j/map_width -.5
            ny = i/map_height -.5
            
            arr[i, j] = noise(((i, j), (nx, ny)))[1]

            #calc_nums.append(((i, j), (nx, ny)))
            
    #with Pool() as pool:
    #    result = pool.map(noise, calc_nums)
    #
    #for loc, num in result:
    #    arr[*loc] = num
      
    return arr

def water_adjust(val: float) -> float:
    return (1/.9)*(1-water_level)*(val-.1)+water_level

def get_biome(elevation, moisture = None) -> str:
    
    if elevation < water_level:
        return 'WATER'
    elif elevation < water_adjust(.2):
        return 'BEACH'
    elif elevation < water_adjust(.3):
        return 'FOREST'
    elif elevation < water_adjust(.5):
        return 'JUNGLE'
    elif elevation < water_adjust(.7):
        return 'SAVANNAH'
    elif elevation < water_adjust(.8):
        return 'DESERT'
    else:
        return 'SNOW'

def main():
    global seed, formula, n, water_level, frequency
    step_val = .01

    mouse_location= None
    
    sample = gen_noise()
    data_map = [[0  for _ in range(map_width)] for _ in range(map_height)]
    #160,144,119
    biome_colors = {'WATER': (0, 0, 255), 'BEACH': (171, 157, 108), 'FOREST': (116,169,99), 'JUNGLE': (65,126,98), 'SAVANNAH': (164,189,125), 'DESERT': (190,210,175), 'SNOW': (255, 255, 255)}

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
        console = tcod.console.Console(map_width, map_height+1, order='F')

        context.sdl_window.maximize()

        while True:
            console.clear()

            for i, row in enumerate(sample):
                for j, val in enumerate(row):
                    nx=(2*j/map_width - 1)
                    ny=(2*i/map_height - 1)

                    circ = max(2*(1 - (1-nx**2) * (1-ny**2)), 0)
                    square = abs(nx)+abs(ny)
                    euc = min(1, (nx**2 + ny**2) / 2**.5)
                    dist = [euc, square, circ][formula]

                    temp = 1-lerp(val, dist, n)
                    data_map[i][j] = temp
                    console.rgb[j, i] = ord('█'), biome_colors[get_biome(temp)], (0,)*3

            console.print(0, console.height-1, f'Lerp Const: {n}')

            console.print(5+len(f'Lerp Const: {n}'), console.height-1, f'Water Level: {water_level}')

            console.print(10+5+len(f'Lerp Const: {n}')+len(f'Water Level: {water_level}'), console.height-1, f'Frequency: {frequency}')
            if mouse_location and mouse_location[1] in range(map_height) and mouse_location[0] in range(map_width):
                console.print(console.width-1, console.height-1, f'Elv: {round(data_map[mouse_location[1]][mouse_location[0]], 3)}', alignment=tcod.libtcodpy.RIGHT)

            context.present(console)


            for event in tcod.event.get():
                context.convert_event(event)

                if isinstance(event, tcod.event.KeyDown):
                    match event.sym:
                        case tcod.event.KeySym.ESCAPE:
                            exit()

                        case tcod.event.KeySym.UP:
                            n = round(min(1, n+step_val), 3)
                        case tcod.event.KeySym.DOWN:
                            n = round(max(0, n-step_val), 3)
                        case tcod.event.KeySym.LEFT:
                            water_level = round(min(1, water_level+step_val), 3)
                        case tcod.event.KeySym.RIGHT:
                            water_level = round(max(0, water_level-step_val), 3)
                        case tcod.event.KeySym.w:
                            sample = gen_noise()
                            frequency = round(min(20, frequency+.5), 3)
                        case tcod.event.KeySym.s:
                            sample = gen_noise()
                            frequency = round(max(0, frequency-.5), 3)
                        case tcod.event.KeySym.RETURN:
                            formula+=1
                            if formula > 2:
                                formula = 0
                        case tcod.event.KeySym.SPACE:
                            seed = random.randint(0, 636413622)
                            sample = gen_noise()

                if isinstance(event, tcod.event.MouseMotion):
                    mouse_location = event.tile.x, event.tile.y

                if isinstance(event, tcod.event.Quit):
                    exit()


            context.present(console)
            
if __name__=="__main__":
    freeze_support()
    main()