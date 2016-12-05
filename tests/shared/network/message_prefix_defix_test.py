import unittest

from dipla.shared.network.message_defixer import MessageDefixer
from dipla.shared.network.message_prefixer import prefix_message as prefix


class MessagePrefixDefixTest(unittest.TestCase):

    def test_message_prefix_and_defix(self):
        self.assertEquals("Foo", defix(prefix("Foo")))
        self.assertEquals("Hello!", defix(prefix("Hello!")))
        self.assertEquals("!£$%^&*()_+", defix(prefix("!£$%^&*()_+")))
        self.assertEquals("Hello\0world!", defix(prefix("Hello\0world!")))
        self.assertEquals("AESTHETIC", defix(prefix("AESTHETIC")))
        self.assertEquals("A E S T H E tic", defix(prefix("A E S T H E tic")))
        self.assertEquals("::::", defix(prefix("::::")))


# This is a helper method to simplify tests
def defix(string):
    message_defixer = MessageDefixer()
    for c in string:
        message_defixer.feed_character(c)
    return message_defixer.get_defixed_message()


if __name__ == "__main__":
    unittest.main()
