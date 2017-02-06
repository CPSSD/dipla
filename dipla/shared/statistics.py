class StatisticsUpdater:
    """
    A class to update and modify statistics.
    All statistics modification should happen through this class exclusively.
    """

    def __init__(self, statistics):
        """Creates a StatisticsUpdater, should ideally be called once."""
        self.__statistics = statistics

    def increment(self, statistic):
        """Increments an integer statistic by 1."""
        self.adjust(statistic, 1)

    def decrement(self, statistic):
        """Decrements an integer statistic by 1"""
        self.adjust(statistic, -1)

    def adjust(self, statistic, amount):
        """Adjust the value of a statistic by a specified amount"""
        check_statistic_exists(statistic, self.__statistics)
        self.__statistics[statistic] += amount

    def overwrite(self, statistic, value):
        """Overwrites a statistic's old value with a new one."""
        check_statistic_exists(statistic, self.__statistics)
        self.__statistics[statistic] = value


class StatisticsReader:
    """
    A class to read statistics in an immutable way.
    """

    def __init__(self, statistics):
        self.__statistics = statistics

    def read(self, statistic):
        """Fetch the value for a statistic."""
        check_statistic_exists(statistic, self.__statistics)
        return self.__statistics[statistic]

    def read_all(self):
        """Fetch an immutable dictionary of all statistics."""
        return self.__statistics.copy()


class StatisticsError(Exception):
    pass


def check_statistic_exists(statistic, statistics):
    """Raise a StatisticsError if the statistic doesn't exist."""
    if statistic not in statistics:
        error_message = "Statistic {} does not exist".format(statistic)
        raise StatisticsError(error_message)
