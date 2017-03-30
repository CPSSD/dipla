# This file is intended to store the templates for the scripts the clients
# will run.
# The '{}' will be replaced with the base64 of the pickle of the deconstructed
# function code object.

unwrap_function_script = """#! /usr/bin/python3
from base64 import b64decode
from types import CodeType
import dill
import json
import sys

encoded_code = {}
pickled_code = b64decode(encoded_code)
codeobject_data = dill.loads(pickled_code)
func_code = CodeType(*codeobject_data)

def unwraped_func():
    pass

unwraped_func.__code__ = func_code
"""

argv_input_script = unwrap_function_script + """
output = dict()

args = json.loads(sys.argv[1])
output['data'] = unwraped_func(*args)
output['signals'] = dict()
print(json.dumps(output))"""

explorer_argv_input_script = unwrap_function_script + """discovered = []

output = dict()
output['signals'] = dict()

args = json.loads(sys.argv[1])
output['data'] = unwraped_func(*args, discovered)

for value in discovered:
    f = open('yolo.swag', "w")
    f.write(str(value) + " in discovered")
    if 'DISCOVERED' not in output['signals']:
        f.write("setting signal to empty list discovered")
        output['signals']['DISCOVERED'] = []
    f.write("about to appedn")
    output['signals']['DISCOVERED'].append([value])
    f.write("Appended")
    f.close()

print(json.dumps(output))
"""
