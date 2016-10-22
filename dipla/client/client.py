#!/usr/bin/env python

import asyncio
import websockets
import json
import threading
from logging import FileHandler
from queue import Queue
from dipla.shared import logutils


class Client(object):

    def __init__(self, address, logfile_handler=FileHandler('DIPLA.log')):
        """Create the client.

        address, string: The address of the websocket server to connect to,
                eg. 'ws://localhost:8765'."""
        self.server_address = address

        # Create a queue of messages to be sent to the server.
        # Must be thread-safe, as the communications run in their own thread.
        # queue.Queue is the thread-safe queue from the standard library.
        self.queue = Queue()

        self.logger = logutils.init(handler=logfile_handler)

    def get_logger():
        return self.logger

    def send(self, message):
        """Send a message to the server.

        message, dict: the message to be sent, a dict with a 'label' field
            and a 'data' field."""

        self.logger.debug('Adding message to queue: %s.' % message)

        if not ('label' in message and 'data' in message):
            raise ValueError(
                'Missing label or data field in message %s.' % message)

        s = json.dumps(message)
        # queue.put raises Full exception if the queue is full, so no need for
        # us to add a check here.
        self.queue.put(s)

    def _handle(self, raw_message):
        """Do something with a message received from the server.

        raw_message, string: the raw data received from the server."""

        message = json.loads(raw_message)
        self.logger.debug("Received: %s." % message)

    async def _start_websocket(self):
        """Run the send and receive websocket communication loop."""
        async with self.websocket_connection as websocket:
            try:
                while True:
                    # Send everything in the outgoing queue.
                    while not self.queue.empty():
                        message = self.queue.get()
                        print('Sending message: %s.' % message)
                        await websocket.send(message)

                    # Wait until there is another message to read.
                    # TODO(iandioch): Find a way to skip if no message
                    # is waiting, so that outgoing messages are not
                    # left waiting for too long.
                    message = await websocket.recv()
                    self._handle(message)
            except websockets.exceptions.ConnectionClosed:
                # The connection with the server has been dropped.
                # Probably the server quit the connection, or the network has
                # failed.
                self.logger.warning("Connection closed.")

    def _start_websocket_in_new_event_loop(self):
        """Creates an event loop & runs the websocket communicationss in it."""
        # The main thread already has an event loop,
        # but we need to create a new one as we are running in a different
        # thread.
        loop = asyncio.new_event_loop()
        # Tell asyncio that this new loop is the relevant one.
        asyncio.set_event_loop(loop)
        # Start websocket and stay running until the function returns.
        asyncio.get_event_loop().run_until_complete(self._start_websocket())

    def start(self):
        """Get the websocket to connect to the server, send the new_client message,
        and start the communication loop in a new thread."""
        # Make the connection to the server.
        self.websocket_connection = websockets.connect(self.server_address)
        # Add the new_client message to the queue to be sent to the server.
        self.send({'label': 'new_client', 'data': {}})
        # Create a new thread to run the websocket communications in.
        t = threading.Thread(target=self._start_websocket_in_new_event_loop,
                             name='websocket_thread')
        # Start the thread.
        t.start()
