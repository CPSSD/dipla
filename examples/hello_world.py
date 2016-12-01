from os import path
import sys
sys.path.append(path.abspath('../dipla'))

from dipla.api import dipla

input_data = [1, 2, 3, 4, 5]

# Convert the input_data list to a form that dipla can use for
# distributing
data_source = dipla.read_data_source(input_data) 
