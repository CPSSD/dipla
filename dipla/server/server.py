import re
import sys
import json
import asyncio
import websockets
import dipla.server.task_queue

from dipla.server.worker_group import WorkerGroup, Worker
from dipla.shared.services import ServiceError
from dipla.shared.message_generator import generate_message
from base64 import b64encode


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


class ServiceParams:

    def __init__(self, server, worker):
        self.server = server
        self.worker = worker


class ServerServices:

    def __init__(self):
        """
        Raising an exception will transmit it back to the client. A
        ServiceError lets you include a specific error code to allow
        the client to better choose what to do with it.

        The services provided here expect a data object of type
        ServiceParams that carry the server that is calling the service
        as well as the worker that owns the websocket that called the
        service
        """
        self.services = {
            'get_binaries': self._handle_get_binaries,
            'binaries_received': self._handle_binary_received,
            'client_result': self._handle_client_result,
            'runtime_error': self._handle_runtime_error,
        }

    def get_service(self, label):
        if label in self.services:
            return self.services[label]
        raise KeyError("Label '{}' does not have a handler".format(label))

    def _handle_get_binaries(self, message, params):
        params.worker.set_quality(message['quality'])
        platform = message['platform']
        try:
            encoded_binaries = server.binary_manager.get_binaries(platform)
        except KeyError as e:
            raise ServiceError(e, 2)

        data = {
            'base64_binaries': dict(encoded_binaries),
        }
        return data

    def _handle_binary_received(self, message, params):
        # Worker has downloaded binary and is ready to do tasks
        try:
            params.server.worker_group.add_worker(params.worker)
        except ValueError:
            # TODO(cianlr): Log something here indicating the error
            data = {'details': 'UserID already taken', 'code': 0}
            params.server.send(websocket, 'runtime_error', data)
            return None
        # If there was extra tasks that no others could do, try and
        # assign it to this worker, as it should be the only ready one
        # If there are other workers it is okay to distribute tasks to
        # them too
        params.server.distribute_tasks()
        return None

    def _handle_client_result(self, message, params):
        task_id = message['task_uid']
        results = message['results']
        server = params.server
        for result in results:
            server.task_queue.add_result(task_id, result)
        server.worker_group.return_worker(params.worker.uid)
        server.distribute_tasks()
        return None

    def _handle_runtime_error(self, message, params):
        print('Client had an error (code %d): %s' % (message['code'],
                                                     message['details']))
        return None


class Server:

    def __init__(self,
                 task_queue,
                 binary_manager,
                 worker_group=None,
                 services=None):
        """
        task_queue is a TaskQueue object that tasks to be run are taken from

        binary_manager is an instance of BinaryManager to be used to source
        task binaries

        worker_group is the WorkerGroup class used to manage and sort workers

        services is an instance of ServerServices that is used to lookup
        functions for handling client requests. If this is not provided a
        default instance is used.
        """
        self.task_queue = task_queue
        self.binary_manager = binary_manager

        self.worker_group = worker_group
        if not self.worker_group:
            self.worker_group = WorkerGroup()

        self.services = services
        if not self.services:
            self.services = ServerServices()

    async def websocket_handler(self, websocket, path):
        user_id = self.worker_group.generate_uid()
        worker = Worker(user_id, websocket)
        try:
            # recv() raises a ConnectionClosed exception when the client
            # disconnects, which breaks out of the while True loop.
            while True:
                try:
                    # Parse the message, get the corresponding service, send
                    # back the response.
                    message = self._decode_message(
                        await worker.websocket.recv())
                    service = self.services.get_service(message['label'])
                    response_data = service(
                        message['data'], params=ServiceParams(self, worker))
                    if response_data is None:
                        continue
                    self.send(
                        worker.websocket, message['label'], response_data)
                except (ValueError, KeyError) as e:
                    # If there is a general error that isn't service specific
                    # then send a message with the 'runtime_error' label.
                    data = {
                        'details': 'Error during websocket loop: %s' % str(e),
                        'code': 1,
                    }
                    self.send(worker.websocket, 'runtime_error', data)
                except ServiceError as e:
                    # This error has a specific code to transmit attached to it
                    data = {'details': str(e), 'code': e.code}
                    self.send(worker.websocket, 'runtime_error', data)
        except websockets.exceptions.ConnectionClosed as e:
            print(worker.uid + " has closed the connection")
        finally:
            if worker.uid in self.worker_group.worker_uids():
                self.worker_group.remove_worker(worker.uid)

    def distribute_tasks(self):
        # By leasing workers without specifying an id, we get the
        # highest quality worker for the task
        while self.worker_group.has_available_worker():
            if not self.task_queue.has_next_input():
                break

            task_input = self.task_queue.pop_task_input()

            # Create the message and send it
            data = {}
            data['task_instructions'] = task_input.task_instructions
            data['task_uid'] = task_input.task_uid
            data['arguments'] = task_input.values
            # TODO(Update the documentation with this)
            worker = self.worker_group.lease_worker()
            self.send(worker.websocket, 'run_instructions', data)

    def _decode_message(self, message):
        message_dict = json.loads(message)
        if 'label' not in message_dict or 'data' not in message_dict:
            raise ValueError('Message missing "label" or "data": {}'.format(
                str(message_dict)))
        return message_dict

    async def _send_message(self, socket, label, data):
        message = generate_message(label, data)
        await socket.send(json.dumps(message))

    def send(self, socket, label, data):
        asyncio.ensure_future(self._send_message(socket, label, data))

    def start(self):
        start_server = websockets.serve(
            self.websocket_handler,
            "localhost",
            8765)

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
