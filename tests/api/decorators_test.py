from unittest import TestCase
from dipla.api.decorators import distributable
from dipla.api.decorators import data_source


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


class TaskInputDecoratorTest(TestCase):

    def test_that_data_source_decorator_can_be_imported(self):
        self.given_a_data_source_decorator()
        self.when_it_is_imported()
        self.then_no_errors_are_thrown()

    def test_that_data_source_decorator_can_be_applied(self):
        self.given_a_data_source_decorator()
        self.when_it_is_applied_to_a_function()
        self.then_no_errors_are_thrown()

    def given_a_data_source_decorator(self):
        pass

    def when_it_is_imported(self):
        self.operation = self._import_data_source_decorator

    def when_it_is_applied_to_a_function(self):
        self.operation = self._apply_data_source_decorator

    def then_no_errors_are_thrown(self):
        self.operation()

    def _import_data_source_decorator(self):
        from dipla.api.decorators import data_source

    def _apply_data_source_decorator(self):
        @data_source
        def foo():
            pass
        return foo
