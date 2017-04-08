import asyncio
import websockets
import json
import threading
import time
import os

from dipla.client.quality_scorer import QualityScorer
from dipla.shared.services import ServiceError
from dipla.shared.message_generator import generate_message
from dipla.shared.logutils import LogUtils


class Client(object):

    def __init__(self, quality_scorer=None, stats=None):
        """Create the client."""
        self._stats_updater = stats
        # the number of times to try to connect before giving up
        self.connect_tries_limit = 8
        # A class to be used to assign a quality to this client
        if quality_scorer:
            self.quality_scorer = quality_scorer
        else:
            self.quality_scorer = QualityScorer()

    def inject_services(self, services):
        # TODO: Refactor Client
        #
        # This method is a very hacky workaround to a circular dependency.
        #
        # This can be avoided by splitting the Client class up into smaller
        # areas of functionality. After doing that, the entire client will not
        # need to be passed into all of the ClientServices.
        self.services = services

    def _json_message(self, message):
        """Send a message to the server.

        message, dict: the message to be sent, a dict with a 'label' field
            and a 'data' field"""
        if not ('label' in message and 'data' in message):
            raise ValueError(
                'Missing label or data field in message %s.' % message)

        LogUtils.debug('Sending message: %s.' % message)
        json_message = json.dumps(message)

        # run the coroutine to send the message
        self._stats_updater.increment('messages_sent')
        return json_message

    def _make_error_message(self, details, code):
        """Send an error to the server.

        details, str: the error message.
        code, int: the error code."""
        data = {
            'details': details,
            'code': code
        }
        message = generate_message('runtime_error', data)
        return self._json_message(message)

    async def _send_async(self, message):
        """Asynchronous task for sending a message to the server.

        message, string: the message to be sent"""
        await self.websocket.send(message)

    async def receive_loop(self):
        """Task for handling messages received from server."""
        try:
            while True:
                message = await self.websocket.recv()
                resp = self._safe_handle(message)
                if resp:
                    await self._send_async(resp)
                self._stats_updater.increment('requests_resolved')
        except websockets.exceptions.ConnectionClosed:
            LogUtils.warning("Connection closed.")

    def _safe_handle(self, raw_message):
        try:
            return self._handle(raw_message)
        except ServiceError as e:
            return self._make_error_message(str(e), e.code)

    def _handle(self, raw_message):
        """Do something with a message received from the server.

        raw_message, string: the raw data received from the server."""
        LogUtils.debug("Received: %s." % raw_message)
        message = json.loads(raw_message)
        if not ('label' in message and 'data' in message):
            raise ServiceError('Missing field from message: %s' % message, 4)

        started_processing_at = time.time()

        result_message = self._run_service(message["label"], message["data"])

        finished_processing_at = time.time()
        time_taken_to_process = finished_processing_at - started_processing_at
        self._stats_updater.adjust('processing_time', time_taken_to_process)

        self._stats_updater.increment('tasks_done')
        if result_message is not None:
            # send the client_result back to the server
            return self._json_message(result_message)
        return None

    def _run_service(self, label, data):
        try:
            service = self.services[label]
        except KeyError as e:
            error_message = "Failed to find service: {}".format(label)
            LogUtils.error(error_message, e)
            raise ServiceError(error_message, 5)
        return service.execute(data)

    async def _start_websocket(self, server_address):
        """Run the loop receiving websocket messages. Makes use of
        exponential backoff when trying to connect, waiting for longer
        times each trial before giving up after self.connect_tries_limit
        times."""
        num_tries = 0
        backoff = 1
        while num_tries < self.connect_tries_limit:
            LogUtils.warning(
                'trying connection %d/%d' % (num_tries,
                                             self.connect_tries_limit))
            try:
                return await websockets.connect(server_address)
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
        return self.quality_scorer.get_quality()

    def start(self, server_address, password=''):
        """Send the get_binary message, and start the communication loop
        in a new thread."""
        loop = asyncio.get_event_loop()
        self.websocket = loop.run_until_complete(
            self._start_websocket(server_address))
        if not self.websocket:
            LogUtils.error(
                'Could not connect to server after %d tries' %
                self.connect_tries_limit)
            return

        receive_task = asyncio.ensure_future(self.receive_loop())

        data = {
            'platform': self._get_platform(),
            'quality': self._get_quality(),
        }
        if password != '':
            data['password'] = password
        get_binaries_future = asyncio.ensure_future(
            self._send_async(
                self._json_message(generate_message('get_binaries', data))))

        self._stats_updater.overwrite('running', True)
        loop.run_until_complete(receive_task)
