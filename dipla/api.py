from dipla.api_support.function_serialise import get_encoded_script
from dipla.server.server import Server, BinaryManager

class Dipla:

    # BinaryManager to be injected into server.
    binary_manager = BinaryManager()

    # Server instance.
    server = None

    @staticmethod
    def distribute(function):
        base64_binary = get_encoded_script(function)
        Dipla.binary_manager.add_encoded_binaries('.*', [
            (function.__name__, base64_binary),
        ])

    @staticmethod
    def data_source(function):
        pass

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
