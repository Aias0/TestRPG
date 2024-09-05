import tcod

import numpy as np
from numpy.typing import NDArray

from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt

from itertools import starmap
from multiprocessing import Pool, freeze_support

from colour import Color
import time, sys, threading

import random
import opensimplex

from enum import Enum, auto

#Standard test seed = 1234
seed = 1234

if seed is None:
    seed = random.randint(0, 636413622)
opensimplex.seed(seed)
np.random.seed(seed)
random.seed(seed)

class SpinWheel:
    def __init__(self):
        self.spinner = self.spinning_cursor()
        self.is_computing = threading.Event()
        self.can_run = True
        self.progress_wheel = threading.Thread(target=self.loading)
        self.progress_wheel.start()

    def spinning_cursor(self):
        while True:
            for cursor in '|/-\\':
                yield cursor

    def loading(self):
        while self.can_run:
            if not self.is_computing.is_set():
                continue
            sys.stdout.write(next(self.spinner))
            sys.stdout.flush()
            time.sleep(0.1)
            sys.stdout.write('\b')

    def start(self):
        self.is_computing.set()

    def end(self):
        self.is_computing.clear()
        sys.stdout.write('\b')

    def kill(self):
        self.can_run = False
        self.is_computing.set()
        self.progress_wheel.join()
spin = SpinWheel()

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
            
            arr[i, j] = (total/sum(octave_blend))**redistribution
    
    #print(np.min(arr), np.max(arr), octave_blend, sep=' | ')
    return arr

def dist_formula(point1, point2):
    x1, y1, = point1
    x2, y2 = point2
    return ((x2-x1)**2+(y2-y1)**2)**.5

def boundary_type(vector1: tuple, vector1_pos: tuple, vector2: tuple, vector2_pos: tuple):
    rel_vect = np.subtract(vector2, vector1)
    rel_pos = np.subtract(vector2_pos, vector1_pos)

    
    dot_product = -np.dot(rel_pos, rel_vect)

    b_type = ''
    if dot_product > 4:
        b_type = 'C' #"Vectors point toward each other"
    elif dot_product < -4:
        b_type = 'D' #"Vectors point away from each other"
    else:
        b_type = 'T' #"Vectors are orthogonal (perpendicular)"
    
    return b_type, dot_product

def gen_plates(shape: tuple, num_plates: int) -> tuple[Voronoi, dict[tuple, tuple[str, float]], dict[tuple, tuple], dict[tuple, tuple[tuple, tuple]], dict[tuple[tuple, tuple], list[tuple]]]:
    print('Generating Tectonic Plates... ', end='')
    spin.start()
    points = np.array([[np.random.randint(0, shape[0]), np.random.randint(0, shape[1])] for _ in range(num_plates)])
    
    vor = Voronoi(points)
    
    plate_vectors: dict[tuple, tuple] = {}
    for point in vor.points:
        point = tuple(map(lambda x: int(x), point))
        vector = (np.random.random()*2-1, np.random.random()*2-1)
        plate_vectors[point] = vector
    
    center = vor.points.mean(axis=0)
    ptp_bound = vor.points.ptp(axis=0)
    
    plate_boundaries: dict[tuple[tuple, tuple], tuple[str, float]] = {}
    boundary_parents: dict[tuple, tuple[tuple, tuple]] = {}
    ridge_lines: dict[tuple[tuple, tuple], tuple[list[tuple], tuple]] = {}
    
    for pointidx, simplex in zip(vor.ridge_points, vor.ridge_vertices):
        simplex = np.asarray(simplex)
        temp_boundary = None
        if np.all(simplex >= 0):
            temp = []
            for i in vor.vertices[simplex]:
                temp.append(tuple(map(lambda x: int(x), i)))
            temp_boundary = tuple(temp)
            #print(lines[-1])
        else:
            i = simplex[simplex >= 0][0]  # finite end Voronoi vertex

            t = vor.points[pointidx[1]] - vor.points[pointidx[0]]  # tangent
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])  # normal

            midpoint = vor.points[pointidx].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            if (vor.furthest_site):
                direction = -direction
            far_point = vor.vertices[i] + direction * ptp_bound.max()

            temp_boundary = (tuple(map(lambda x: int(x), vor.vertices[i])), tuple(map(lambda x: int(x), far_point)))
        
        parent_points = tuple(vor.points[pointidx[1]]), tuple(vor.points[pointidx[0]])
        parent_vectors = plate_vectors[parent_points[0]], plate_vectors[parent_points[1]]
        
        plate_boundaries[temp_boundary] = boundary_type(parent_vectors[0], parent_points[0], parent_vectors[1], parent_points[1])
        boundary_parents[temp_boundary] = (parent_points, parent_vectors)
        
        if plate_boundaries[temp_boundary][0] == 'C':
            #ridge_lines[temp_boundary] = tuple(map(lambda x: np.add(x, [int(_*6+1.5) for _ in np.add(*parent_vectors)]), temp_boundary))
            ridge_lines[temp_boundary] = (tuple(map(lambda x: np.add(x, [int(_*6+1.5) for _ in np.add(*parent_vectors)]), temp_boundary)), tuple(int(_*6+1.5) for _ in np.add(*parent_vectors)))
    
    spin.end()
    print('\rGenerating Tectonic Plates... Complete')
    return vor, plate_boundaries, plate_vectors, boundary_parents, ridge_lines

def points_in_circle_np(radius, x0=0, y0=0):
    x_ = np.arange(x0 - radius - 1, x0 + radius + 1, dtype=int)
    y_ = np.arange(y0 - radius - 1, y0 + radius + 1, dtype=int)
    x, y = np.where((x_[:,np.newaxis] - x0)**2 + (y_ - y0)**2 <= radius**2)
    # x, y = np.where((np.hypot((x_-x0)[:,np.newaxis], y_-y0)<= radius)) # alternative implementation
    for x, y in zip(x_[x], y_[y]):
        yield x, y

def points_in_circle_v_pass(radius, x0, y0, vector):
    return tuple(points_in_circle_np(radius, x0, y0)), vector

def gen_elevation(
    shape: tuple,
    ridge_lines: dict[tuple, tuple[list[tuple], tuple]],
    plate_boundaries: dict[tuple[tuple, tuple], tuple[str, float]],
    water_level: float,
    frequency: float = 1,
    octave_blend: list[float] = [1],
    redistribution: float = 1,
    mountain_radius: int = 5
) -> NDArray:
    print('Generating base elevation... ', end='')
    spin.start()
    elevation = np.zeros(shape)
    
    for i, row in enumerate(elevation):
        for j, _ in enumerate(row):
            nx = frequency*(j/elevation.shape[1] -.5)
            ny = frequency*(i/elevation.shape[0] -.5)
            
            total = 0
            for octave in octave_blend:
                total += octave*normalized_noise2(1/octave*nx, 1/octave*ny)

            elevation[i, j] = (total/sum(octave_blend))**redistribution
    spin.end()
    print('\rGenerating base elevation... Complete')
    print('Creating mountains from plate collisions... ', end='')
    spin.start()
    
    ridge_vect_points = sum(
        [
            [[*point, *ridge[1][1]] for point in tcod.los.bresenham(*ridge[1][0]).tolist() if point[0] in range(len(elevation)) and point[1] in range(len(elevation[0]))]
            for ridge in ridge_lines.items()
        ],
        []
    )
    
    temp = {}
    for i in ridge_vect_points:
        temp[tuple(i[:2])] = tuple(i[2:])
        
    ridge_vect_points = temp
    
    #print(ridge_vect_points)
    ridge_vect_points = dict(ridge_vect_points)

    for rad in range(mountain_radius, 0, -1):
        temp = set()
        points_vect = [ #(p[0], ridge_vect_points[p[1]])
            temp.update([(j, p[1]) for j in p[0] if j[0] in range(elevation.shape[0]) and j[1] in range(elevation.shape[1]) and elevation[j] > water_level])
            for p in starmap(points_in_circle_v_pass, [(rad, *point, vector) for point, vector in ridge_vect_points.items()])
        ]
        #if p[0] in range(elevation.shape[0]) and p[1] in range(elevation.shape[1]) and elevation[p] > water_level
        points_vect = temp
        
        for point, vector in points_vect:
            #print(point, vector)
            vector_mag = abs((vector[0]**2 + vector[1]**2)**0.5)
            #print(vector_mag)
            elevation[point] += ((.15/7)*(vector_mag)**0.5 + .1)/rad
    spin.end()
    print('\rCreating mountains from plate collisions... Complete')
    print('Creating islands from plate collisions... ', end='')
    spin.start()
    
    points = {
        p for p in set().union(*starmap(points_in_circle_np, [(3, *point) for point in ridge_vect_points.keys()]))
        if p[0] in range(elevation.shape[0]) and p[1] in range(elevation.shape[1]) and elevation[p] <= water_level
    }
    
    #print(points)

    for point in random.choices(list(points), k=int(len(points)*.1)):
        elevation[point] = np.random.randint(80, 100)/100
        for p in [tuple(np.add(point, i)) for i in [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]]:
            if p[0] not in range(elevation.shape[0]) or p[1] not in range(elevation.shape[1]):
                continue
            elevation[p] = np.random.randint((water_level*100)-15, (water_level*100)+5)/100
    
    spin.end()
    print('\rCreating islands from plate collisions... Complete')
    print('Creating rift valleys from plate divergences... ', end='')
    spin.start()
    
    valley_points = sum(
        [
            [point for point in tcod.los.bresenham(*bound).tolist() if point[0] in range(len(elevation)) and point[1] in range(len(elevation[0]))]
            for bound in [b[0] for b in plate_boundaries.items() if b[1][0] == 'D']
        ],
        [],
    )
    
    for rad in range(max(mountain_radius-3, 2), 0, -1):
        points = {
            p for p in set().union(*starmap(points_in_circle_np, [(rad, *point) for point in valley_points]))
            if p[0] in range(len(elevation)) and p[1] in range(len(elevation[0])) and elevation[p] > water_level
        }
        
        for point in points:
            elevation[point] -= .1/(1+(rad-1)**2)
    
    spin.end()
    print('\rCreating rift valleys from plate divergences... Complete')
    return elevation

def water_adjust(water_level, val: float) -> float:
    return (1/.9)*(1-water_level)*(val-.1)+water_level

def gen_rivers(elevation: NDArray, water_level: float, num_rivers_range: tuple = (6, 9)) -> list[list[tuple]]:
    num_rivers = random.randint(*num_rivers_range)
    total_rivers = num_rivers
    print(f'Generating Rivers and Lakes [0/{total_rivers}] ... ', end='')
    spin.start()
    
    rivers: list[list[tuple]] = []
    while num_rivers > 0:
        current_point = random.randint(0, elevation.shape[0]-1), random.randint(0, elevation.shape[1]-1)
        #print(f'Point: {current_point}')
        
        if (
            (elevation[current_point] < water_adjust(water_level, .85) and (rivers and current_point not in [river[0] for river in rivers if river])) or
            [p for p in points_in_circle_np(2, *current_point) if p[0] in range(elevation.shape[0]) and (p[1] in range(elevation.shape[1]) and elevation[p] < water_level and (rivers and [river for river in rivers if p not in river]))]
        ):
            continue
        
        rivers.append([])
        

        while not elevation[*current_point] < water_level:
            surrounding_points = {
                tuple(np.add(current_point, p)): elevation[*np.add(current_point, p)] for p in [(1, 0), (0, 1), (-1, 0), (0, -1)]
                if (np.add(current_point, p)[0] in range(elevation.shape[0]) and np.add(current_point, p)[1] in range(elevation.shape[1]))
            }
            
            next_point = min(surrounding_points, key=surrounding_points.get)
            
            rounds = 0
            if elevation[*next_point] > elevation[*current_point]:
                # Lake
                #print('Generating a lake...')
                test_points = [current_point]
                while True:
                    rounds+=1
                    #print(f'Round: {rounds}')

                    test_surrounding_points = {}
                    for point in test_points:
                        temp = {
                            tuple(np.add(point, p)): elevation[*np.add(point, p)] for p in [(1, 0), (0, 1), (-1, 0), (0, -1)]
                            if (np.add(point, p)[0] in range(elevation.shape[0]) and np.add(point, p)[1] in range(elevation.shape[1]) and tuple(np.add(point, p)) not in rivers[-1] and tuple(np.add(point, p)) not in test_points)
                        }
                        test_surrounding_points.update(temp)
                    
                    # Shouldn't happen
                    if not test_surrounding_points:
                        print(test_points, test_surrounding_points)
                        exit()
                    
                    potential_next_point = min(test_surrounding_points, key=test_surrounding_points.get)
                    
                    if elevation[potential_next_point] < elevation[current_point]:
                        rivers[-1].extend(test_points[1:])
                        next_point = potential_next_point
                        break
                    
                    test_points.append(potential_next_point)
                        
            rivers[-1].append(next_point)
            current_point = next_point
            #print(rivers[-1][0], current_point)
            
        num_rivers -= 1
        print(f'\rGenerating Rivers and Lakes [{len(rivers)}/{total_rivers}] ... ', end='')
    
    # Cleaning up empty rivers
    rivers = [river for river in rivers if river]
    
    spin.end()
    print(f'\rGenerating Rivers and Lakes [{len(rivers)}/{total_rivers}] ... Complete')
    # print([i[0] for i in rivers])
    return rivers

def gen_moisture(elevation: NDArray, rivers: list[list[tuple]], water_level: float, moisture_const: float = .95) -> NDArray:
    print('Generating Moisture... ', end='')
    spin.start()
    moisture = np.zeros(elevation.shape)
    if not rivers:
        return moisture
    
    data = []
    for i, row in enumerate(elevation):
        for j, elv in enumerate(row):
            random_fudge = (random.random()*.00625)-.003125
            data.append([(i, j), elevation, rivers, water_level, moisture_const, random_fudge])
            
    results = Pool().starmap(moisture_at_cell, data)
    
    for result in results:
        moisture[*result[0]] = result[1]
    
    spin.end()
    print('\rGenerating Moisture... Complete')
    return moisture
    
def moisture_at_cell(point, elevation, rivers, water_level, moisture_const, random_fudge) -> float:
    if elevation[*point] < water_level or any([point in river for river in rivers]):
        return (point, 1)
    closest_fresh_water = rivers[0][0]
    for river in rivers:
        #print('working on moist')
        for r_point in river:
            new_dist = dist_formula(r_point, point)
            old_dist = dist_formula(closest_fresh_water, point)
            if new_dist < old_dist:
                closest_fresh_water = r_point
    
    
    moisture_val = (moisture_const + random_fudge)**dist_formula(closest_fresh_water, point)

    return (point, moisture_val)

def gen_biome(elevation: NDArray, rivers: list[list[tuple]], moisture: NDArray, water_level: float) -> NDArray:
    print('Generating Biomes... ', end='')
    spin.start()
    biomes = np.full(elevation.shape, BiomeTypes.OCEAN, dtype=BiomeTypes)
    
    for i, row in enumerate(elevation):
        for j, cell in enumerate(row):
            if any([(i, j) in river for river in rivers]):
                biomes[i, j] = BiomeTypes.FRESH_WATER
            
            elif cell < water_level:
                continue
            elif cell < water_adjust(water_level, .12):
                biomes[i, j] =  BiomeTypes.SHALLOW_WATER

            elif cell < water_adjust(water_level, .2):
                biomes[i, j] = BiomeTypes.BEACH

            elif cell < water_adjust(water_level, .3):
                if moisture[i, j] < 0.16:
                    biomes[i, j] = BiomeTypes.SUBTROPICAL_DESERT
                elif moisture[i, j] < 0.33:
                    biomes[i, j] = BiomeTypes.GRASSLAND
                elif moisture[i, j] < 0.66:
                    biomes[i, j] = BiomeTypes.TROPICAL_SEASONAL_FOREST
                else:
                    biomes[i, j] = BiomeTypes.TROPICAL_RAIN_FOREST

            elif cell < water_adjust(water_level, .6):
                if moisture[i, j] < 0.16:
                    biomes[i, j] = BiomeTypes.TEMPERATE_DESERT
                elif moisture[i, j] < 0.50:
                    biomes[i, j] = BiomeTypes.GRASSLAND
                elif moisture[i, j] < 0.83:
                    biomes[i, j] = BiomeTypes.TEMPERATE_DECIDUOUS_FOREST
                else:
                    biomes[i, j] = BiomeTypes.TEMPERATE_RAIN_FOREST

            elif cell < water_adjust(water_level, .8):
                if moisture[i, j] < 0.33:
                    biomes[i, j] = BiomeTypes.TEMPERATE_DESERT
                elif moisture[i, j] < 0.66:
                    biomes[i, j] = BiomeTypes.SHRUBLAND
                else:
                    biomes[i, j] = BiomeTypes.TAIGA
                
            else:
                if moisture[i, j] < 0.1:
                    biomes[i, j] = BiomeTypes.SCORCHED
                elif moisture[i, j] < 0.2:
                    biomes[i, j] = BiomeTypes.BARE
                elif moisture[i, j] < 0.5:
                    biomes[i, j] = BiomeTypes.TUNDRA
                else:
                    biomes[i, j] = BiomeTypes.SNOW
                
    spin.end()
    print('\rGenerating Biomes... Complete')
    return biomes

class BiomeTypes(Enum):
    OCEAN = auto()
    FRESH_WATER = auto()
    SHALLOW_WATER = auto()
    BEACH = auto()
    
    SUBTROPICAL_DESERT = auto()
    GRASSLAND = auto()
    TROPICAL_SEASONAL_FOREST = auto()
    TROPICAL_RAIN_FOREST = auto()
    
    TEMPERATE_DESERT = auto()
    TEMPERATE_DECIDUOUS_FOREST = auto()
    TEMPERATE_RAIN_FOREST = auto()
    
    SHRUBLAND = auto()
    TAIGA = auto()
    
    DESERT = auto()
    
    SCORCHED = auto()
    BARE = auto()
    TUNDRA = auto()
    SNOW = auto()

biome_colors = {
    BiomeTypes.OCEAN: (0, 0, 200),
    BiomeTypes.FRESH_WATER: (2, 153, 184),
    BiomeTypes.SHALLOW_WATER: (0, 113, 200),

    BiomeTypes.BEACH: (232, 210, 153),

    BiomeTypes.SUBTROPICAL_DESERT: (233,221,199),
    BiomeTypes.GRASSLAND: (196,212,170),
    BiomeTypes.TROPICAL_SEASONAL_FOREST: (169,204,164),
    BiomeTypes.TROPICAL_RAIN_FOREST: (156,187,169),

    BiomeTypes.TEMPERATE_DESERT: (228,232,202),

    BiomeTypes.TEMPERATE_DECIDUOUS_FOREST: (180,201,169),
    BiomeTypes.TEMPERATE_RAIN_FOREST: (164,196,168),


    BiomeTypes.SHRUBLAND: (196,204,187),
    BiomeTypes.TAIGA: (204,212,187),

    BiomeTypes.DESERT: (190,210,175),

    BiomeTypes.SCORCHED: (153,153,153),
    BiomeTypes.BARE: (187,187,187),
    BiomeTypes.TUNDRA: (221,221,187),
    BiomeTypes.SNOW: (255, 255, 255)


}

def main():
    freeze_support()
    map_width = 150 #150
    map_height = 100 #100
    
    frequency = 5
    octaves = [1, .5, .25, .125]
        
    water_level = .45
    
    num_plates = 14
    show_info = False
    show_water = True
    show_noise = False
    
    
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
        mouse_location = (0, 0)
        console = tcod.console.Console(map_width, map_height+1, order='F')
        global seed
        global spin
        print(f'\nSeed: {seed}')
        vor, plate_boundaries, plate_vectors, boundary_parents, ridge_lines = gen_plates((map_width, map_height), num_plates)
        elevation = gen_elevation((map_width, map_height), ridge_lines, plate_boundaries, water_level, frequency, octaves)
        rivers = gen_rivers(elevation, water_level)
        moisture = gen_moisture(elevation, rivers, water_level)
        biomes = gen_biome(elevation, rivers, moisture, water_level)
        spin.kill()
        #print(plate_boundaries)
        while True:
            console.clear()
            
            # Draw Noise/Water level
            for i, row in enumerate(elevation):
                for j, val in enumerate(row):
                    if show_noise:
                        if val < water_level and show_water:
                            console.print(i, j, ' ', bg=(0, 0, 255))
                        else:
                            console.print(i, j, ' ', bg=b_w_grad[min(int(val*100), 99)])
                    else:
                        console.print(i, j, ' ', bg=biome_colors[biomes[i, j]])
                    
            
            # Tectonic plates
            if show_info:
                for point in vor.points:
                    point = tuple(map(lambda x: int(x), point))
                    console.print(*point, ' ', bg=(255, 0, 0))

                for point in vor.vertices:
                    point = tuple(map(lambda x: int(x), point))
                    console.print(*point, ' ', bg=(255, 255, 0))

                for line, bound_type in plate_boundaries.items():
                    line_points = tcod.los.bresenham(*line).tolist()
                    for i, j in enumerate(line_points):
                        d = {'C': (255, 50, 0), 'D': (255, 150, 0), 'T': (255, 100, 255)}
                        console.print(*j, ' ', bg=d[bound_type[0]])
                        if (len(line_points)%2 == 0 and i == (len(line_points)-1)/2) or (len(line_points)%2 != 0 and i == (len(line_points)-1)//2) and bound_type[0] == 'C':
                            new_point = tuple(np.add(j, [int(_*6+1.5) for _ in np.add(*boundary_parents[line][1])]))
                            for _ in tcod.los.bresenham(j, new_point).tolist():
                                console.print(*_, '*', fg=(0, 255, 255))

                for ridge in ridge_lines.values():
                    line_points = tcod.los.bresenham(*ridge[0]).tolist()
                    for point in line_points:
                        console.print(*point, ' ', bg=[0, 0, 0])
                    
                    """
                    if bound_type[0] == 'C':
                        ridge_points = map(lambda x: map(int, np.add(x, [int(_*6+1.5) for _ in np.add(*boundary_parents[line][1])])), line_points)
                        for i, j in enumerate(ridge_points):
                            console.print(*j, ' ', bg=[0, 0, 0]) """
                            
                for river in rivers:
                    for i, point in enumerate(river):
                        console.print(*point, ' ', bg=(0, 0, 255))
                        if show_info and i == 0:
                            console.print(*point, ' ', bg=(57, 30, 112))
                        elif show_info:
                            console.print(*point, ' ', bg=(150, 100, 255))
                            

                for point, vect in plate_vectors.items():
                    new_point = tuple(np.add(point, [int(_*6+1.5) for _ in vect]))
                    for _ in tcod.los.bresenham(point, new_point).tolist():
                        console.print(*_, '*', fg=(0, 255, 0))
                                
            #GUI
            console.draw_rect(x=0, y=console.height-1, width=console.width, height=1, ch=ord(' '), bg=(0,)*3)
            console.print(x=1, y=console.height-1, string=f'Loc: {mouse_location} | Elv: {elevation[*mouse_location]}')
            console.print(x=console.width//2, y=console.height-1, string=f'Biome: {biomes[mouse_location].name}', alignment=tcod.constants.CENTER)
        
            for line, bound_type in plate_boundaries.items():
                if list(mouse_location) in tcod.los.bresenham(*line).tolist():
                    console.print(x=console.width-1, y=console.height-1, string=f'Boundary: {bound_type}', alignment=tcod.constants.RIGHT)
                        
            context.present(console)
            #plt.show()
            
            for event in tcod.event.get():
                event_tile = context.convert_event(event)

                if isinstance(event, tcod.event.KeyDown):
                    match event.sym:
                        case tcod.event.KeySym.ESCAPE:
                            exit()
                        
                        case tcod.event.KeySym.SPACE:
                            spin = SpinWheel()
                            seed = random.randint(0, 636413622)
                            opensimplex.seed(seed)
                            np.random.seed(seed)
                            random.seed(seed)
                            print(f'\nSeed: {seed}')
                            vor, plate_boundaries, plate_vectors, boundary_parents, ridge_lines = gen_plates((map_width, map_height), num_plates)
                            elevation = gen_elevation((map_width, map_height), ridge_lines, plate_boundaries, water_level, frequency, octaves)
                            rivers = gen_rivers(elevation, water_level)
                            moisture = gen_moisture(elevation, rivers, water_level)
                            biomes = gen_biome(elevation, rivers, moisture, water_level)
                            spin.kill()
                            
                        case tcod.event.KeySym.p:
                            voronoi_plot_2d(vor)
                            plt.scatter(vor.points[:, 0], vor.points[:, 1], c='red', marker='o')
                            plt.xlim(0, elevation.shape[1])
                            plt.ylim(elevation.shape[0], 0)
                            plt.show()
                            
                        case tcod.event.KeySym.RETURN:
                            show_info = not show_info
                            
                        case tcod.event.KeySym.BACKSPACE:
                            show_water = not show_water
                            
                        case tcod.event.KeySym.n:
                            show_noise = not show_noise
                            
                        case tcod.event.KeySym.s:
                            spin = SpinWheel()
                            seed = int(input('Seed: '))
                            opensimplex.seed(seed)
                            np.random.seed(seed)
                            random.seed(seed)
                            print(f'\nSeed: {seed}')
                            vor, plate_boundaries, plate_vectors, boundary_parents, ridge_lines = gen_plates((map_width, map_height), num_plates)
                            elevation = gen_elevation((map_width, map_height), ridge_lines, plate_boundaries, water_level, frequency, octaves)
                            rivers = gen_rivers(elevation, water_level)
                            moisture = gen_moisture(elevation, rivers, water_level)
                            biomes = gen_biome(elevation, rivers, moisture, water_level)
                            spin.kill()
                            
                        #case tcod.event.KeySym.DOWN:
                        #    frequency+=.5
                        #    print(f'Frequency: {frequency}')
                        #    elevation = gen_elevation((map_width, map_height), ridge_lines, water_level, frequency, octaves)
                        #case tcod.event.KeySym.UP:
                        #    frequency-=.5
                        #    print(f'Frequency: {frequency}')
                        #    elevation = gen_elevation((map_width, map_height), ridge_lines, water_level, frequency, octaves)
                        #case tcod.event.KeySym.LEFT:
                        #    water_level = min(water_level+.01, 1)
                        #    print(f'Water level: {water_level}')
                        #case tcod.event.KeySym.RIGHT:
                        #    water_level = max(water_level-.01, 0)
                        #    print(f'Water level: {water_level}')
                            
                if isinstance(event_tile, tcod.event.MouseMotion):
                    mouse_location = event_tile.position.x, min(event_tile.position.y, map_height-1)
            
if __name__ == '__main__':
    try:
        main()
    except BaseException as e:
        spin.kill()
        raise e