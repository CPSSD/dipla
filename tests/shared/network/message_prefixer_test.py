import unittest
from dipla.shared.network.message_prefixer import prefix_message as prefix


class MessagePrefixTest(unittest.TestCase):

    def test_message_prefix(self):
        self.assertEquals("0:", prefix(""))
        self.assertEquals("1:x", prefix("x"))
        self.assertEquals("1:y", prefix("y"))
        self.assertEquals("2:xx", prefix("xx"))
        self.assertEquals("3:xyz", prefix("xyz"))
        self.assertEquals("7:foo bar", prefix("foo bar"))
        self.assertEquals("17:arbitrary message", prefix("arbitrary message"))


if __name__ == "__main__":
    unittest.main()
