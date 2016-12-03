from dipla.api_support.function_serialise import get_encoded_script
from dipla.server.server import Server, BinaryManager


class Dipla:

    # BinaryManager to be injected into server.
    binary_manager = BinaryManager()

    # Server instance.
    server = None

    @staticmethod
    def distribute(function):
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
        pass

    @staticmethod
    def apply_distributable(function, stream):
        task_name = function.__name__

    @staticmethod
    def start():
        # Start the dipla server

        # This comment is included to illustrate how I expect the start() to
        # look, the final implementation may vary.
        # Dipla.server = Server(
        #     Dipla.tq,
        #     Dipla.binary_manager
        # )
        # Dipla.server.start()
        pass
