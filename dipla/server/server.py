import re
import sys
import json
import asyncio
import websockets
import dipla.server.task_queue

from dipla.server.worker_group import WorkerGroup, Worker
from base64 import b64encode


class BinaryManager:

	def __init__(self):
		self.platform_re_list = []

	def add_platform(self, platform_re, task_list):
		# Ensure task_list a correcly formatted list of tuples containing a
		# task name string and path string.
		for task_tuple in task_list:
			assert(isinstance(task_tuple, tuple))
			task_name, binary_path = task_tuple
			assert(isinstance(task_name, str) and isinstance(binary_path, str))

		self.platform_re_list.append((re.compile(platform_re), task_list))

	def get_binaries(self, platform):
		for platform_re, task_list in self.platform_re_list:
			if platform_re.match(platform):
				return task_list
		raise KeyError('No matching binaries found for this platform')


class ServerServices:

    def __init__(self):
        # Raising an expection in these services will NOT return an error to
        # to the client, the service should add a field to the dict it returns
        # that indicates an error occured.
        self.services = {
            'get_binaries': self._handle_get_binary,
            'get_instructions': self._handle_get_instructions,
        }

    def get_service(self, label):
        if label in self.services:
            return self.services[label]
        raise KeyError("Label '{}' does not have a handler".format(label))

    def _handle_get_binary(self, message, server):
        platform = message['platform']
        try:
        	task_list = self.binary_manager.get_binaries(platform)
        except KeyError as e:
        	data = {
        		'error': str(e),
        	}
        	return data

        encoded_binaries = {}
        for task_name, path in task_list:
            with open(path, 'rb') as binary:
                binary_bytes = binary.read()
            encoded_bytes = b64encode(binary_bytes)
            encoded_binaries[task_name] = encoded_bytes.decode('utf-8')

        data = {
            'base64_binaries': encoded_binaries,
        }
        return data

    def _handle_get_instructions(self, message, server):
        data = {}
        try:
            task = server.task_queue.pop_task()
            data['task_instructions'] = task.task_instructions
            data['data_instructions'] = task.data_instructions
        except task_queue.TaskQueueEmpty as e:
            data['command'] = 'quit'
        return data


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
        user_id = self.worker_group.generate_uid(8)
        try:
            self.worker_group.add_worker(
                Worker(user_id, websocket, quality=0.5))
        except ValueError:
            # TODO(cianlr): Log something here indicating the error
            data = {'details': 'UserID already taken'}
            await self._send_message(websocket, 'general_error', data)
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
                    await self._send_message(worker.websocket,
                                             message['label'],
                                             response_data)
                except (ValueError, KeyError) as e:
                    # If there is a general error that isn't service specific
                    # then send a message with the 'general_error' label.
                    data = {'details': str(e)}
                    await self._send_message(worker.websocket,
                                             'general_error',
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
