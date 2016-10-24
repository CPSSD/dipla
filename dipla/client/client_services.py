from abc import ABC, abstractmethod
from base64 import b64decode


# This is an interface that all client services must implement.
class ClientService(ABC):

    # Pass any dependencies of the service in through the constructor
    #
    # The first parameter should be the client, so that bi-directional
    # communication is possible. This parameter must change in the future,
    # as it introduces a circular dependency.
    @abstractmethod
    def __init__(self, client):
        pass

    # Decide what happens when the service is executed.
    #
    # The json_data will be passed into this.
    #
    # The json_data is the "data" section of the json message
    # received from the server.
    @abstractmethod
    def execute(self, json_data):
        pass


class BinaryRunnerService(ClientService):

    def __init__(self, binary_runner):
        self._binary_runner = binary_runner

    def execute(self, json_data):
        filepath = json_data["filepath"]
        arguments = json_data["arguments"]
        self._binary_runner.run(filepath, arguments)

class BinaryReceiverService(ClientService):

    def __init__(self, client, filepath):
        self.client = client
        self._filepath = filepath

    def execute(self, json_data):
        base64_data = json_data['base64_binary']
        raw_data = b64decode(base64_data)
        with open(self._filepath, 'wb') as file_writer:
            file_writer.write(raw_data)
