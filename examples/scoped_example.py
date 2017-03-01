from os import path
import sys
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla

@Dipla.scoped_distributable(count=3)
def get_evens(input_value, index, count):
    import json
    interval = int(json.loads(input_value)[1]) // int(count)
    out = []
    for i in range(interval * int(index), interval * (int(index)+1)):
        if i % 2 == 0:
            out.append(i)
    return out

# Apply a distributable function to the stream of values from
# the above source
evens_results = Dipla.apply_distributable(get_evens, [(1, 12)])

out = Dipla.get(evens_results)

for o in out:
    print(o)
