import unittest

import functools

from dipla.shared.statistics import StatisticsUpdater,\
                                    StatisticsReader,\
                                    StatisticsError


class StatisticsUpdaterTest(unittest.TestCase):

    def setUp(self):
        self.statistics = {
            "x": 0,
            "y": 0
        }

    def test_that_statistics_can_be_incremented_individually(self):
        self.given_a_statistics_updater()
        self.when_incrementing("x")
        self.when_incrementing("x")
        self.then_the_statistic_is("x", 2)
        self.when_incrementing("y")
        self.when_incrementing("y")
        self.when_incrementing("y")
        self.then_the_statistic_is("y", 3)

    def test_that_statistics_can_be_decremented_individually(self):
        self.given_a_statistics_updater()
        self.when_decrementing("x")
        self.when_decrementing("x")
        self.then_the_statistic_is("x", -2)
        self.when_decrementing("y")
        self.when_decrementing("y")
        self.when_decrementing("y")
        self.then_the_statistic_is("y", -3)

    def test_that_statistics_can_be_adjusted_individually(self):
        self.given_a_statistics_updater()
        self.when_adjusting("x", 10)
        self.when_adjusting("x", 5)
        self.when_adjusting("y", 2)
        self.when_adjusting("y", -1)
        self.then_the_statistic_is("x", 15)
        self.then_the_statistic_is("y", 1)

    def test_that_statistics_can_be_overwritten_individually(self):
        self.given_a_statistics_updater()
        self.when_overwriting("x", 500)
        self.when_overwriting("y", 30)
        self.then_the_statistic_is("x", 500)
        self.then_the_statistic_is("y", 30)

    def test_StatisticsError_is_raised_when_incrementing(self):
        self.given_a_statistics_updater()
        self.when_attempting_to_increment("z")
        self.then_a_StatisticsError_is_raised()

    def test_StatisticsError_is_raised_when_overwriting(self):
        self.given_a_statistics_updater()
        self.when_attempting_to_overwrite("z")
        self.then_a_StatisticsError_is_raised()

    def given_a_statistics_updater(self):
        self.statistics_updater = StatisticsUpdater(self.statistics)

    def when_incrementing(self, statistic):
        self.statistics_updater.increment(statistic)

    def when_decrementing(self, statistic):
        self.statistics_updater.decrement(statistic)

    def when_adjusting(self, statistic, amount):
        self.statistics_updater.adjust(statistic, amount)

    def when_overwriting(self, statistic, value):
        self.statistics_updater.overwrite(statistic, value)

    def when_attempting_to_increment(self, statistic):
        self.operation = functools.partial(self.when_incrementing, statistic)

    def when_attempting_to_overwrite(self, statistic):
        arbitrary_value = 100
        self.operation = functools.partial(self.when_overwriting,
                                           statistic,
                                           arbitrary_value)

    def then_the_statistic_is(self, statistic, expected):
        self.assertEqual(expected, self.statistics[statistic])

    def then_a_StatisticsError_is_raised(self):
        self.assertRaises(StatisticsError, self.operation)


class StatisticsReaderTest(unittest.TestCase):

    def setUp(self):
        self.statistics = {
            "x": 20,
            "y": "healthy"
        }

    def test_that_individual_statistics_can_be_read(self):
        self.given_a_statistics_reader()
        self.when_reading("x")
        self.then_the_value_is(20)
        self.when_reading("y")
        self.then_the_value_is("healthy")

    def test_StatisticsError_is_raised_when_reading(self):
        self.given_a_statistics_reader()
        self.when_attempting_to_read("z")
        self.then_a_StatisticsError_is_raised()

    def test_that_all_statistics_can_be_read(self):
        self.given_the_statistics_are({"a": 1, "b": 4})
        self.given_a_statistics_reader()
        self.when_reading_all()
        self.then_the_statistics_are({"a": 1, "b": 4})

    def test_that_statistics_are_immutable(self):
        self.given_a_statistics_reader()
        self.when_reading_all()
        self.when_modifying("x", 200)
        self.when_reading("x")
        self.then_the_value_is(20)

    def given_the_statistics_are(self, statistics):
        self.statistics = statistics

    def given_a_statistics_reader(self):
        self.statistics_reader = StatisticsReader(self.statistics)

    def when_reading(self, statistic):
        self.value = self.statistics_reader.read(statistic)

    def when_modifying(self, statistic, new_value):
        self.value[statistic] = new_value

    def when_attempting_to_read(self, statistic):
        self.operation = functools.partial(self.when_reading, statistic)

    def when_reading_all(self):
        self.value = self.statistics_reader.read_all()

    def then_the_value_is(self, expected):
        self.assertEqual(expected, self.value)

    def then_the_statistics_are(self, expected):
        self.then_the_value_is(expected)

    def then_a_StatisticsError_is_raised(self):
        self.assertRaises(StatisticsError, self.operation)


if __name__ == "__main__":
    unittest.main()
