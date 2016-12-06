import timeit


class QualityScorer:

    SAMPLE_SIZE = 10000

    def get_quality(self):
        return (self._test_floating_point_speed() +
                self._test_string_speed() +
                self._test_lookup_speed())

    def _test_floating_point_speed(self):
        return timeit.timeit("[x * 3.1415 for x in range(100)]",
                             number=QualityScorer.SAMPLE_SIZE)

    def _test_string_speed(self):
        return timeit.timeit("'-'.join([str(x) for x in range(100)])",
                             number=QualityScorer.SAMPLE_SIZE)

    def _test_lookup_speed(self):
        return timeit.timeit("[a[x] for x in range(100)]",
                             setup="a = {x:str(x) for x in range(100)}",
                             number=QualityScorer.SAMPLE_SIZE)
