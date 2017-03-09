import logging
import os
from dipla.shared import message_generator
from dipla.shared.services import ServiceError
from dipla.shared.error_codes import ErrorCodes
from abc import ABC, abstractmethod, abstractstaticmethod
from base64 import b64decode


class ClientService(ABC):
    """an interface that all client services must implement."""

    @staticmethod
    @abstractmethod
    def get_label():
        """Get the label that identifies messages for this service"""

    @abstractmethod
    def execute(self, data):
        """
        This method should contain whatever 'executing' your service entails.

        :param data: a json object containing any data relevant to the service.

        :returns: Any results of the service execution.

        For example, an `AdditionService` implementation might take
        {'values': [2, 2, 3]} as the data field and return a 7.
        """


class BinaryRunnerService(ClientService):

    @staticmethod
    def get_label(): pass

    def __init__(self, binary_paths, binary_runner):
        self.__binary_paths = binary_paths
        self.__binary_runner = binary_runner

    def execute(self, data):
        task = data["task_instructions"]

        if len(self.__binary_paths) <= 0:
            raise ServiceError(ValueError('Client does not have any binaries'),
                               ErrorCodes.no_binaries_present)

        if task not in self.__binary_paths:
            raise ServiceError(KeyError('Task "' + task + '" does not exist'),
                               ErrorCodes.invalid_binary_key)

        results = self.__binary_runner.run(
            self.__binary_paths[task],
            data['arguments']
        )

        result_data = {
            'task_uid': data['task_uid'],
            'results': results
        }

        message = message_generator.generate_message(
            'binary_result', result_data)
        return message


class RunInstructionsService(BinaryRunnerService):

    @staticmethod
    def get_label():
        return 'run_instructions'

    def execute(self, data):
        result_message = super().execute(data)
        result_message['label'] = 'client_result'
        return result_message


class VerifyInputsService(BinaryRunnerService):

    @staticmethod
    def get_label():
        return 'verify_inputs'

    def execute(self, data):
        result_message = super().execute(data)
        result_message['label'] = 'verify_inputs_result'
        return result_message


class BinaryReceiverService(ClientService):

    @staticmethod
    def get_label():
        return 'get_binaries'

    def __init__(self, base_file_path, binary_paths):
        self.__base_file_path = base_file_path
        self.__binary_paths = binary_paths

    def execute(self, data):
        binaries = data['base64_binaries']
        for task_name, encoded_bin in binaries.items():
            # Decode and save each binary in the response.
            binary_path = self.__base_file_path + task_name
            self.__binary_paths[task_name] = binary_path

            raw_data = b64decode(encoded_bin)
            with open(binary_path, 'wb') as file_writer:
                file_writer.write(raw_data)
            os.chmod(binary_path, 511)

        return message_generator.generate_message("binaries_received", "")


class ServerErrorService(ClientService):

    @staticmethod
    def get_label():
        return 'runtime_error'

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def execute(self, data):
        self.logger.error('Error from server (code %d): %s' % (
            data['code'], data['details']))
