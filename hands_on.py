from dipla.api import Dipla


example_data = list(range(1, 10))

@Dipla.distributable()
def multiply_by_10(N):
    return N * 10

times_ten = Dipla.apply_distributable(multiply_by_10, example_data)

for out in times_ten.get():
    print(out)
