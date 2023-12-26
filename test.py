import math

width, height = 11, 11
a, b = 5, 5
r = 2

map_ = [['.' for x in range(width)] for y in range(height)]

# draw the circle
for angle in range(0, 180, 5):
    x = r * math.sin(math.radians(angle)) + a
    y = r * math.cos(math.radians(angle)) + b
    map_[int(round(y)+.5)][int(round(x)+.5)] = '#'
    map_[int(round(y)+.5)][int(round(a-(x-a))+.5)] = '#'
    
# print the map
for line in map_:
    print(' '.join(line))