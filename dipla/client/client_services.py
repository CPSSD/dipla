from abc import ABC, abstractmethod


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
    # The json_data will be passed into this.
    #
    # The json_data is the "data" section of the json message
    # received from the server.
    @abstractmethod
    def execute(self, json_data):
        pass


class BinaryRunnerService(ClientService):

    def __init__(self, client, binary_runner):
        super().__init__(client)
        self._binary_runner = binary_runner

    def execute(self, json_data):
        filepath = json_data["filepath"]
        arguments = json_data["arguments"]
        self._binary_runner.run(filepath, arguments)
