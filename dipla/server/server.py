import re
import sys
import json
import asyncio
import websockets
import dipla.server.task_queue

from dipla.server.worker_group import WorkerGroup, Worker
from dipla.shared.services import ServiceError
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
        full_task_list = []
        for platform_re, task_list in self.platform_re_list:
            if platform_re.match(platform):
                full_task_list.extend(task_list)

        if full_task_list:
            return full_task_list
        raise KeyError('No matching binaries found for this platform')


class ServerServices:

    def __init__(self):
        # Raising an exception will transmit it back to the client. A
        # ServiceError lets you include a specific error code to allow
        # the client to better choose what to do with it.
        self.services = {
            'get_binaries': self._handle_get_binaries,
            'get_instructions': self._handle_get_instructions,
            'client_result': self._handle_client_result,
            'runtime_error': self._handle_runtime_error,
        }

    def get_service(self, label):
        if label in self.services:
            return self.services[label]
        raise KeyError("Label '{}' does not have a handler".format(label))

    def _handle_get_binaries(self, message, server):
        platform = message['platform']
        try:
            encoded_binaries = server.binary_manager.get_binaries(platform)
        except KeyError as e:
            raise ServiceError(e, 2)

        data = {
            'base64_binaries': dict(encoded_binaries),
        }
        return data

    def _handle_get_instructions(self, message, server):
        data = {}
        try:
            task = server.task_queue.pop_task()
            data['task_instructions'] = task.task_instructions
            data['data_instructions'] = json.dumps(
                {d.name: d.get_value() for d in task.data_instructions})
        except task_queue.TaskQueueEmpty as e:
            data['command'] = 'quit'
        return data

    def _handle_client_result(self, message, server):
        data_type = message['type']
        value = message['value']
        print('New client result of type "%s": %s' % (data_type, value))
        server.task_queue.add_new_data(data_type, value)
        return None

    def _handle_runtime_error(self, message, server):
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
        try:
            self.worker_group.add_worker(
                Worker(user_id, websocket, quality=0.5))
        except ValueError:
            # TODO(cianlr): Log something here indicating the error
            data = {'details': 'UserID already taken', 'code': 0}
            await self._send_message(websocket, 'runtime_error', data)
            return
        # This is kind of unusual, we add a new worker to the group and
        # then pull out whatever is at the top of the group and repurpose
        # the thread to handle that worker, but it works for now.
        worker = self.worker_group.lease_worker()
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
                    response_data = service(message['data'], self)
                    if response_data is None:
                        continue
                    await self._send_message(worker.websocket,
                                             message['label'],
                                             response_data)
                except (ValueError, KeyError) as e:
                    # If there is a general error that isn't service specific
                    # then send a message with the 'runtime_error' label.
                    data = {
                        'details': 'Error during websocket loop: %s' % str(e),
                        'code': 1,
                    }
                    await self._send_message(worker.websocket,
                                             'runtime_error',
                                             data)
                except ServiceError as e:
                    # This error has a specific code to transmit attached to it
                    data = {'details': str(e), 'code': e.code}
                    await self._send_message(worker.websocket,
                                             'runtime_error',
                                             data)
        except websockets.exceptions.ConnectionClosed as e:
            print(worker.uid + " has closed the connection")
        finally:
            self.worker_group.return_worker(worker.uid)
            self.worker_group.remove_worker(worker.uid)

    def _decode_message(self, message):
        message_dict = json.loads(message)
        if 'label' not in message_dict or 'data' not in message_dict:
            raise ValueError('Message missing "label" or "data": {}'.format(
                str(message_dict)))
        return message_dict

    async def _send_message(self, socket, label, data):
        response = {
            'label': label,
            'data': data,
        }
        await socket.send(json.dumps(response))

    def start(self):
        start_server = websockets.serve(
            self.websocket_handler,
            "localhost",
            8765)

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
