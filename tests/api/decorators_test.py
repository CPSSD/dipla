from unittest import TestCase
from unittest.mock import Mock, patch
from dipla.shared import uid_generator
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
        self.given_a_distributable_decorator()
        self.when_it_is_applied_to_a_function()
        self.then_no_errors_are_thrown()
        self.when_the_function_is_applied_to_data()
        self.when_the_server_is_started()
        self.then_there_is_a_new_binary()

    def test_that_distributable_decorator_adds_a_verifier(self):
        self.given_a_result_verifier()
        self.given_a_distributable_decorator()
        self.when_it_is_applied_to_a_function_with_verifier()
        self.then_no_errors_are_thrown()
        self.then_there_is_a_new_verifier()

    def given_a_binary_manager(self):
        self.binary_manager = Mock()

        def create_mock_binary_manager():
            return self.binary_manager

        Dipla._create_binary_manager = create_mock_binary_manager

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

    def when_the_server_is_started(self):
        with patch('dipla.server.server.Server.start') as start_function:
            Dipla.get(self.promised)

    def when_it_is_imported(self):
        self.operation = self._import_distributable_decorator

    def when_it_is_applied_to_a_function(self):
        self.operation = self._apply_distributable_decorator

    def when_it_is_applied_to_a_function_with_verifier(self):
        self.operation = self._apply_distributable_decorator_with_verifier

    def when_the_function_is_applied_to_data(self):
        self.promised = Dipla.apply_distributable(self.applied_distributable,
                                                  [1, 2, 3])

    def then_no_errors_are_thrown(self):
        self.operation()

    def then_there_is_a_new_binary(self):
        self.assertTrue(
            len(self.binary_manager.add_encoded_binaries.mock_calls) > 0)

    def then_there_is_a_new_verifier(self):
        self.assertTrue(len(Dipla.result_verifier.task_names) > 0)
        self.assertTrue(len(Dipla.result_verifier.verifiy_functions) > 0)

    def _import_distributable_decorator(self):
        from dipla.api import Dipla

    def _apply_distributable_decorator(self):
        @Dipla.distributable()
        def foo():
            pass
        self.applied_distributable = foo
        return foo

    def _apply_distributable_decorator_with_verifier(self):
        @Dipla.distributable(verifier=lambda i, o: True)
        def foo():
            pass
        self.applied_distributable = foo
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


class ScopedDistributableTest(TestCase):

    def test_that_distributable_decorator_can_be_imported(self):
        self.given_a_scoped_distributable_decorator()
        self.when_it_is_imported()
        self.then_no_errors_are_thrown()

    def test_that_distributable_decorator_can_be_applied(self):
        self.given_a_scoped_distributable_decorator()
        self.when_it_is_applied_to_a_function()
        self.then_no_errors_are_thrown()

    def test_that_distributable_decorator_adds_to_binary_manager(self):
        self.given_a_binary_manager()
        self.given_a_scoped_distributable_decorator()
        self.when_it_is_applied_to_a_function()
        self.then_no_errors_are_thrown()
        self.when_the_function_is_applied_to_data()
        self.when_the_server_is_started()
        self.then_there_is_a_new_binary()

    def test_that_distributable_decorator_adds_a_verifier(self):
        self.given_a_result_verifier()
        self.given_a_scoped_distributable_decorator()
        self.when_it_is_applied_to_a_function_with_verifier()
        self.then_no_errors_are_thrown()
        self.then_there_is_a_new_verifier()

    def test_that_not_implemented_error_is_thrown_if_count_not_provided(self):
        self.given_a_scoped_distributable_decorator()
        self.then_no_count_causes_implemented_error()

    def given_a_binary_manager(self):
        self.binary_manager = Mock()

        def create_mock_binary_manager():
            return self.binary_manager

        Dipla._create_binary_manager = create_mock_binary_manager

    def given_a_result_verifier(self):
        class MockRV:
            def __init__(self):
                self.task_names = []
                self.verifiy_functions = []

            def add_verifier(self, task_name, func):
                self.task_names.append(task_name)
                self.verifiy_functions.append(func)
        Dipla.result_verifier = MockRV()

    def given_a_scoped_distributable_decorator(self):
        pass

    def when_it_is_imported(self):
        self.operation = self._import_scoped_distributable_decorator

    def when_it_is_applied_to_a_function(self):
        self.operation = self._apply_scoped_distributable_decorator

    def when_it_is_applied_to_a_function_with_verifier(self):
        self.operation =\
            self._apply_scoped_distributable_decorator_with_verifier

    def when_the_function_is_applied_to_data(self):
        self.promised = Dipla.apply_distributable(self.applied_distributable,
                                                  [1, 2, 3])

    def then_no_errors_are_thrown(self):
        self.operation()

    def when_the_server_is_started(self):
        with patch('dipla.server.server.Server.start') as start_function:
            Dipla.get(self.promised)

    def then_no_count_causes_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self._apply_scoped_distributable_without_count()

    def then_there_is_a_new_binary(self):
        self.assertTrue(
            len(self.binary_manager.add_encoded_binaries.mock_calls) > 0)

    def then_there_is_a_new_verifier(self):
        self.assertTrue(len(Dipla.result_verifier.task_names) > 0)
        self.assertTrue(len(Dipla.result_verifier.verifiy_functions) > 0)

    def _import_scoped_distributable_decorator(self):
        from dipla.api import Dipla

    def _apply_scoped_distributable_decorator(self):
        @Dipla.scoped_distributable(count=2)
        def foo(input_value, interval, count):
            pass
        self.applied_distributable = foo
        return foo

    def _apply_scoped_distributable_decorator_with_verifier(self):
        @Dipla.scoped_distributable(count=2, verifier=lambda i, o: True)
        def foo(input_value, interval, count):
            pass
        self.applied_distributable = foo
        return foo

    def _apply_scoped_distributable_without_count(self):
        @Dipla.scoped_distributable
        def func(input_value, index, count):
            return input_value+1
