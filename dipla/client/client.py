import asyncio
import websockets
import json
import threading
import logging
import os

from dipla.shared.services import ServiceError

class Client(object):

    def __init__(self, server_address):
        """Create the client.

        server_address, string: The address of the websocket server to
            connect to, eg. 'ws://localhost:8765'."""
        self.server_address = server_address
        self.logger = logging.getLogger(__name__)

    def inject_services(self, services):
        # TODO: Refactor Client
        #
        # This method is a very hacky workaround to a circular dependency.
        #
        # This can be avoided by splitting the Client class up into smaller
        # areas of functionality. After doing that, the entire client will not
        # need to be passed into all of the ClientServices.
        self.services = services

    def get_logger(self):
        return self.logger

    def send(self, message, websocket):
        """Send a message to the server.

        message, dict: the message to be sent, a dict with a 'label' field
            and a 'data' field.
        websocket, websockets.websocket: this client's websocket connected
            to the server"""
        if not ('label' in message and 'data' in message):
            raise ValueError(
                'Missing label or data field in message %s.' % message)

        self.logger.debug('Sending message: %s.' % message)
        json_message = json.dumps(message)

        # run the coroutine to send the message
        asyncio.ensure_future(self._send_async(websocket, json_message))

    def send_error(self, details, code, websocket):
        """Send an error to the server.

        details, str: the error message.
        code, int: the error code.
        websocket, websockets.websocket: this client's websocket connected
            to the server"""
        message = {
            'label': 'runtime_error',
            'data': {
                'details': details,
                'code': code,
            }
        }
        self.send(message, websocket)

    async def _send_async(self, websocket, message):
        """Asynchronous task for sending a message to the server.

        websocket, websockets.websocket: this client's websocket connected
            to the server
        message, string: the message to be sent"""
        await websocket.send(message)

    async def receive_loop(self, websocket):
        """Task for handling messages received from server

        websocket, websockets.websocket: this client's websocket connected
            to the server"""
        try:
            while True:
                message = await websocket.recv()
                try:
                    self._handle(message)
                except ServiceError as e:
                    self.send_error(str(e), e.code, websocket)
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("Connection closed.")

    def _handle(self, raw_message):
        """Do something with a message received from the server.

        raw_message, string: the raw data received from the server."""
        self.logger.debug("Received: %s." % raw_message)
        message = json.loads(raw_message)
        if not ('label' in message and 'data' in message):
            raise ServiceError('Missing field from message: %s' % message,
                4)
        self._run_service(message["label"], message["data"])

    def _run_service(self, label, data):
        try:
            service = self.services[label]
            service.execute(data)
        except KeyError:
            self.logger.error("Failed to find service: {}".format(label))
            raise ServiceError('Failed to find service: {}'.format(label), 5)

    async def _start_websocket(self):
        """Run the loop receiving websocket messages."""
        return await websockets.connect(self.server_address)

    def _get_platform(self):
        """Get some information about the platform the client is running on."""
        if os.name == 'posix':
            return ''.join(os.uname())
        # TODO(ndonn): Add better info for Windows and Mac versions
        return os.name

    def start(self):
        """Send the get_binary message, and start the communication loop
        in a new thread."""
        loop = asyncio.get_event_loop()
        websocket = loop.run_until_complete(self._start_websocket())

        asyncio.ensure_future(self.receive_loop(websocket))
        self.send({
            'label': 'get_binaries',
            'data': {
                 'platform': self._get_platform()}},
            websocket)

        loop.run_forever()
