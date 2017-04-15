from os import path
import sys
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla

@Dipla.scoped_distributable(count=4)
def bfs(grid, index, count):
    from queue import Queue
    q = Queue()
    # Start in the center of the grid
    q.put((len(grid)//2, len(grid)//2))
    seen = set()
    ans = []
    
    # Split the grid into 4 quadrants, and calculate the bounds of each
    bounds = [(0, 0), (1, 0), (0, 1), (1, 1)]
    half_grid = len(grid)//2
    min_x = bounds[index][0] * half_grid
    min_y = bounds[index][1] * half_grid
    max_x = min_x + half_grid
    max_y = min_y + half_grid

    # Standard breadth first search
    while not q.empty():
        popped = q.get()
        directions = [(1, 0), (-1, 0), (0, 1),  (0, -1)]
        for xy in directions:
          newx = popped[0] + xy[0]
          newy = popped[1] + xy[1]      
          
          if newx < min_x or newx > max_x or newy < min_y or newy > max_y:
              continue
          new = (newx, newy)
          if new in seen:
              continue
          if grid[new[1]][new[0]] == 2:
              continue
          if grid[new[1]][new[0]] == 1:
              ans.append(new)
          seen.add(new)
          q.put(new)
    return ans

grid = [
    [1, 0, 2, 2, 0, 0, 0],
    [2, 0, 2, 2, 0, 0, 1],
    [0, 0, 0, 0, 0, 0, 0],
    [2, 2, 2, 0, 0, 0, 0],
    [0, 0, 2, 0, 0, 2, 0],
    [1, 0, 2, 0, 2, 1, 0],
    [0, 0, 0, 0, 0, 0, 0]
]

# Apply a distributable function to the stream of values from
# the above source
out = Dipla.apply_distributable(bfs, [[grid]]).get()

u = []
for y in out:
    u += [(x[0], x[1]) for x in y]

for o in set(u):
   print(o)
