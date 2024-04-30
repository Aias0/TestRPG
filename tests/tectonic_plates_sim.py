import tcod

import numpy as np
from numpy.typing import NDArray

from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt

from itertools import starmap

from colour import Color

import random
import opensimplex

seed = None

if seed is None:
    seed = random.randint(0, 636413622)
opensimplex.seed(seed)
np.random.seed(seed)

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
    print('Generating Tectonic Plates...')
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
    ridge_lines: dict[tuple[tuple, tuple], list[tuple]] = {}
    
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
            ridge_lines[temp_boundary] = tuple(map(lambda x: np.add(x, [int(_*6+1.5) for _ in np.add(*parent_vectors)]), temp_boundary))
    
    return vor, plate_boundaries, plate_vectors, boundary_parents, ridge_lines

def points_in_circle_np(radius, x0=0, y0=0, ):
    x_ = np.arange(x0 - radius - 1, x0 + radius + 1, dtype=int)
    y_ = np.arange(y0 - radius - 1, y0 + radius + 1, dtype=int)
    x, y = np.where((x_[:,np.newaxis] - x0)**2 + (y_ - y0)**2 <= radius**2)
    # x, y = np.where((np.hypot((x_-x0)[:,np.newaxis], y_-y0)<= radius)) # alternative implementation
    for x, y in zip(x_[x], y_[y]):
        yield x, y

def gen_elevation(
    shape: tuple,
    ridge_lines: dict[tuple, list[tuple]],
    water_level: float,
    frequency: float = 1,
    octave_blend: list[float] = [1],
    redistribution: float = 1,
    mountain_radius: int = 5
) -> NDArray:
    print('Generating Elevation...')
    elevation = np.zeros(shape)
    
    for i, row in enumerate(elevation):
        for j, _ in enumerate(row):
            nx = frequency*(j/elevation.shape[1] -.5)
            ny = frequency*(i/elevation.shape[0] -.5)
            
            total = 0
            for octave in octave_blend:
                total += octave*normalized_noise2(1/octave*nx, 1/octave*ny)
                
            tectonic_fudge = 0
            
            elevation[i, j] = (total/sum(octave_blend))**(redistribution + tectonic_fudge)
    
    print('Creating mountains from plate collisions...')
    
    ridge_points = sum([[
        point for point in tcod.los.bresenham(*ridge).tolist()
        if point[0] in range(len(elevation)) and point[1] in range(len(elevation[0]))] for ridge in ridge_lines.values()
    ], [])

    for rad in range(mountain_radius, 0, -1):
        points = {
            p for p in set().union(*starmap(points_in_circle_np, [(rad, *point) for point in ridge_points]))
            if p[0] in range(len(elevation)) and p[1] in range(len(elevation[0])) and elevation[p] > water_level
        }
        
        for point in points:
            elevation[point] += .2/rad
            
    print('Done\n')
    return elevation


def main():
    map_width = 150
    map_height = 100
    
    frequency = 5
    octaves = [1, .5, .25, .125]
        
    water_level = .5
    
    num_plates = 14
    show_plates = False
    
    
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
        print(f'\nSeed: {seed}')
        vor, plate_boundaries, plate_vectors, boundary_parents, ridge_lines = gen_plates((map_width, map_height), num_plates)
        elevation = gen_elevation((map_width, map_height), ridge_lines, water_level, frequency, octaves)
        #print(plate_boundaries)
        while True:
            console.clear()
            
            # Draw Noise/Water level
            for i, row in enumerate(elevation):
                for j, val in enumerate(row):
                    console.print(i, j, ' ', bg=b_w_grad[min(int(val*100), 99)])
                    if val < water_level:
                        console.print(i, j, ' ', bg=(0, 0, 255))
            
            # Tectonic plates
            if show_plates:
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
                    line_points = tcod.los.bresenham(*ridge).tolist()
                    for point in line_points:
                        console.print(*point, ' ', bg=[0, 0, 0])
                    
                    """
                    if bound_type[0] == 'C':
                        ridge_points = map(lambda x: map(int, np.add(x, [int(_*6+1.5) for _ in np.add(*boundary_parents[line][1])])), line_points)
                        for i, j in enumerate(ridge_points):
                            console.print(*j, ' ', bg=[0, 0, 0]) """
                            

                for point, vect in plate_vectors.items():
                    new_point = tuple(np.add(point, [int(_*6+1.5) for _ in vect]))
                    for _ in tcod.los.bresenham(point, new_point).tolist():
                        console.print(*_, '*', fg=(0, 255, 0))
            
            
            #GUI
            console.draw_rect(x=0, y=console.height-1, width=console.width, height=1, ch=ord(' '), bg=(0,)*3)
            console.print(x=1, y=console.height-1, string=f'Elv: {elevation[*mouse_location]}')
        
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
                            seed = random.randint(0, 636413622)
                            opensimplex.seed(seed)
                            np.random.seed(seed)
                            print(f'\nSeed: {seed}')
                            vor, plate_boundaries, plate_vectors, boundary_parents, ridge_lines = gen_plates((map_width, map_height), num_plates)
                            elevation = gen_elevation((map_width, map_height), ridge_lines, water_level, frequency, octaves)
                            
                        case tcod.event.KeySym.p:
                            voronoi_plot_2d(vor)
                            plt.scatter(vor.points[:, 0], vor.points[:, 1], c='red', marker='o')
                            plt.xlim(0, elevation.shape[1])
                            plt.ylim(elevation.shape[0], 0)
                            plt.show()
                            
                        case tcod.event.KeySym.RETURN:
                            show_plates = not show_plates
                            
                        case tcod.event.KeySym.DOWN:
                            frequency+=.5
                            print(f'Frequency: {frequency}')
                            elevation = gen_elevation((map_width, map_height), ridge_lines, water_level, frequency, octaves)
                        case tcod.event.KeySym.UP:
                            frequency-=.5
                            print(f'Frequency: {frequency}')
                            elevation = gen_elevation((map_width, map_height), ridge_lines, water_level, frequency, octaves)
                        case tcod.event.KeySym.LEFT:
                            water_level = min(water_level+.01, 1)
                            print(f'Water level: {water_level}')
                        case tcod.event.KeySym.RIGHT:
                            water_level = max(water_level-.01, 0)
                            print(f'Water level: {water_level}')
                            
                if isinstance(event_tile, tcod.event.MouseMotion):
                    mouse_location = event_tile.position.x, min(event_tile.position.y, map_height-1)
            
if __name__ == '__main__':
    main()