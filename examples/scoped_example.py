from os import path
import sys
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla

@Dipla.scoped_distributable(count=3)
def get_evens(input_value, index, count):
    import json
    # input value is a json representation of the provided inputs,
    # get the range and divide it by the count (number of workers) to
    # get the interval size
    interval = input_value[1] // count
    # Create an output list with all the even numbers
    out = []
    for i in range(interval * index, interval * (index + 1)):
        if i % 2 == 0:
            out.append(i)
    return out

# Apply a distributable function to the stream of values from
# the above source
out = Dipla.apply_distributable(get_evens, [(1, 12)]).get()

for o in out:
    print(o)
