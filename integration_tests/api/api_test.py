from unittest import TestCase

from dipla.api import Dipla


class APIIntegrationTest(TestCase):

    def test_scoped_task_inputs_contain_correct_arguments(self):
        @Dipla.scoped_distributable(count=3)  # n = 3
        def func(input_value, index, count):
            return None  # This function isn't used in this test

        Dipla.apply_distributable(func, [(1, 12)])
        inputs = []
        while Dipla.task_queue.has_next_input():
            inputs.append(Dipla.task_queue.pop_task_input().values)
        self.assertEquals(3, len(inputs))
        # Should contain 3 intervals, each with the same (1, 12) input
        self.assertEquals(
            [
                 [[(1, 12)], [0], [3]],
                 [[(1, 12)], [1], [3]],
                 [[(1, 12)], [2], [3]]
            ],
            inputs)
