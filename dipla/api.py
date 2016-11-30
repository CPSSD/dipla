from dipla.api_support.function_serialise import get_encoded_script
from dipla.server.server import BinaryManager

class Dipla:

    binary_mananger = BinaryManager()

    @staticmethod
    def distribute(function):
        base64_binary = get_encoded_script(function)
        #Dipla.binary_mananger.add_platform('.*', )

    @staticmethod
    def data_source(function):
        pass

    @staticmethod
    def start():
        # Start the dipla server
        pass