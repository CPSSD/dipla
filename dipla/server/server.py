import re
import sys
import json
import asyncio
import websockets
import random

from datetime import datetime
from dipla.server.task_queue import MachineType
from dipla.server.worker_group import WorkerGroup, Worker
from dipla.server.server_services import ServerServices, ServiceParams
from dipla.shared.services import ServiceError
from dipla.shared.message_generator import generate_message
from dipla.shared.error_codes import ErrorCodes
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


class Server:

    def __init__(self,
                 task_queue,
                 services,
                 result_verifier,
                 worker_group=None,
                 stats=None):
        """
        task_queue is a TaskQueue object that tasks to be run are taken from

        binary_manager is an instance of BinaryManager to be used to source
        task binaries

        worker_group is the WorkerGroup class used to manage and sort workers

        services is an instance of ServerServices that is used to lookup
        functions for handling client requests. If this is not provided a
        default instance is used.

        stats is an instance of shared.statistics.StatisticsUpdater,
        used to update information on the current runtime status of the
        project.

        This constructor creates variables used in verifying inputs,
        where whether or not verification is performed is decided
        probabilistically using the verify_probability ratio

        verify_inputs is a dictionary of inputs with an array as the
        value, indexed by `{worker.uid}-{task_uid}` of the worker and
        task that they are the inputs for, that store the inputs that
        will be verified once the actual answers have been obtained
        """
        self.task_queue = task_queue
        self.services = services
        self.result_verifier = result_verifier

        self.worker_group = worker_group
        self.min_worker_correctness = 0.99
        if not self.worker_group:
            self.worker_group = WorkerGroup(stats)

        self.__statistics_updater = stats

        self.verify_probability = 0.5
        self.verify_inputs = {}

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
                        'code': ErrorCodes.server_websocket_loop,
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

    def _get_distributable_task_input(self):
        """
        Used to get the next task input for either distributing to
        clients or running on the server. This will consider whether
        there are any available workers, and if not will only get server
        side tasks. This is an implementation detail of at least the
        distribute_tasks method.
        """
        if not self.worker_group.has_available_worker():
            if self.task_queue.has_next_input(MachineType.server):
                return self.task_queue.pop_task_input(MachineType.server)
            return None
        return self.task_queue.pop_task_input()

    def _add_verify_input_data(self, inputs, task_instr, worker_id, task_id):
        self.verify_inputs[worker_id + "-" + task_id] = {
            "task_instructions": task_instr,
            "inputs": inputs,
            "original_worker_uid": worker_id
        }

    def distribute_tasks(self):
        # By leasing workers without specifying an id, we get the
        # highest quality worker for the task
        while self.task_queue.has_next_input():
            # If workers are connected pop any kind of task input. If no
            # workers are connected we must only get server task input

            task_input = self._get_distributable_task_input()
            if task_input is None:  # Happens when no input can be used
                break

            if task_input.machine_type == MachineType.client:
                task_instructions = task_input.task_instructions
                # Create the message and send it
                data = {}
                data['task_instructions'] = task_instructions
                data['task_uid'] = task_input.task_uid
                data['arguments'] = task_input.values
                # TODO(Update the documentation with this)
                worker = self.worker_group.lease_worker()
                worker.current_task_instr = task_instructions
                self.send(worker.websocket, 'run_instructions', data)

                if self.result_verifier.has_verifier(task_instructions):
                    # Store the inputs to be verified with the results later
                    worker.last_inputs = task_input.values

                if(random.random() < self.verify_probability):
                    # This stores the input values in the worker and also in
                    # the server's verify_inputs dict. HOWEVER, only one copy
                    # of the data is actually stored in memory because
                    # verify_inputs only has a reference to worker.last_inputs.
                    #
                    # This can be seen with:
                    # assert(worker.last_inputs is inner_dict_thing['inputs'])
                    worker.last_inputs = task_input.values
                    self._add_verify_input_data(
                        worker.last_inputs,
                        worker.current_task_instr,
                        worker.uid,
                        task_input.task_uid)
            elif task_input.machine_type == MachineType.server:
                # Server side tasks do not have any maching binaries, so
                # we skip the send-to-client stage and move the read
                # data straight to the results. All server side tasks
                # have one argument, so extract the values for that lone
                # argument
                task_values = task_input.values[0]
                for result in task_values:
                    self.task_queue.add_result(task_input.task_uid, result)

            if self.task_queue.is_inactive():
                # Kill the server
                # TODO(cianlr): This kills things unceremoniously, there may be
                # a better way.
                asyncio.get_event_loop().stop()

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

    def start(self, address='0.0.0.0', port=8765, password=None):
        self.__statistics_updater.overwrite("start_time",
                                            datetime.utcnow().isoformat())
        server = websockets.serve(
            self.websocket_handler,
            address,
            port)
        self.password = password

        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().call_soon(self.distribute_tasks)
        asyncio.get_event_loop().run_forever()
