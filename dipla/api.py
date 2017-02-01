from dipla.api_support.function_serialise import get_encoded_script
from dipla.server.server import BinaryManager, Server
from dipla.server.task_queue import TaskQueue, Task, DataSource, MachineType
from dipla.shared import uid_generator


class Dipla:

    # BinaryManager and TaskQueue to be injected into server.
    binary_manager = BinaryManager()
    task_queue = TaskQueue()

    # Stop reading the data source once we hit EOF
    # TODO(StefanKennedy) Set up data sources to run indefinitely.
    @staticmethod
    def complete_on_eof(streamer):
        if streamer.stream_location >= len(streamer.stream):
            return True
        return False

    @staticmethod
    def stream_not_empty(stream, location):
        return len(stream) > 0

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
            if len(source) > 0:
                return [function(source.pop(0))]
        return read_function_wrapper

    @staticmethod
    def _generate_task_id():
        return uid_generator.generate_uid(
            length=8, existing_uids=Dipla.task_queue.get_task_ids())

    @staticmethod
    def read_data_source(read_function, source):
        task_uid = Dipla._generate_task_id()
        # The Task name is only used to run binaries, which does not
        # happen when reading a data source, so we simply call this
        # 'read_data_source' as it is never used. This actually creates
        # a Task object from the provided read function, so we will add
        # it to the TaskQueue as a Server task
        read_task = Task(
            task_uid,
            'read_data_source',
            MachineType.server,
            complete_check=Dipla.complete_on_eof)
        source_uid = uid_generator.generate_uid(length=8, existing_uids=[])
        # Create a reader task that consumes the input source being read,
        # this does not move the location because consuming the values
        # will cause the read function to find new values anyway
        read_task.add_data_source(DataSource.create_source_from_iterable(
            source,
            source_uid,
            read_function,
            availability_check=Dipla.stream_not_empty,
            location_changer=lambda x, y: False))
        Dipla.task_queue.push_task(read_task)
        return Promise(task_uid)

    @staticmethod
    def get(promise):
        task_uid = Dipla._generate_task_id()

        # Get function is given a complete function so that the server
        # will terminate once it runs out of values
        get_task = Task(
            task_uid,
            'get',
            MachineType.server,
            complete_check=Dipla.complete_on_eof)
        # Generate a uid for the source (bridge) from the get task to
        # the task provided in the promise
        source_uid = uid_generator.generate_uid(length=8, existing_uids=[])
        get_task.add_data_source(DataSource.create_source_from_task(
            Dipla.task_queue.get_task(promise.task_uid), source_uid))
        Dipla.task_queue.push_task(get_task)

        server = Server(Dipla.task_queue, Dipla.binary_manager)
        server.start()

        return get_task.task_output


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
