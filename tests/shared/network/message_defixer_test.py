import functools
import unittest
from dipla.shared.network.message_defixer import MessageDefixer
from dipla.shared.network.message_defixer import NoMessageException
from dipla.shared.network.message_defixer import IllegalHeaderException


class MessageDefixerTest(unittest.TestCase):

    def test_that_message_defixer_starts_in_READ_HEADER_state(self):
        self.given_a_message_defixer()
        self.when_fed_nothing()
        self.then_its_state_is_READ_HEADER()

    def test_that_message_defixer_stays_in_READ_HEADER_state_when_fed_a_character(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("0")
        self.then_its_state_is_READ_HEADER()

    def test_that_message_defixer_stays_in_READ_HEADER_state_when_fed_empty_character(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed_empty_character()
        self.then_its_state_is_READ_HEADER()

    def test_that_message_defixer_turns_to_READ_BODY_state_when_fed_colon(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("2:")
        self.then_its_state_is_READ_BODY()

    def test_that_message_defixer_stays_in_READ_HEADER_state_when_fed_two_characters(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("22")
        self.then_its_state_is_READ_HEADER()

    def test_that_message_defixer_turns_to_READ_BODY_state_when_fed_two_characters_then_a_colon(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("22:")
        self.then_its_state_is_READ_BODY()

    def test_that_message_defixer_turns_to_READ_HEADER_state_when_it_has_read_enough_characters(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("1:a")
        self.then_its_state_is_READ_HEADER()

    def test_that_message_defixer_does_not_turn_to_READ_HEADER_state_when_it_has_not_read_enough_characters(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("2:a")
        self.then_its_state_is_READ_BODY()

    def test_that_message_defixer_turns_to_READ_HEADER_state_when_it_has_read_multi_digit_length_message(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("12:indisputable")
        self.then_its_state_is_READ_HEADER()

    def test_that_message_defixer_stays_in_READ_BODY_state_when_it_has_not_read_enough_of_a_multi_digit_message(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("12:indisputabl")
        self.then_its_state_is_READ_BODY()

    def test_that_message_defixer_can_return_message_once_fully_read(self):
        self.given_a_message_defixer()
        self.when_fed("12:indisputable")
        self.when_a_defixed_message_is_requested()
        self.then_the_defixed_message_is("indisputable")

    def test_that_message_defixer_can_read_multiple_consecutive_full_messages(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("3:foo")
        self.when_a_defixed_message_is_requested()
        self.then_the_defixed_message_is("foo")
        self.when_fed("3:bar")
        self.when_a_defixed_message_is_requested()
        self.then_the_defixed_message_is("bar")

    def test_that_message_defixer_can_read_multiple_consecutive_full_messages_of_varying_length(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("3:foo")
        self.when_a_defixed_message_is_requested()
        self.then_the_defixed_message_is("foo")
        self.when_fed("4:bars")
        self.when_a_defixed_message_is_requested()
        self.then_the_defixed_message_is("bars")

    def test_that_message_defixer_can_read_multiple_consecutive_full_messages_without_being_read_until_end(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("3:foo")
        self.when_fed("4:bars")
        self.when_a_defixed_message_is_requested()
        self.then_the_defixed_message_is("foo")
        self.when_a_defixed_message_is_requested()
        self.then_the_defixed_message_is("bars")

    def test_that_message_defixer_stays_in_READ_HEADER_state_after_reading_full_message_and_starting_another(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("3:foo")
        self.then_its_state_is_READ_HEADER()
        self.when_fed("4:bar")
        self.then_its_state_is_READ_BODY()
        self.when_fed("s")
        self.then_its_state_is_READ_HEADER()

    def test_that_message_defixer_throws_NoMessageException_when_message_is_requested_but_not_READ_HEADER(self):  # nopep8
        self.given_a_message_defixer()
        self.when_attempting_to_request_defixed_message()
        self.then_a_NoMessageException_is_thrown()

    def test_that_message_defixer_throws_NoMessageException_when_reading_twice_without_enough_data(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("3:foo")
        self.when_a_defixed_message_is_requested()
        self.then_the_defixed_message_is("foo")
        self.when_attempting_to_request_defixed_message()
        self.then_a_NoMessageException_is_thrown()

    def test_that_message_defixer_can_read_multiple_consecutive_full_messages_fed_in_one_go(self):  # nopep8
        self.given_a_message_defixer()
        self.when_fed("5:Hello6:World!")
        self.when_a_defixed_message_is_requested()
        self.then_the_defixed_message_is("Hello")
        self.when_a_defixed_message_is_requested()
        self.then_the_defixed_message_is("World!")

    def test_that_message_defixer_throws_IllegalHeaderException_when_header_contains_a_letter(self):  # nopep8
        self.given_a_message_defixer()
        self.when_attempting_to_feed("a")
        self.then_an_IllegalHeaderException_is_thrown()

    def test_that_message_defixer_throws_IllegalHeaderException_when_header_contains_letter_at_end(self):  # nopep8
        self.given_a_message_defixer()
        self.when_attempting_to_feed("512k")
        self.then_an_IllegalHeaderException_is_thrown()

    def test_that_message_defixer_throws_IllegalHeaderException_when_header_contains_special_character(self):  # nopep8
        self.given_a_message_defixer()
        self.when_attempting_to_feed("512;")
        self.then_an_IllegalHeaderException_is_thrown()

    def test_that_message_defixer_can_read_message_full_of_colons(self):
        self.given_a_message_defixer()
        self.when_fed("10:::::::::::")
        self.when_a_defixed_message_is_requested()
        self.then_the_defixed_message_is("::::::::::")

    def given_a_message_defixer(self):
        self.message_defixer = MessageDefixer()

    def when_fed_nothing(self):
        pass

    def when_fed_empty_character(self):
        self.message_defixer.feed_character("")

    def when_attempting_to_feed(self, string):
        self.operation = functools.partial(self.when_fed, string)

    def when_fed(self, string):
        for c in string:
            self.message_defixer.feed_character(c)

    def when_a_defixed_message_is_requested(self):
        self.defixed_message = self.message_defixer.get_defixed_message()

    def when_attempting_to_request_defixed_message(self):
        self.operation = self.when_a_defixed_message_is_requested

    def then_its_state_is_READ_HEADER(self):
        self.assert_message_defixer_state(MessageDefixer.READ_HEADER_STATE)

    def then_its_state_is_READ_BODY(self):
        self.assert_message_defixer_state(MessageDefixer.READ_BODY_STATE)

    def then_the_defixed_message_is(self, expected_message):
        self.assertEquals(expected_message, self.defixed_message)

    def then_a_NoMessageException_is_thrown(self):
        try:
            self.operation()
            self.fail("NoMessageException wasn't thrown.")
        except NoMessageException:
            pass

    def then_an_IllegalHeaderException_is_thrown(self):
        try:
            self.operation()
            self.fail("IllegalHeaderException wasn't thrown")
        except IllegalHeaderException:
            pass

    def assert_message_defixer_state(self, expected_state):
        self.assertEquals(expected_state, self.message_defixer.get_state())


if __name__ == "__main__":
    unittest.main()
