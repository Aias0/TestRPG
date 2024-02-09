import numpy as np
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt

# Generate some random points
np.random.seed(123)
points = np.random.rand(10, 2)

# Compute Voronoi diagram
vor = Voronoi(points)

# Plot the Voronoi diagram
voronoi_plot_2d(vor)
plt.scatter(points[:, 0], points[:, 1], c='red', marker='o')
plt.show()