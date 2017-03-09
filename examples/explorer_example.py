from os import path
import sys
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla


@Dipla.explorer()
@Dipla.distributable()
def add_ten(input_value):
    if int(input_value) == 1:
        print("DISCOVERED(5)([[8]])")
    print(int(input_value)+10)

added_ten = Dipla.apply_distributable(add_ten, [1, 2, 3])

out = Dipla.get(added_ten)

for o in out:
    print(o)
