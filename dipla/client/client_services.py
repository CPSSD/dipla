from abc import ABC, abstractmethod
from base64 import b64decode


# This is an interface that all client services must implement.
class ClientService(ABC):

    # Pass any dependencies of the service in through the constructor
    #
    # The first parameter should be the client, so that bi-directional
    # communication is possible. This parameter must change in the future,
    # as it introduces a circular dependency.
    #
    # Don't forget to call the superconstructor.
    def __init__(self, client):
        self._client = client

    # Decide what happens when the service is executed.
    #
    # The data field from the decoded JSON will be passed into this.
    @abstractmethod
    def execute(self, data):
        pass


class BinaryRunnerService(ClientService):

    def __init__(self, client, binary_runner):
        super().__init__(client)
        self._binary_runner = binary_runner

    def execute(self, data):
        filepath = data["filepath"]
        arguments = data["arguments"]
        self._binary_runner.run(filepath, arguments)

class BinaryReceiverService(ClientService):

    def __init__(self, client, filepath):
        self.client = client
        self._filepath = filepath

    def execute(self, data):
        base64_data = data['base64_binary']
        raw_data = b64decode(base64_data)
        with open(self._filepath, 'wb') as file_writer:
            file_writer.write(raw_data)
