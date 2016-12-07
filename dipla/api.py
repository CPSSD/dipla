from dipla.api_support.function_serialise import get_encoded_script
from dipla.server.server import BinaryManager
from dipla.server.task_queue import TaskQueue, Task, DataSource, MachineType
from dipla.shared import uid_generator


class Dipla:

    # BinaryManager and TaskQueue to be injected into server.
    binary_manager = BinaryManager()
    task_queue = TaskQueue()

    @staticmethod
    def distributable(function):
        """
        Takes a function and converts it to a binary, the binary is then
        registered with the BinaryManager. The function is returned unchanged.
        """
        # Turn the function into a base64'd Python script.
        base64_binary = get_encoded_script(function)
        # Register the result as a new binary for any platform with the name
        # of the function as the task name.
        Dipla.binary_manager.add_encoded_binaries('.*', [
            (function.__name__, base64_binary),
        ])
        # Don't actually modify the final function.
        return function

    @staticmethod
    def data_source(function):
        def read_function_wrapper(source, location):
            # Abstract the ability to return multiple results from the
            # user, always give them one input and expect one output.
            # Give them each value in the source and convert their
            # output to a single value array
            while len(source) > 0:
                return [function(source.pop(0))]
        return read_function_wrapper

    @staticmethod
    def read_data_source(read_function, source):
        task_uid = uid_generator.generate_uid(
            length=8, existing_uids=[Dipla.task_queue.get_task_ids()])
        # The Task name is only used to run binaries, which does not
        # happen when reading a data source, so we simply call this
        # 'read_data_source' as it is never used
        read_task = Task(task_uid, 'read_data_source', MachineType.server)
        source_uid = uid_generator.generate_uid(length=8, existing_uids=[])
        read_task.add_data_source(DataSource.create_source_from_iterable(
            source, source_uid, read_function))
        Dipla.task_queue.push_task(read_task)
        return Promise(task_uid)

    @staticmethod
    def apply_distributable(function, *args):
        task = Task(None, function.__name__, MachineType.client)
        for arg in args:
            if type(arg) is list:
                source_uid = uid_generator.generate_uid(
                    length=8, existing_uids=Dipla.task_queue.get_task_ids())
                task.add_data_source(DataSource.create_source_From_iterable(
                    arg,
                    source_uid))
        pass


class Promise:

    def __init__(self, promise_uid):
        self.task_uid = promise_uid

# Remember that the function's __name__ is the task name in apply_distributable
# task_name = function.__name__

# When starting the server inside this class you must inject the binary
# manager that's tied to the class. Eg:
# Dipla.server = Server(
#     Dipla.tq,
#     Dipla.binary_manager
# )
