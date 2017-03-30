from os.path import abspath
import sys
sys.path.append(abspath('../dipla'))
from dipla.api import Dipla


COMPUTATIONAL_INTENSITY = 1000


@Dipla.data_source
def read(input_value):
    return input_value


@Dipla.distributable()
def square(n):
    return int(n)**2


def generate_inputs():
    inputs = []
    for n in range(COMPUTATIONAL_INTENSITY):
        inputs.append(str(n))
        if len(inputs) == 5:
            yield inputs
            inputs = []
    yield inputs


def main():
    # Dipla.start_dashboard()

    data_source = Dipla.read_data_source(
        read,
        generate_inputs()
    )

    squared_inputs_promise = Dipla.apply_distributable(
        square,
        data_source
    )

    squared_inputs = [int(s) for s in Dipla.get(squared_inputs_promise)]
    sum_of_squared_inputs = sum(squared_inputs)
    print(sum_of_squared_inputs)
    

if __name__ == '__main__':
    main()

