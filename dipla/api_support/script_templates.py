# This file is intended to store the templates for the scripts the clients
# will run.
# The '{}' will be replaced with the base64 of the pickle of the deconstructed
# function code object.

unwrap_function_script = """#! /usr/bin/python3
from base64 import b64decode
from types import CodeType
import pickle
import sys

encoded_code = {}
pickled_code = b64decode(encoded_code)
codeobject_data = pickle.loads(pickled_code)
func_code = CodeType(*codeobject_data)

def unwraped_func():
    pass

unwraped_func.__code__ = func_code
"""

argv_input_script = unwrap_function_script + """
print(unwraped_func(*sys.argv[1:]))"""

explorer_argv_input_script = unwrap_function_script + """discovered = []

print(unwraped_func(*sys.argv[1:], discovered))
for value in discovered:
    str_value = str(value)
    print("DISCOVERED("+str(len(str_value))+")("+str_value+")")
"""
