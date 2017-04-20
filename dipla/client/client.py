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
        # Set of task UIDs that have been marked as terminated by the server
        self._terminated_tasks = set()
        # A class to be used to assign a quality to this client
        if quality_scorer:
            self.quality_scorer = quality_scorer
        else:
            self.quality_scorer = QualityScorer()

    def mark_task_terminated(self, task_uid):
        self._terminated_tasks.add(task_uid)

    def is_task_terminated(self, task_uid):
        return task_uid in self._terminated_tasks

    def inject_services(self, services):
        # TODO: Refactor Client
        #
        # This method is a very hacky workaround to a circular dependency.
        #
        # This can be avoided by splitting the Client class up into smaller
        # areas of functionality. After doing that, the entire client will not
        # need to be passed into all of the ClientServices.
        self.services = services

    def _make_error_message(self, details, code):
        """Returns an error message for the server.

        details, str: the error message.
        code, int: the error code."""
        data = {
            'details': details,
            'code': code
        }
        return generate_message('runtime_error', data)

    async def _send_async(self, message):
        """Asynchronous task for sending a message to the server.

        message, dict: the message to be sent"""
        self._stats_updater.increment('requests_resolved')
        if not message:
            return
        if not ('label' in message and 'data' in message):
            raise ValueError(
                'Missing label or data field in message %s.' % message)

        self._stats_updater.increment('messages_sent')
        LogUtils.debug('Sending message: %s.' % message)
        await self.websocket.send(json.dumps(message))

    async def _sending_callback(self, future):
        """A method that acts almost as a callback, waiting for a future to
        be ready and then sending its result."""
        await asyncio.wait_for(future, None)
        await self._send_async(future.result())

    async def receive_loop(self):
        """Task for handling messages received from server and
        sending replies."""
        try:
            loop = asyncio.get_event_loop()
            while True:
                message = await self.websocket.recv()
                task_future = loop.run_in_executor(
                    None, self._safe_handle, message)
                asyncio.ensure_future(self._sending_callback(task_future))
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

        # Return the final message, if result_message is None then nothing is
        # sent back to the server.
        self._stats_updater.increment('tasks_done')
        return result_message

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
            'password': password,
        }
        asyncio.ensure_future(
            self._send_async(generate_message('get_binaries', data)))

        self._stats_updater.overwrite('running', True)
        loop.run_until_complete(receive_task)
