from os import path
import sys
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla

# This tries all values to see if it can discover a block with two
# zeroes. This is split into one hundred sections, theoretically distributing
# a tenth of the work to each of one hundred workers

max_search = 100000

@Dipla.scoped_distributable(count=(max_search//1000))
def find_block(input_value, index, count):
    import hashlib
    start = index*input_value//count
    end = (index+1)*input_value//count
    out = []
    for i in range(start, end):
        check = hashlib.sha256(hashlib.sha256(bytes(i)).digest()).digest()
        if check[-2:] == b'\0\0':
            out.append(i)
    return out

out = Dipla.apply_distributable(find_block, [max_search]).get()
print([x for x in out if len(x) > 0])
