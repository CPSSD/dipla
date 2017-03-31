from os import path
import sys
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla

input_data = ["1", "2", "3", "4", "5"]

Dipla.start_dashboard()


@Dipla.data_source
def read_function(input_value):
    return int(input_value) * 2


def factor_verifier(inp, out):
    # Input is a tuple of the inputs, even if there's only one input.
    # E.g. (2,)
    input_int = inp[0]
    for fac in out:
        if input_int%fac:
            # If there's a non-0 remainder
            return False
    print(out, "are all factors of", input_int)
    return True

@Dipla.distributable(verifier=factor_verifier)
def get_factors(n):
    facts = [1]
    for i in range(2, n // 2 + 1):
        if n % i == 0:
            facts.append(i)
    facts.append(n)
    return facts

# Convert the input_data list to a form that dipla can use for
# distributing
data_source = Dipla.read_data_source(read_function, input_data)

# Apply a distributable function to the stream of values from
# the above source
factor_results = Dipla.apply_distributable(get_factors,
                                           data_source)

out = Dipla.get(factor_results)

for o in out:
    print(o)
