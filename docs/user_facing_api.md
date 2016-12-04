# User Facing API

## Distributing work

To distribute work using dipla, you should create chunks of code that can exist in isolation, and that make sense for a machine to be able to run that chunk without depending on anything else. You can create one of these chunks by creating a function that takes a string input parameter and giving it the @Dipla.distributable decorator, for example if you wanted to create a chunk that would calculate the square root of a number you could do the following:

```
@Dipla.distributable
def square_root(input_value):
    import math
    return math.sqrt(int(input_value))
```

You can apply this task to your input values in a distributed way by informing dipla about this task, and telling it what input values it should be applied to:

```
square_rooted_values = Dipla.apply_distributable(square_root, input_values)
```

## Reading Input

There are currently two ways possible to receive input for your distributable functions. The first is to use an iterable python object like a list, or a set. You use it by simply passing it as the input parameter to `apply_distributable()`, for example:

```
processed = Dipla.apply_distributable(my_task, [1, 4, 9, 16, 25])
```

This will mean that my_task will be applied to everything in the iterable collection to produce a new output location, represented by `processed`

The other way to read inputs is by using a function that retrieves inputs from some source. In this case the parameter to the function would be used to retrieve the input, for example, if we wanted to get inputs by fetching some urls we would have a function and the list of urls:

```
@Dipla.data_source
def fetch_url(url_string):
    import urllib.request
    return urllib.request.urlopen(url_string).read()

url_strings = ['www.google.com', 'www.dcu.ie', 'www.facebook.com/login']
my_inputs = Dipla.read_data_source(fetch_url, url_strings)
```

## Creating a distributable program

Once you have a data source to input your data, you can apply the tasks to the inputs. Once you have run a task on the inputs, you can run another task on the output of the first task. To finish all of your work off, you should have a `Dipla.get()` or a `Dipla.start()` call. Take this example where we square root some inputs and then cube them:

```
from dipla.api import Dipla

@Dipla.distributable
def square_root(input_value):
    import math
    return math.sqrt(int(input_value))

@Dipla.distributable
def cubed_value(input_value):
    return int(input_value)**3

rooted = Dipla.apply_distributable(square_root, [1, 4, 9, 16, 25])
cubed = Dipla.apply_distributable(cubed_value, rooted)

final_output = Dipla.get(cubed)

for num in final_output:
    print(num)
```

The `Dipla.get()` shown above is very important, its what converts your results out of the format that _Dipla_ needs it to be in for it to use them, back into the format that _you_ can understand and manipulate with normal code.

There is an alternative to `Dipla.get()`. You can also use `Dipla.start()`, which does not return anything.

## More advanced usage

You can also make tasks have multiple different dependencies. To do this you only need to add extra parameters to `Dipla.apply_distributable`. For example:

```
from dipla.api import Dipla

@Dipla.distributable
def fibonacci(input_value):
    a = 1
    b = 1
    for i in range(int(input_value)):
        temp_a = a
        a = b
        b = b + temp_a
    return b

@Dipla.distributable
def negate(input_value):
    return -1 * int(input_value)

@Dipla.distributable
def reduce(fibonacci_input, negate_input):
    return int(fibonacci_input) + int(negate_input)

@Dipla.data_source
def read_database(input):
    import databaselib
    sqldatabase = databaselib.create_database()
    return sqldatabase.read_int(
        "SELECT value FROM inputs WHERE id = ?").bind(int(input))

my_inputs = Dipla.read_data_source(read_database, [1, 2, 3, 4, 5])

fibonacci = Dipla.apply_distributable(fibonacci, my_inputs)
negated = Dipla.apply_distributable(negate, my_inputs)

# Parameters must be given in the same order than the
# @Dipla.distributable takes them
reduced = Dipla.apply_distributable(reduce, fibonacci, negate)

final_output = Dipla.get(reduced)

for num in final_output:
    print(num)
```
