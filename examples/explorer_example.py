from os import path
import sys
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla

@Dipla.explorer()
@Dipla.distributable()
def add_ten(input_value, discovered):
    # If the input value is 1, discover a new input, '8'
    if input_value == 1:
        discovered.append(8)
    return input_value + 10

# The inputs of add_ten are 1, 2, 3. Since there is a 1 here, it should
# discover another input 8. This means the output should add ten to all
# four inputs, outputting 11, 12, 13, 18

out = Dipla.apply_distributable(add_ten, [1, 2, 3]).get()

for o in out:
    print(o)
