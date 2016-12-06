import asyncio
import websockets
import json
import threading
import time
import logging
import os

from dipla.client.quality_test import QualityTest
from dipla.shared.services import ServiceError
from dipla.shared.message_generator import generate_message


class Client(object):

    def __init__(self, server_address, quality_test=None):
        """Create the client.

        server_address, string: The address of the websocket server to
            connect to, eg. 'ws://localhost:8765'."""
        self.server_address = server_address
        self.logger = logging.getLogger(__name__)
        # the number of times to try to connect before giving up
        self.connect_tries_limit = 8
        # A class to be used to assign a quality to this client
        self.quality_test = quality_test if quality_test else QualityTest()

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

    def send(self, message):
        """Send a message to the server.

        message, dict: the message to be sent, a dict with a 'label' field
            and a 'data' field"""
        if not ('label' in message and 'data' in message):
            raise ValueError(
                'Missing label or data field in message %s.' % message)

        self.logger.debug('Sending message: %s.' % message)
        json_message = json.dumps(message)

        # run the coroutine to send the message
        asyncio.ensure_future(self._send_async(json_message))

    def send_error(self, details, code):
        """Send an error to the server.

        details, str: the error message.
        code, int: the error code."""
        data = {
            'details': details,
            'code': code
        }
        message = generate_message('runtime_error', data)
        self.send(message)

    async def _send_async(self, message):
        """Asynchronous task for sending a message to the server.

        message, string: the message to be sent"""
        await self.websocket.send(message)

    async def receive_loop(self):
        """Task for handling messages received from server"""
        try:
            while True:
                self.logger.warning('iter')
                message = await self.websocket.recv()
                try:
                    self._handle(message)
                except ServiceError as e:
                    self.send_error(str(e), e.code)
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("Connection closed.")

    def _handle(self, raw_message):
        """Do something with a message received from the server.

        raw_message, string: the raw data received from the server."""
        self.logger.debug("Received: %s." % raw_message)
        message = json.loads(raw_message)
        if not ('label' in message and 'data' in message):
            raise ServiceError('Missing field from message: %s' % message, 4)

        result_message = self._run_service(message["label"], message["data"])
        if result_message is not None:
            # send the client_result back to the server
            self.send(result_message)

    def _run_service(self, label, data):
        try:
            service = self.services[label]
        except KeyError:
            error_message = "Failed to find service: {}".format(label)
            self.logger.error(error_message)
            raise ServiceError(error_message, 5)
        return service.execute(data)

    async def _start_websocket(self):
        """Run the loop receiving websocket messages. Makes use of
        exponential backoff when trying to connect, waiting for longer
        times each trial before giving up after self.connect_tries_limit
        times."""
        num_tries = 0
        backoff = 1
        while num_tries < self.connect_tries_limit:
            self.logger.warning(
                'trying connection %d/%d' % (num_tries,
                                             self.connect_tries_limit))
            try:
                return await websockets.connect(self.server_address)
            except:
                num_tries += 1
                time.sleep(backoff)
                backoff *= 2
        return None

    def _get_platform(self):
        """Get some information about the platform the client is running on."""
        if os.name == 'posix':
            return ''.join(os.uname())
        # TODO(ndonn): Add better info for Windows and Mac versions
        return os.name

    def _get_quality(self):
        return self.quality_test.get_quality()

    def start(self):
        """Send the get_binary message, and start the communication loop
        in a new thread."""
        loop = asyncio.get_event_loop()
        self.websocket = loop.run_until_complete(self._start_websocket())
        if not self.websocket:
            self.logger.error(
                'Could not connect to server after %d tries' %
                self.connect_tries_limit)
            return
        receive_task = asyncio.ensure_future(self.receive_loop())
        data = {
            'platform': self._get_platform(),
            'quality': self._get_quality(),
        }
        self.send(generate_message('get_binaries', data))

        loop.run_until_complete(receive_task)
        self.start()
