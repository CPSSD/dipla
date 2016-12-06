from dipla.api_support.function_serialise import get_encoded_script
from dipla.server.server import BinaryManager
from dipla.server.task_queue import TaskQueue, Task


class Dipla:

    # BinaryManager to be injected into server.
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
        return function

    @staticmethod
    def apply_distributable(function, *args):
        uid = None
        task = Task(uid, function.__name__)
	for arg in args:
            pass
        task_queue.push_task(task)
        return task
        

# Remember that the function's __name__ is the task name in apply_distributable
# task_name = function.__name__

# When starting the server inside this class you must inject the binary
# manager that's tied to the class. Eg:
# Dipla.server = Server(
#     Dipla.tq,
#     Dipla.binary_manager
# )
