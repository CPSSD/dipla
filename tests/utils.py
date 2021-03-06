import time


def assert_with_timeout(test_case, condition_function, timeout):
    start_time = time.time()
    end_time = start_time + timeout
    condition_met = False
    while time.time() < end_time and not condition_met:
        condition_met = condition_function()
    test_case.assertTrue(condition_met)
