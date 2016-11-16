from unittest import TestCase
from dipla.api.decorators import distributable


class DistributableDecoratorTest(TestCase):

    def test_that_distributable_decorator_can_be_imported(self):
        self.given_a_distributable_decorator()
        self.when_it_is_imported()
        self.then_no_errors_are_thrown()

    def test_that_distributable_decorator_can_be_applied(self):
        self.given_a_distributable_decorator()
        self.when_it_is_applied_to_a_function()
        self.then_no_errors_are_thrown()

    def given_a_distributable_decorator(self):
        pass

    def when_it_is_imported(self):
        self.operation = self._import_distributable_decorator

    def when_it_is_applied_to_a_function(self):
        self.operation = self._apply_distributable_decorator

    def then_no_errors_are_thrown(self):
        self.operation()

    def _import_distributable_decorator(self):
        from dipla.api.decorators import distributable

    def _apply_distributable_decorator(self):
        @distributable
        def foo():
            pass
        return foo
