import tcod
import numpy as np
import random

from colour import Color

import opensimplex

from multiprocessing.pool import Pool
from multiprocessing import freeze_support

def lerp(start, end, amt):
  return (1-amt)*start+amt*end

map_height = 50 #50
map_width = 80 #80
seed = None

if seed is None:
    seed = random.randint(0, 636413622)
gen = opensimplex.OpenSimplex(seed)

n=.45
moisture_const = .95
water_level = .1
formula = 2
frequency = 8

def opensim_noise(x, y):
    return (gen.noise2(x, y)*(1/.86591)+1)/2

def noise(tup):
    loc, val = tup
    x, y = val
    e = (1*opensim_noise(1*frequency*x, 1*frequency*y)
        + .5*opensim_noise(.5*frequency*x, .5*frequency*y)
        + .25*opensim_noise(.25*frequency*x, .25*frequency*y)
        )
    
    return loc, e/(1 + 0.5 + 0.25)

def gen_noise():
    global seed, gen, formula, n, water_level, frequency
    gen = opensimplex.OpenSimplex(seed)
    
    arr = np.zeros((map_height, map_width))
    
    calc_nums = []
    for i, row in enumerate(arr):
        for j, _ in enumerate(row):
            nx = j/map_width -.5
            ny = i/map_height -.5
            
            val = noise(((i, j), (nx, ny)))[1]
            
            nx=(2*j/map_width - 1)
            ny=(2*i/map_height - 1)
            
            dist = max(2*(1 - (1-nx**2) * (1-ny**2)), 0)
            #square = abs(nx)+abs(ny)
            #euc = min(1, (nx**2 + ny**2) / 2**.5)
            #dist = [euc, square, circ][formula]
            
            arr[i, j] = 1-lerp(val, dist, n)

            #calc_nums.append(((i, j), (nx, ny)))
            
    #with Pool() as pool:
    #    result = pool.map(noise, calc_nums)
    #
    #for loc, num in result:
    #    arr[*loc] = num
      
    return arr

def get_surround_elevation(y, x) -> list[tuple]:
    surrounding = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    
    vals = []
    for s_point in surrounding:
        point = tuple(np.add((y, x), s_point))
        if point[0] not in range(map_width) or point[1] not in range(map_height):
            continue
        xx = point[1]
        yy = point[0]
        
        nx = xx/map_width -.5
        ny = yy/map_height -.5

        val = noise(((xx, yy), (nx, ny)))[1]

        nx=(2*xx/map_width - 1)
        ny=(2*yy/map_height - 1)

        dist = max(2*(1 - (1-nx**2) * (1-ny**2)), 0)
        #square = abs(nx)+abs(ny)
        #euc = min(1, (nx**2 + ny**2) / 2**.5)
        #dist = [euc, square, circ][formula]
        
        vals.append((point, 1-lerp(val, dist, n)))
        
    return vals

def in_bounds(x, y):
    return 0 <= x < map_width and 0 <= y < map_height

def gen_rivers(arr, num_rivers = None) -> list[list[tuple]]:
    random.seed(seed)
    if num_rivers is None:
        num_rivers = random.randint(0, 3)
    
    rivers: list[list] = []
    while num_rivers > 0:
        current_point = (random.randint(0, map_height-1), random.randint(0, map_width-1))
        if (
        arr[*current_point] < water_adjust(.8) or
        (rivers and current_point in [tuple(np.add(river[0], p)) for p in [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, -1), (-1, 1), (0, 0)] for river in rivers])):
            continue
        
        rivers.append([])
        picked_points = []
        while not arr[*current_point] < water_level:
            neighbors = get_surround_elevation(*current_point)
            temp = neighbors[0]
            picked_point = False
            for neighbor in neighbors:
                if neighbor[0] not in picked_points and neighbor[1] <= temp[1]:
                    temp = neighbor
                    picked_point = True
                    
            
            # Lakes/ponds
            if not picked_point:
                temp = picked_points[-1]
                for point in picked_points:
                    p_neighbors = get_surround_elevation(*point)
                    temp2 = None
                    for p_neighbor in p_neighbors:
                        if p_neighbor[0] not in picked_points and (temp2 is None or p_neighbor[1] < temp2[1]):
                            temp2 = p_neighbor
                    if temp2 and temp2[1] < temp[1]:
                        temp = temp2
                            
            
            picked_points.append(current_point)
            rivers[-1].append(current_point)
            current_point = temp[0]

        num_rivers -= 1
        
    return rivers

def dist_formula(x2, x1, y2, y1):
    return ((x2-x1)**2+(y2-y1)**2)**.5

def gen_moisture(arr, rivers:list[list[tuple]]):
    moisture = np.zeros((map_height, map_width))
    if not rivers:
        return moisture
    
    for i, row in enumerate(arr):
        for j, elv in enumerate(row):
            if not rivers[0] or elv < water_level:
                continue
            closest_fresh_water = rivers[0][0]
            for river in rivers:
                for point in river:
                    new_dist = dist_formula(point[0], i, point[1], j)
                    old_dist = dist_formula(closest_fresh_water[0], i, closest_fresh_water[1], j)
                    if new_dist < old_dist:
                        closest_fresh_water = point
            
            moisture[i, j] = (moisture_const + (random.random()*.00625)-.003125)**dist_formula(closest_fresh_water[0], i, closest_fresh_water[1], j)
            #print([i, j],closest_fresh_water)
            
    return moisture
            
                

def water_adjust(val: float) -> float:
    return (1/.9)*(1-water_level)*(val-.1)+water_level

def get_biome(elevation, moisture) -> str:
    if elevation < water_level:
        return 'OCEAN'
    
    elif elevation < water_adjust(.2):
        return 'BEACH'
    
    elif elevation < water_adjust(.3):
        if moisture < 0.16:
            return 'SUBTROPICAL_DESERT'
        if moisture < 0.33:
            return 'GRASSLAND'
        if moisture < 0.66:
            return 'TROPICAL_SEASONAL_FOREST'
        return 'TROPICAL_RAIN_FOREST'
    
    elif elevation < water_adjust(.6):
        if moisture < 0.16:
            return 'TEMPERATE_DESERT'
        if moisture < 0.50:
            return 'GRASSLAND'
        if moisture < 0.83:
            return 'TEMPERATE_DECIDUOUS_FOREST'
        return 'TEMPERATE_RAIN_FOREST'
    
    elif elevation < water_adjust(.8):
        if moisture < 0.33:
            return 'TEMPERATE_DESERT'
        if moisture < 0.66:
            return 'SHRUBLAND'
        return 'TAIGA'
    
    #elif elevation < water_adjust(.8):
    #    return 'DESERT'
    
    else:
        if moisture < 0.1:
            return 'SCORCHED'
        if moisture < 0.2:
            return 'BARE'
        if moisture < 0.5:
            return 'TUNDRA'
        return 'SNOW'
    
def gen_map() -> tuple:
    elevation = gen_noise()
    rivers = gen_rivers(elevation)
    moisture = gen_moisture(elevation, rivers)
    
    return elevation, rivers, moisture
    

def main():
    global seed, formula, n, water_level, frequency
    step_val = .01

    mouse_location= None
    
    elevation, rivers, moisture = gen_map()
    
    
    #160,144,119
    biome_colors = {
        'OCEAN': (0, 0, 200),
        'FRESH_WATER': (0, 0, 255),
        
        'BEACH': (232, 210, 153),
        
        'SUBTROPICAL_DESERT': (233,221,199),
        'GRASSLAND': (196,212,170),
        'TROPICAL_SEASONAL_FOREST': (169,204,164),
        'TROPICAL_RAIN_FOREST': (156,187,169),
        
        'TEMPERATE_DESERT': (228,232,202),
        #'GRASSLAND': (196,212,170),
        'TEMPERATE_DECIDUOUS_FOREST': (180,201,169),
        'TEMPERATE_RAIN_FOREST': (164,196,168),
        
        #'TEMPERATE_DESERT': (228,232,202),
        'SHRUBLAND': (196,204,187),
        'TAIGA': (204,212,187),
        
        'DESERT': (190,210,175),
        
        'SCORCHED': (153,153,153),
        'BARE': (187,187,187),
        'TUNDRA': (221,221,187),
        'SNOW': (255, 255, 255)
    }

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
        console = tcod.console.Console(map_width, map_height+2, order='F')

        show_hover = False
        #context.sdl_window.maximize()

        while True:
            console.clear()

            for i, row in enumerate(elevation):
                for j, val in enumerate(row):
                    console.rgb[j, i] = ord(' '),  (0,)*3, biome_colors[get_biome(val, moisture[i, j])]
                    
            for river in rivers:
                for point in river:
                    console.rgb[*point[::-1]] = ord(' '), (0,)*3, biome_colors['FRESH_WATER']

            console.print(0, console.height-2, f'LC: {n}')

            console.print(2+len(f'LC: {n}'), console.height-2, f'WL: {water_level}')

            console.print(4+len(f'LC: {n}')+len(f'WL: {water_level}'), console.height-2, f'FR: {frequency}')
            console.print(6+len(f'LC: {n}')+len(f'WL: {water_level}')+len(f'FR: {frequency}'), console.height-2, f'P: {mouse_location}')
            if mouse_location and mouse_location[1] in range(map_height) and mouse_location[0] in range(map_width):
                console.print(console.width-1, console.height-2, f'Elv: {"%.3f" % round(elevation[mouse_location[1]][mouse_location[0]], 3)}', alignment=tcod.libtcodpy.RIGHT)
                console.print(console.width-1, console.height-1, f'Mos: {"%.3f" % round(moisture[mouse_location[1]][mouse_location[0]], 3)}', alignment=tcod.libtcodpy.RIGHT)
                console.print(0, console.height-1, f'Biome: {get_biome(elevation[mouse_location[1]][mouse_location[0]], moisture[mouse_location[1]][mouse_location[0]])}')

                if show_hover:
                    #console.rgba= ord('+'), (255,)*4, (0,)*4
                    console.print(*mouse_location, string='+', fg=(255,)*3, bg=None)
            
            context.present(console)
            


            for event in tcod.event.get():
                context.convert_event(event)

                if isinstance(event, tcod.event.KeyDown):
                    match event.sym:
                        case tcod.event.KeySym.ESCAPE:
                            exit()

                        case tcod.event.KeySym.UP:
                            elevation, rivers, moisture = gen_map()
                            n = round(min(1, n+step_val), 3)
                        case tcod.event.KeySym.DOWN:
                            elevation, rivers, moisture = gen_map()
                            n = round(max(0, n-step_val), 3)
                        case tcod.event.KeySym.LEFT:
                            water_level = round(min(1, water_level+step_val), 3)
                            rivers = gen_rivers(elevation)
                            moisture = gen_moisture(elevation, rivers)
                        case tcod.event.KeySym.RIGHT:
                            water_level = round(max(0, water_level-step_val), 3)
                            rivers = gen_rivers(elevation)
                            moisture = gen_moisture(elevation, rivers)
                        case tcod.event.KeySym.w:
                            frequency = round(min(20, frequency+.5), 3)
                            elevation, rivers, moisture = gen_map()
                        case tcod.event.KeySym.s:
                            frequency = round(max(0, frequency-.5), 3)
                            elevation, rivers, moisture = gen_map()
                        case tcod.event.KeySym.RETURN:
                            formula+=1
                            if formula > 2:
                                formula = 0
                            elevation, rivers, moisture = gen_map()
                        case tcod.event.KeySym.SPACE:
                            #print()
                            seed = random.randint(0, 636413622)
                            random.seed(seed)
                            elevation, rivers, moisture = gen_map()
                            
                        case tcod.event.KeySym.m:
                            context.sdl_window.maximize()
                            
                        case tcod.event.KeySym.e:
                            show_hover = not show_hover
                            
                        case tcod.event.KeySym.i:
                            seed = int(input("seed: "))
                            elevation, rivers, moisture = gen_map()
                        case tcod.event.KeySym.p:
                            print(seed)
                            

                if isinstance(event, tcod.event.MouseMotion):
                    mouse_location = event.tile.x, event.tile.y

                if isinstance(event, tcod.event.Quit):
                    exit()


            context.present(console)
            
if __name__=="__main__":
    freeze_support()
    main()