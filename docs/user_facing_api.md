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
