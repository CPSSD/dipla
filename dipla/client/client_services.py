from abc import ABC, abstractmethod, abstractstaticmethod
from base64 import b64decode


# This is an interface that all client services must implement.
class ClientService(ABC):

    # Get the label that identifies messages for this service
    @abstractstaticmethod
    def get_label():
        pass

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

    @staticmethod
    def get_label():
        return 'run_binary'

    def __init__(self, client, binary_runner):
        super().__init__(client)
        self._binary_runner = binary_runner

    def execute(self, data):
        task = data["task_instructions"]
        arguments = data["data_instructions"]

        if not hasattr(self.client, 'binary_paths'):
            raise ValueError('Client does not have any binaries')
        if task not in self.client.binary_paths:
            raise ValueError('Task "' + task + '" does not exist')

        self._binary_runner.run(self.client.binary_paths[task], arguments)


class BinaryReceiverService(ClientService):

    @staticmethod
    def get_label():
        return 'get_binary'

    def __init__(self, client, base_filepath):
        self.client = client
        self._base_filepath = base_filepath
        self.client.binary_paths = {}

    def execute(self, data):
        base64_data = data['base64_binary']
        binary_name = data['name']
        binary_path = self._base_filepath + binary_name

        self.client.binary_paths[binary_name] = binary_path

        raw_data = b64decode(base64_data)
        with open(binary_path, 'wb') as file_writer:
            file_writer.write(raw_data)
