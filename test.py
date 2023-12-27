

def draw_line(start_coord: tuple[int, int], end_coord: tuple[int, int]) -> None:
    x1, y1 = start_coord
    x2, y2 = end_coord
    x, y = x1, y1
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    gradient = dy/float(dx)
    
    if gradient > 1:
        dx, dy = dy, dx
        x, y = y, x
        x1, y1 = y1, x1
        x2, y2 = y2, x2
        
    p = 2*dy - dx
    # Initialize the plotting points
    points = [(x, y)]

    for k in range(2, dx + 2):
        if p > 0:
            y = y + 1 if y < y2 else y - 1
            p = p + 2 * (dy - dx)
        else:
            p = p + 2 * dy

        x = x + 1 if x < x2 else x - 1

        points.append((x, y))