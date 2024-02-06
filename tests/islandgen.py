import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import tcod

import numpy as np
from numpy.typing import NDArray

from colour import Color

import random
import opensimplex

from multiprocessing import Pool, freeze_support

import time, ast

b_w_grad = [tuple(map(lambda x: int(x*255), color.rgb)) for color in Color('black').range_to(Color('white'), 100)]

def normalized_noise2(x: float, y: float) -> float:
    """ Opensimplex noise normalized to 0-1. """
    noise = (opensimplex.noise2(x, y)/.86591+1)/2
    assert 0 <= noise <= 1
    return noise

def lerp(start, end, amt):
  return (1-amt)*start+amt*end

def noise_array(shape: tuple, frequency: float = 1, octave_blend: list[float] = [1], redistribution: float = 1) -> NDArray:
    arr = np.zeros(shape)
    
    for i, row in enumerate(arr):
        for j, _ in enumerate(row):
            nx = frequency*(j/arr.shape[1] -.5)
            ny = frequency*(i/arr.shape[0] -.5)
            
            total = 0
            for octave in octave_blend:
                total += octave*normalized_noise2(1/octave*nx, 1/octave*ny)
            
            arr[i, j] = (total/sum(octave_blend))**redistribution
    
    #print(np.min(arr), np.max(arr), octave_blend, sep=' | ')
    return arr

def gen_elevation(noise: NDArray, lerp_const: float, redistribution: float = 1.2) -> NDArray:
    arr = np.zeros(noise.shape)
    
    for i, row in enumerate(arr):
        for j, _ in enumerate(row):
            val = noise[i, j]
            
            nx = 2*j/arr.shape[1] - 1
            ny = 2*i/arr.shape[0] - 1
            #dist = 1 - (1-nx**2) * (1-ny**2)
            dist = max(2*(1 - (1-nx**2) * (1-ny**2)), 0)
            
            arr[i, j] = max(lerp(val, 1-dist, lerp_const), 0)**redistribution
    
    #print(np.min(arr), np.max(arr), octave_blend, sep=' | ')
    return arr

def get_surround_elevation(elevation: NDArray, point: tuple):
    surrounding = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    
    vals = []
    for mod in surrounding:
        s_point = tuple(np.add(point, mod))
        if s_point[0] not in range(elevation.shape[0]) or s_point[1] not in range(elevation.shape[1]):
            continue
        
        vals.append((s_point, elevation[s_point]))
        
    return vals
        

def gen_rivers(elevation: NDArray, water_level: float, num_rivers: int | None = None) -> list[list[tuple]]:
    if num_rivers is None:
        num_rivers = random.randint(0, 3)
        
    rivers: list[list] = []
    while num_rivers > 0:
        current_point = (random.randint(0, elevation.shape[0]-1), random.randint(0, elevation.shape[1]-1))
        
        if elevation[*current_point] < water_adjust(water_level, .8) or (rivers and current_point in [tuple(np.add(river[0], p)) for p in [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, -1), (-1, 1), (0, 0)] for river in rivers]):
            continue
        
        rivers.append([])
        picked_points = []
        while not elevation[*current_point] < water_level:
            neighbors = get_surround_elevation(elevation, current_point)
            temp = neighbors[0]
            picked_point = False
            for neighbor in neighbors:
                if neighbor[0] not in picked_points and neighbor[1] <= temp[1]:
                    temp = neighbor
                    picked_point = True
            
            #print(f'lake {current_point}')
            # Lakes/ponds
            if not picked_point:
                temp = picked_points[-1]
                for point in picked_points:
                    #print(f'working on lake {point}')
                    p_neighbors = get_surround_elevation(elevation, point)
                    temp2 = None
                    for p_neighbor in p_neighbors:
                        if p_neighbor[0] not in picked_points and (temp2 is None or p_neighbor[1] < temp2[1]):
                            temp2 = p_neighbor
                    if temp2 and temp2[1] < temp[1]:
                        temp = temp2
            
            picked_points.append(current_point)
            rivers[-1].append(current_point)
            current_point = temp[0]
        
        num_rivers -=1
        
    return rivers
        
def gen_moisture(elevation: NDArray, rivers: list[list[tuple]], water_level: float, moisture_const: float = .95) -> NDArray:
    moisture = np.zeros(elevation.shape)
    if not rivers:
        for i, row in enumerate(elevation):
            for j, elv in enumerate(row):
                if elv < water_level:
                    moisture[i, j] = 1
        return moisture
    
    data = []
    for i, row in enumerate(elevation):
        for j, elv in enumerate(row):
            random_fudge = (random.random()*.00625)-.003125
            data.append([(i, j), elevation, rivers, water_level, moisture_const, random_fudge])
            
    results = Pool().starmap(moisture_at_tile, data)
    
    for result in results:
        moisture[*result[0]] = result[1]
            
    return moisture

def dist_formula(x2, x1, y2, y1):
    return ((x2-x1)**2+(y2-y1)**2)**.5
def moisture_at_tile(point, elevation, rivers, water_level, moisture_const, random_fudge) -> float:
    if elevation[*point] < water_level or any([point in river for river in rivers]):
        return (point, 1)
    closest_fresh_water = rivers[0][0]
    for river in rivers:
        #print('working on moist')
        for r_point in river:
            new_dist = dist_formula(r_point[0], point[0], r_point[1], point[1])
            old_dist = dist_formula(closest_fresh_water[0], point[0], closest_fresh_water[1], point[1])
            if new_dist < old_dist:
                closest_fresh_water = r_point
    
    
    moisture_val = (moisture_const + random_fudge)**dist_formula(closest_fresh_water[0], point[0], closest_fresh_water[1], point[1])

    return (point, moisture_val)
    
def gen_map(map_shape, frequency, octaves, lerp_const, water_level) -> tuple:
    print()
    print(f'Seed: {opensimplex.get_seed()}')
    noise_time = time.time()
    raw_noise = noise_array(map_shape, frequency, octaves)
    print(f'Noise: {time.time()-noise_time}')
    
    elevation_time = time.time()
    elevation = gen_elevation(raw_noise, lerp_const)
    print(f'Elevation: {time.time()-elevation_time}')
    
    river_time = time.time()
    rivers = gen_rivers(elevation, water_level)
    print(f'Rivers: {time.time()-river_time}')
    
    moisture_time = time.time()
    moisture = gen_moisture(elevation, rivers, water_level)
    print(f'Moisture: {time.time()-moisture_time}')
    print()
    
    return raw_noise, elevation, rivers, moisture

def water_adjust(water_level, val: float) -> float:
    return (1/.9)*(1-water_level)*(val-.1)+water_level
def get_biome(water_level, elevation, moisture) -> str:
    if elevation < water_level:
        return 'OCEAN'
    
    #elif elevation < water_adjust(water_level, .14):
    #    return 'SHALLOW_WATER'
    
    elif elevation < water_adjust(water_level, .2):
        return 'BEACH'
    
    elif elevation < water_adjust(water_level, .3):
        if moisture < 0.16:
            return 'SUBTROPICAL_DESERT'
        if moisture < 0.33:
            return 'GRASSLAND'
        if moisture < 0.66:
            return 'TROPICAL_SEASONAL_FOREST'
        return 'TROPICAL_RAIN_FOREST'
    
    elif elevation < water_adjust(water_level, .6):
        if moisture < 0.16:
            return 'TEMPERATE_DESERT'
        if moisture < 0.50:
            return 'GRASSLAND'
        if moisture < 0.83:
            return 'TEMPERATE_DECIDUOUS_FOREST'
        return 'TEMPERATE_RAIN_FOREST'
    
    elif elevation < water_adjust(water_level, .8):
        if moisture < 0.33:
            return 'TEMPERATE_DESERT'
        if moisture < 0.66:
            return 'SHRUBLAND'
        return 'TAIGA'
    
    #elif elevation < water_adjust(water_level, .8):
    #    return 'DESERT'
    
    else:
        if moisture < 0.1:
            return 'SCORCHED'
        if moisture < 0.2:
            return 'BARE'
        if moisture < 0.5:
            return 'TUNDRA'
        return 'SNOW'
biome_colors = {
    'OCEAN': (0, 0, 200),
    'FRESH_WATER': (0, 0, 255),
    'SHALLOW_WATER': (169,153,166),
    
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

def make_seed(val):
    try:
        val = ast.literal_eval(val)
    except ValueError:
        pass
    except SyntaxError:
        pass
    if val is None:
        val = random.randint(0, 636413622)
    elif isinstance(val, str):
        temp = ''
        for char in val:
            temp += str(ord(char))
        val = int(temp)
    return val

def main():
    freeze_support()
    
    seed = None
    seed = make_seed(seed)
    opensimplex.seed(seed)
    random.seed(seed)
    
    map_width = 100
    map_height = 80
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
        context.sdl_window.resizable = False
        context.sdl_window.size = int(map_width*10*1.5), int(map_height*10*1.5)
        
        console = tcod.console.Console(map_width, map_height+1, order='F')
        mouse_location = (0, 0)
        
        frequency = 8
        octaves = [1, .5, .25]
        lerp_const = .5
        
        water_level = .1
        
        background_stuff = 0
        
        input_text: str = ''
        inputting_text = False
        
        raw_noise, elevation, rivers, moisture = gen_map((map_width, map_height), frequency, octaves, lerp_const, water_level)
        while True:
            if not inputting_text and input_text:
                seed = make_seed(input_text)
                input_text = ''
                opensimplex.seed(seed)
                random.seed(seed)
                raw_noise, elevation, rivers, moisture = gen_map((map_width, map_height), frequency, octaves, lerp_const, water_level)
            console.clear()
            if background_stuff == 1: # Elevation
                for i, row in enumerate(elevation):
                    for j, val in enumerate(row):
                        console.print(i, j, ' ', bg=b_w_grad[min(int(val*100), 99)])
                console.print(0, 0, string='Elevation', fg=(255,)*3)
            elif background_stuff == 2: # Moisture
                for i, row in enumerate(moisture):
                    for j, val in enumerate(row):
                        console.print(i, j, ' ', bg=b_w_grad[min(int(val*100), 99)])
                console.print(0, 0, string='Moisture', fg=(0,)*3)
                    
            else:
                for i, row in enumerate(elevation):
                    for j, val in enumerate(row):
                        console.print(i, j, ' ', bg=biome_colors[get_biome(water_level, elevation[i, j], moisture[i, j])])

                for river in rivers:
                    for p in river:
                        console.print(*p, ' ', bg=biome_colors['FRESH_WATER'])
                        
                        
            if mouse_location[0] in range(console.height-1) and mouse_location[1] in range(console.width-1):
                console.print(x=0, y=console.height-1, string=f'Elv:{elevation[*mouse_location]}')
                console.print(x=console.width//2, y=console.height-1, string=f'Biome:{get_biome(water_level, elevation[*mouse_location], moisture[*mouse_location])}', alignment=tcod.constants.CENTER)
                console.print(x=console.width-1, y=console.height-1, string=f'Moist:{moisture[*mouse_location]}', alignment=tcod.constants.RIGHT)
            
            if inputting_text:
                console.print_box(x=0, y=0, width=len(input_text)+3, height=3, string='', fg=(0,)*3, bg=(0,)*3)
                console.draw_frame(x=0, y=0, width=len(input_text)+3, height=3, fg=(255,)*3, bg=(0,)*3)
                console.print(x=1, y=1, string=input_text, fg=(255,)*3, bg=(0,)*3)
                console.print(x=len(input_text)+1, y=1, string='_', bg=(0,)*3)

            context.present(console)
            
            for event in tcod.event.wait():
                context.convert_event(event)

                if not inputting_text and isinstance(event, tcod.event.KeyDown):
                    match event.sym:
                        case tcod.event.KeySym.ESCAPE:
                            exit()
                        
                        case tcod.event.KeySym.SPACE:
                            seed = make_seed(random.randint(0, 636413622))
                            opensimplex.seed(seed)
                            random.seed(seed)
                            raw_noise, elevation, rivers, moisture = gen_map((map_width, map_height), frequency, octaves, lerp_const, water_level)
                        case tcod.event.KeySym.i:
                            inputting_text = True
                            has_i = True
                        case tcod.event.KeySym.p:
                            print(seed)
                            
                        case tcod.event.KeySym.s:
                            frequency+=.5
                            elevation = noise_array((map_width, map_height), frequency, octaves)
                        case tcod.event.KeySym.w:
                            frequency-=.5
                            elevation = noise_array((map_width, map_height), frequency, octaves)
                            
                        case tcod.event.KeySym.UP:
                            lerp_const = min(lerp_const+.01, 1)
                            elevation = gen_elevation(raw_noise, lerp_const)
                            rivers = gen_rivers(elevation, water_level)
                            moisture = gen_moisture(elevation, rivers, water_level)
                        case tcod.event.KeySym.DOWN:
                            lerp_const = max(lerp_const-.01, 0)
                            elevation = gen_elevation(raw_noise, lerp_const)
                            rivers = gen_rivers(elevation, water_level)
                            moisture = gen_moisture(elevation, rivers, water_level)
                        
                        case tcod.event.KeySym.LEFT:
                            water_level = min(water_level+.01, 1)
                            rivers = gen_rivers(elevation, water_level)
                            moisture = gen_moisture(elevation, rivers, water_level)
                        case tcod.event.KeySym.RIGHT:
                            water_level = max(water_level-.01, 0)
                            rivers = gen_rivers(elevation, water_level)
                            moisture = gen_moisture(elevation, rivers, water_level)
                            
                        case tcod.event.KeySym.TAB:
                            background_stuff += 1
                            if background_stuff > 2:
                                background_stuff = 0
                
                elif inputting_text:
                    if isinstance(event, tcod.event.KeyDown):
                        match event.sym:
                            case tcod.event.KeySym.ESCAPE:
                                input_text = ''
                                inputting_text = False
                            case tcod.event.KeySym.RETURN:
                                inputting_text = False
                            case tcod.event.KeySym.BACKSPACE:
                                input_text = input_text[:-1]
                    
                    elif isinstance(event, tcod.event.TextInput):
                        input_text += event.text
                        
                    if has_i:
                        input_text = ''
                        has_i = False
                
                elif isinstance(event, tcod.event.MouseMotion):
                    mouse_location = event.tile.x, event.tile.y
            
if __name__ == '__main__':
    main()