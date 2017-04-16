from os import path
import sys
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla

# This example finds the number of rows away from the bottom that a
# one exists in a grid. Normally this would require processing a whole
# row before the program can start on the next row, using the
# information from the previous row. This one sends the first half of a
# row as soon as it finds it so that the a worker can start on the next
# stage of processing

@Dipla.chasing_distributable(count=2, chasers=5)
def rows_since_found(row, last_calculated, index, count):
    interval = len(row)//count
    # If we are in the first row, return 1 if we found a 1 and zero
    # otherwise
    if last_calculated == None:
       if interval*index + interval >= len(row):
           return row[index*interval:]
       else:
           return row[index*interval:index*interval+interval]
    # If we're not on the first row, increase each number by 1 so that
    # in the end we'll have values for how far away from the bottom each
    # one was
    else:
        last = last_calculated
        out = []
        for i in range(len(last)):
            if last_calculated[i] == 0:
                out.append(row[i+interval*index])
            else:
                out.append(last[i] + 1)

        return out

grid = [
  [1, 0, 0, 0, 0, 0],
  [0, 1, 0, 0, 0, 0],
  [0, 0, 1, 0, 0, 0],
  [0, 0, 0, 1, 0, 0],
  [0, 0, 0, 0, 1, 0]
]

results = Dipla.apply_distributable(rows_since_found, grid)
out = Dipla.get(results)
outlist = []
for o in out:
    outlist = outlist + o
print(outlist)
