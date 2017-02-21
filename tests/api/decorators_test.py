from unittest import TestCase
from dipla.api import Dipla


class DistributableDecoratorTest(TestCase):

    def test_that_distributable_decorator_can_be_imported(self):
        self.given_a_distributable_decorator()
        self.when_it_is_imported()
        self.then_no_errors_are_thrown()

    def test_that_distributable_decorator_can_be_applied(self):
        self.given_a_distributable_decorator()
        self.when_it_is_applied_to_a_function()
        self.then_no_errors_are_thrown()

    def test_that_distributable_decorator_adds_to_binary_manager(self):
        self.given_a_binary_manager()
        self.when_it_is_applied_to_a_function()
        self.then_no_errors_are_thrown()
        self.then_there_is_a_new_binary()

    def test_that_distributable_decorator_adds_a_verifier(self):
        self.given_a_result_verifier()
        self.given_a_distributable_decorator()
        self.when_it_is_applied_to_a_function_with_verifier()
        self.then_no_errors_are_thrown()
        self.then_there_is_a_new_verifier()

    def given_a_binary_manager(self):
        class MockBM:
            def __init__(self):
                self.regexs = []
                self.binaries = []

            def add_encoded_binaries(self, regex, binary):
                self.regexs.append(regex)
                self.binaries.append(binary)
        Dipla.binary_manager = MockBM()

    def given_a_result_verifier(self):
        class MockRV:
            def __init__(self):
                self.task_names = []
                self.verifiy_functions = []

            def add_verifier(self, task_name, func):
                self.task_names.append(task_name)
                self.verifiy_functions.append(func)
        Dipla.result_verifier = MockRV()

    def given_a_distributable_decorator(self):
        pass

    def when_it_is_imported(self):
        self.operation = self._import_distributable_decorator

    def when_it_is_applied_to_a_function(self):
        self.operation = self._apply_distributable_decorator

    def when_it_is_applied_to_a_function_with_verifier(self):
        self.operation = self._apply_distributable_decorator_with_verifier

    def then_no_errors_are_thrown(self):
        self.operation()

    def then_there_is_a_new_binary(self):
        self.assertTrue(len(Dipla.binary_manager.regexs) > 0)
        self.assertTrue(len(Dipla.binary_manager.binaries) > 0)

    def then_there_is_a_new_verifier(self):
        self.assertTrue(len(Dipla.result_verifier.task_names) > 0)
        self.assertTrue(len(Dipla.result_verifier.verifiy_functions) > 0)

    def _import_distributable_decorator(self):
        from dipla.api import Dipla

    def _apply_distributable_decorator(self):
        @Dipla.distributable()
        def foo():
            pass
        return foo

    def _apply_distributable_decorator_with_verifier(self):
        @Dipla.distributable(verifier=lambda i, o: True)
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
        from dipla.api import Dipla

    def _apply_data_source_decorator(self):
        @Dipla.data_source
        def foo():
            pass
        return foo
