from os import path
import sys
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla

input_data = ["1", "2", "3", "4", "5"]
def read_function(input_value, location):
    return int(str(input_value)) * 2

# Convert the input_data list to a form that dipla can use for
# distributing
data_source = Dipla.read_data_source(read_function, input_data) 

out = Dipla.get(data_source)

for o in out:
    print(o)
