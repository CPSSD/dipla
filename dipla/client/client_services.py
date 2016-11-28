import logging
import os
from dipla.shared import message_generator

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
        return 'get_instructions'

    def __init__(self, client, binary_runner):
        super().__init__(client)
        self._binary_runner = binary_runner

    def execute(self, data):
        task = data["task_instructions"]

        if not hasattr(self._client, 'binary_paths'):
            raise ValueError('Client does not have any binaries')
        if task not in self._client.binary_paths:
            raise ValueError('Task "' + task + '" does not exist')

        results = []
        for input_value in data['data']:
            results.append(self._binary_runner.run(
                    self._client.binary_paths[task], str(input_value)))
        data = {
                'task_id' : task,
                'results' : results
            }

        message = message_generator.generate_message('client_result', data)
        return message


class BinaryReceiverService(ClientService):

    @staticmethod
    def get_label():
        return 'get_binaries'

    def __init__(self, client, base_filepath):
        self.client = client
        self._base_filepath = base_filepath
        self.client.binary_paths = {}

    def execute(self, data):
        binaries = data['base64_binaries']
        for task_name, encoded_bin in binaries.items():
            # Decode and save each binary in the response.
            binary_path = self._base_filepath + task_name
            self.client.binary_paths[task_name] = binary_path

            raw_data = b64decode(encoded_bin)
            with open(binary_path, 'wb') as file_writer:
                file_writer.write(raw_data)
            os.chmod(binary_path, 511)

        return message_generator.generate_message(
            "get_instructions", "")


class ServerErrorService(ClientService):

    @staticmethod
    def get_label():
        return 'runtime_error'

    def __init__(self, client):
        super().__init__(client)
        self.logger = logging.getLogger(__name__)

    def execute(self, data):
        self.logger.error('Error from server (code %d): %s' % (
            data['code'], data['details']))
        return None
