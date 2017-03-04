import re
import json
import asyncio
import websockets
import random
from dipla.server.task_queue import MachineType
from dipla.server.worker_group import Worker
from dipla.shared.services import ServiceError
from dipla.shared.message_generator import generate_message
from base64 import b64encode
from dipla.shared.network.network_connection import EventListener


class BinaryManager:

    def __init__(self):
        self.platform_re_list = []

    def add_binary_paths(self, platform_re, task_list):
        # Ensure task_list is a correcly formatted list of tuples containing a
        # task name string and path string.
        self._check_task_list(task_list)
        b64_binaries = []
        for task_name, binary_path in task_list:
            with open(binary_path, 'rb') as binary:
                # Read the bytes of the binary and base64 encode them.
                binary_b64_bytes = b64encode(binary.read())
                # Turn the bytes of the base64 into a UTF-8 string.
                b64_binaries.append(
                    (task_name, binary_b64_bytes.decode('UTF-8')))

        self.platform_re_list.append((re.compile(platform_re), b64_binaries))

    def add_encoded_binaries(self, platform_re, task_list):
        self._check_task_list(task_list)
        self.platform_re_list.append((re.compile(platform_re), task_list))

    def _check_task_list(self, task_list):
        for task_tuple in task_list:
            if not isinstance(task_tuple, tuple):
                raise ValueError('task_list must be a list of tuples.')
            task_name, path_or_bin = task_tuple
            if not isinstance(task_name, str):
                raise ValueError(
                    'The first element of each tuple must be a string.')
            if not isinstance(path_or_bin, str):
                raise ValueError(
                    'The second element of each tuple must be a string.')

    def get_binaries(self, platform):
        """
        Get's all the binaries with regexes that match the given platform.

        If multiple tasks match then it returns all of them, this allows
        generic binaries to be mixed with platform specific ones.
        """
        full_task_list = []
        for platform_re, task_list in self.platform_re_list:
            if platform_re.match(platform):
                full_task_list.extend(task_list)

        if full_task_list:
            return full_task_list
        raise KeyError('No matching binaries found for this platform')


class Server:

    def __init__(self, task_queue, services, worker_group, stats, password):

        self.__task_queue = task_queue
        self.__services = services
        self.__worker_group = worker_group
        self.__password = password

        self.__min_worker_correctness = 0.99

    def _get_distributable_task_input(self):
        """
        Gets the next task input. If there are no available workers, it will
        only get server side tasks. This is an implementation detail of at
        least the distribute_tasks method. (Which should be extracted later)
        """

        if not self.__worker_group.has_available_worker():
            if self.__task_queue.has_next_input(MachineType.server):
                return self.__task_queue.pop_task_input(MachineType.server)
            return None
        return self.__task_queue.pop_task_input()

    def distribute_tasks(self):

        while self.__task_queue.has_next_input():

            # TaskDistributor stuff extracted...

            if self.__task_queue.is_inactive():
                # Kill the server
                # TODO(cianlr): This kills things unceremoniously, there may be
                # a better way.
                asyncio.get_event_loop().stop()

    def start(self):
        pass

        """start serving connections"""
        self.__server_connection_provider.start()

        """start distributing the tasks"""
        asyncio.get_event_loop().call_soon(self.distribute_tasks)

        """run forever"""
        asyncio.get_event_loop().run_forever()


class ServerEventListener(EventListener):

    def __init__(self, worker_factory, worker_group, services):
        self.__worker_factory = worker_factory
        self.__worker_group = worker_group
        self.__services = services

        self.__service = None
        self.__worker = None
        self.__worker_uid = None

    def on_open(self, connection, message_object):
        self.__create_worker(connection)
        self.__add_worker_to_worker_group()

    def on_close(self, connection, reason):
        self.__worker_group.remove_worker(self.__worker_uid)

    def on_error(self, connection, error):
        pass

    def on_message(self, connection, message_object):
        self.__fetch_service(message_object)
        self.__run_service(connection, message_object)
        self.__send_result_back(connection)

    def __create_worker(self, connection):
        self.__worker_uid = self.__worker_group.generate_uid()
        self.__worker = self.__worker_factory.create_from(self.__worker_uid,
                                                          connection)

    def __add_worker_to_worker_group(self):
        self.__worker_group.add_worker(self.__worker)

    def __fetch_service(self, message_object):
        service_name = message_object['label']
        self.__service = self.__services[service_name]

    def __run_service(self, connection, message_object):
        service_data = message_object['data']
        self.__service_result = run_service(self.__service,
                                            service_data,
                                            connection)

    def __send_result_back(self, connection):
        if self.__service_result is not None:
            connection.send(self.__service_result)


def run_service(service, service_data, connection):
    try:
        return service(service_data)
    except ServiceError as service_error:
        data = {'details': str(service_error), 'code': service_error.code}
        error_message_object = generate_message('runtime_error', data)
        connection.send(error_message_object)
