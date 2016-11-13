import unittest
from dipla.shared.uid_generator import generate_uid
from dipla.shared.uid_generator import IDsExhausted


class UIDGeneratorTest(unittest.TestCase):

    def test_generate_uid(self):
        self.assertEqual(2, len(generate_uid([], 2)))

        uid = generate_uid([], 8, choices="abcdef")
        # Check all characters in uid are present in the choices
        self.assertTrue(set(uid) <= set("abcdef"))

        uid_set = set()
        for i in range(4):
            uid_set.add(generate_uid(uid_set, 2, choices="ab"))

        with self.assertRaises(IDsExhausted):
            generate_uid(uid_set, 2, choices="ab")

        # Reset the uid set to try a new edge case
        uid_set = set()

        uid_set.add(generate_uid(uid_set, 2, choices="aa"))

        with self.assertRaises(IDsExhausted):
            generate_uid(uid_set, 2, choices="aa")
