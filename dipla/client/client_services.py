from abc import ABC, abstractmethod


# This is an interface that all client services must implement.
class ClientService(ABC):
    
    # Pass any dependencies of the service in through the constructor
    @abstractmethod
    def __init__(self):
        pass

    # Decide what happens when the service is executed.
    # You should pass the json_data into this.
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
