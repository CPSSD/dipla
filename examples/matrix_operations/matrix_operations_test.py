import unittest
from examples.matrix_operations.matrix_operations import MatrixOperations


class MatrixOperationsTest(unittest.TestCase):

    def test_correct_determinant_is_found_for_size_2_matrix(self):
        matrix = [[2, 3], [5, 1]]
        self.assertEquals(-13, MatrixOperations.determinant(matrix))

    def test_correct_determinant_is_found_for_1_to_nsquared_in_matrix(self):
        matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        self.assertEquals(0, MatrixOperations.determinant(matrix))

    def test_correct_determinant_is_found_for_arbitrary_matrix(self):
        matrix = [[3, 0, 2], [2, 0, -2], [0, 1, 1]]
        self.assertEquals(10, MatrixOperations.determinant(matrix))

    def test_correct_determinant_is_found_for_large_matrix(self):
        matrix = [
            [3, 2, 3, 2, 4],
            [4, 2, 1, 2, 7],
            [7, 1, 8, 9, 10],
            [1, 10, 11, 10, 1],
            [12, 1, 22, 5, 3]
        ]
        self.assertEquals(1388, MatrixOperations.determinant(matrix))
