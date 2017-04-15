from os import path
import sys
import json
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla
from examples.matrix_operations.matrix_operations import MatrixOperations


def transpose(matrix):
    size = len(matrix)
    return [[matrix[j][i] for j in range(size)] for i in range(size)]


# Note: This example uses the examples.matrix_operatons module. This
# means that it requires all clients to have that module also. It
# imports this from example.matrix_operations so the client should
# save this file with the same module signature
@Dipla.scoped_distributable(count=10)
def cofactors_matrix(matrix, index, count):
    from examples.matrix_operations.matrix_operations import MatrixOperations

    size = len(matrix)

    root_matrix = matrix
    i = int(index)
    size = len(matrix)
    cofactors = []
    # Generate all the cofactors in the i'th row (i = index)
    for j in range(size):
        sign = 1 if (i+j) % 2 == 0 else -1
        cofactors.append(sign * MatrixOperations.determinant(
          [[matrix[m][n] for n in range(size) if n != j]
              for m in range(size) if m != i]))

    return cofactors

matrix = [
    [3, 2, 3, 4, 2, 9, 1, 4, 2, 4],
    [4, 5, 2, 7, 5, 6, 3, 1, 3, 5],
    [1, 8, 9, 5, 2, 3, 4, 5, 2, 2],
    [4, 3, 2, 5, 4, 5, 6, 1, 2, 3],
    [4, 2, 5, 2, 3, 4, 1, 5, 3, 2],
    [8, 1, 4, 5, 7, 2, 4, 6, 7, 1],
    [6, 3, 6, 2, 4, 5, 3, 2, 1, 3],
    [5, 2, 4, 5, 6, 1, 2, 3, 4, 2],
    [1, 2, 5, 6, 2, 4, 3, 2, 1, 3],
    [2, 4, 5, 2, 2, 4, 2, 1, 2, 3]
]

if MatrixOperations.determinant(matrix) == 0:
    print("Matrix is not invertible!")
    sys.exit()

cofactors = Dipla.get(Dipla.apply_distributable(cofactors_matrix, [[matrix]]))

transposed = transpose([x for x in cofactors if len(x) > 0])

determinant_inverse = 1/MatrixOperations.determinant(matrix)
print('\n'.join(
    [' '.join(['{:.1f}'.format(y*determinant_inverse) for y in x])
        for x in transposed]))

# Should be:
# 0.235 0.029 -0.11 0.029
# -0.44 0.181 0.045 0.056
# 0.243 -0.24 0.066 0.014
# 0.114 0.063 0.016 -0.06
