import unittest
from dipla.api import Dipla
from dipla.client.client import Client


class DiplaAPITest(unittest.TestCase):

    def test_read_data_input(self):
        input_data = ["1", "2", "3", "4", "5"]

        def data_source_function(input_value):
            return int(input_value) * 2

        promised = Dipla.read_data_source(input_data, data_source_function)
        self.assertIsNotNone(promised.task_uid)

#    def test_get_on_data_source(self):
#
#        def read_function(input_value):
#            return int(input)
#
#        data_source = Dipla.read_data_source(read_function, ["1", "2", "3"])
#        out = Dipla.get(data_source)
#
#        # Something needs to connect to the server now to start the
#        # processing
#
#        self.assertEqual(["1", "2", "3"], out)
