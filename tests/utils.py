import time
from unittest.mock import MagicMock

from collections import namedtuple


def assert_with_timeout(test_case, condition_function, timeout):
    start_time = time.time()
    end_time = start_time + timeout
    condition_met = False
    while time.time() < end_time and not condition_met:
        condition_met = condition_function()
    test_case.assertTrue(condition_met)


def create_mock_object(methods):
    mock_object = namedtuple('MockObject', methods)
    for method in methods:
        setattr(mock_object, method, MagicMock())
    return mock_object
