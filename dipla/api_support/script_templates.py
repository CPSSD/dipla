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

output = dict()
output['signals'] = dict()

class Dipla:
    @staticmethod
    def terminate_tasks():
        output['signals']['TERMINATE'] = [True]
"""

argv_input_script = unwrap_function_script + """
args = json.loads(sys.argv[1])
output['data'] = unwraped_func(*args)
print(json.dumps(output))"""

explorer_argv_input_script = unwrap_function_script + """
discovered = []

args = json.loads(sys.argv[1])
output['data'] = unwraped_func(*args, discovered)

for value in discovered:
    if 'DISCOVERED' not in output['signals']:
        output['signals']['DISCOVERED'] = []
    output['signals']['DISCOVERED'].append([value])

print(json.dumps(output))
"""
