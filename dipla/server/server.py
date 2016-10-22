import sys
import json
import asyncio
import websockets

from base64 import b64encode


class ServerServices:

    def __init__(self):
        self.services = {
            'get_binary': self._handle_get_binary,
            'get_data_instructions': self._handle_get_data_instructions,
        }

    def get_service(self, label):
        if label in self.services:
            return self.services[label]
        return None

    def _handle_get_binary(self, message):
        # TODO(cianlr): Get data from the `message` to decide which platform
        # to send a binary for
        path = self.binary_paths['win32']
        with open(path, 'rb') as binary:
            binary_bytes = binary.read()

        encoded_bytes = b64encode(binary_bytes)
        return encoded_bytes.decode('utf-8')

    def _handle_get_data_instructions(self, message):
        return self.task_queue.pop_task().data_instructions


class Server:

    def __init__(self, task_queue, binary_paths, services=None):
        """
        task_queue is a TaskQueue object that tasks to be run are taken from

        binary_paths is a dictionary where the keys are the architecures and
        the values are the paths to the binaries to run on those platforms.
        E.g. {'win32':'/binaries/win_bin.exe'}

        services is an instance of ServerServices that is used to lookup
        functions for handling client requests. If this is not provided a
        default instance is used.
        """
        self.task_queue = task_queue
        self.connected = {}
        self.binary_paths = binary_paths
        self.services = services if services else ServerServices()

    async def _reject_user(self, user_id, websocket):
        # TODO(cianlr): Log something here indicating the error
        # TODO(cianlr): Send this in a standard format
        await websocket.send("Sorry, this User ID is taken")

    async def _process_user(self, user_id, websocket):
        self.connected[user_id] = websocket
        try:
            # recv() raises a ConnectionClosed exception when the client
            # disconnects, which breaks out of the while True loop.
            while True:
                message = await websocket.recv()
                # TODO(cianlr): Parse the message into some format rather than
                # taking as a string (to allow other params to be included in
                # the request)
                response = {
                    'status': 'ok',
                    'data': {},
                }
                # TODO(cianlr): Error handling
                service = self.services.get_service(message)
                if not service:
                    response['status'] = 'error'
                else:
                    response['data'] = service(message)
                await websocket.send(json.dumps(response))

        except websockets.exceptions.ConnectionClosed:
            print(user_id + " has closed the connection")
        finally:
            self.connected.pop(user_id, None)

    async def websocket_handler(self, websocket, path):
        user_id = path[1:]
        if user_id not in self.connected:
            self._process_user(user_id, websocket)
        else:
            self._reject_user(user_id, websocket)

    def start(self):
        start_server = websockets.serve(
                self.websocket_handler,
                "localhost",
                8765)

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
