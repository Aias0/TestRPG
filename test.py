import numpy as np

t1 = np.zeros((4, 4), dtype=bool, order='F')
t2 = t1

t2[1, 1] = True

print(t1)
print()
print(t2)