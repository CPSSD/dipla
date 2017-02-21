import unittest
from dipla.server.result_verifier import ResultVerifier


class ResultVerifierTest(unittest.TestCase):

    def test_verifiers_can_be_added(self):
        rv = ResultVerifier()
        rv.add_verifier('name1', lambda i, o: True)
        rv.add_verifier('name2', lambda i, o: False)

    def test_verifier_knows_functions_are_added(self):
        rv = ResultVerifier()
        rv.add_verifier('name1', lambda i, o: True)
        self.assertTrue(rv.has_verifier('name1'))
        self.assertFalse(rv.has_verifier('name2'))

    def test_verifier_must_take_correct_num_args(self):
        rv = ResultVerifier()
        with self.assertRaises(ValueError):
            rv.add_verifier('name1', lambda a, b, c: True)
        with self.assertRaises(ValueError):
            rv.add_verifier('name2', lambda a: True)

    def test_verifier_correctly_verifies(self):
        rv = ResultVerifier()
        rv.add_verifier('double_me', lambda i, o: i*2 == o)
        self.assertTrue(rv.check_output('double_me', 2, 4))
        self.assertFalse(rv.check_output('double_me', 2, 5))

    def test_verifier_fails_open(self):
        rv = ResultVerifier()
        self.assertTrue(rv.check_output('not_here', 1, 2))
