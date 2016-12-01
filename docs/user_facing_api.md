# User Facing API

## Distributing work

To distribute work using dipla, you should create chunks of code that can exist in isolation, and
that make sense for a machine to be able to run that chunk without depending on anything else. You
can create one of these chunks by creating a function and giving it the @distributable decorator,
for example if you wanted to create a chunk that would calculate the square root of a number, you
could do the following:

```
@distributable
def square_root(input_value):
    return math.sqrt(input_value)
```

You can apply this task to your input values in a distributed way by informing dipla about this
task, and telling it what input values it should be applied to:

```
square_rooted_values = Dipla.apply_distributable(square_root, input_values)
```

## Reading Input

There are currently two ways possible to receive input for your distributable functions. The first
is to use a iterable python object like a list, or a set. You can convert the iterable object into
a form that Dipla can distribute in the following way:

```
my_inputs = Dipla.read_data_source([1, 4, 9, 16, 25])
```

This will mean that anywhere else my_inputs is used, it will represent the values from the iterable
list `[1, 4, 9, 16, 25]`

The other way to read inputs is by using a function that retrieves inputs from some source. In this
case the parameter to the function would be used to retrieve the input, for example, if we wanted
to get inputs by fetching some urls we would have a function and the list of urls:

```
@data_source
def fetch_url(url_string):
    return URL(url_string).fetch()

url_strings = ['www.google.com', 'www.dcu.ie', 'www.facebook.com/login']
my_inputs = Dipla.read_data_source(fetch_url, url_strings)
```

This @data_source function will not be distributed, it will run on the server.

## Creating a distributable program

Once you have a data source to input your data, you can apply the tasks to the inputs. Once you have
run a task on the inputs, you can run another task on the output of the first task. To finish all of
your work off, you should have a `Dipla.get()` or a `Dipla.start() call`. Take this example, where
we square root some inputs, then cube them:

```
@distributable
def square_root(input_value):
    import math
    return math.sqrt(input_value)

@distributable
def cubed_value(input_value):
    return input_value**3

my_inputs = Dipla.read_data_source([1, 4, 9, 16, 25])

rooted = Dipla.apply_distributable(square_root, my_inputs)
cubed = Dipla.apply_distributable(cubed_value, rooted)

final_output = Dipla.get(cubed)

for num in final_output:
    print(num)
```

The `Dipla.get()` shown above is very important, its what converts your results out of the format
that _Dipla_ needs it to be in for it to use them, back into the format that _you_ can understand
and manipulate with normal code.

There is an alternative to `Dipla.get()`. You can also use `Dipla.start()`, which has does not
return any output.
