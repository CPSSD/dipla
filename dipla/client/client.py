#!/usr/bin/env python

import asyncio
import websockets
import json
import threading
from logging import FileHandler
from dipla.shared import logutils


class Client(object):

    def __init__(self,
                 server_address,
                 logfile_handler=FileHandler('DIPLA.log')):
        """Create the client.

        address, string: The address of the websocket server to connect to,
                eg. 'ws://localhost:8765'."""
        self.server_address = server_address
        self.websocket = None
        self.logger = logutils.init(handler=logfile_handler)

    def get_logger():
        return self.logger

    async def _get_websocket(self):
        if self.websocket is None:
            self.websocket = await websockets.connect(self.server_address)
        return self.websocket

    async def _get_connection_and_send(self, message):
        """Get the websocket connection and send the given message to
        the server.

        message, json string: The message to be sent."""
        websocket = await self._get_websocket()
        await websocket.send(message)

    def send(self, message):
        """Send a message to the server.

        message, dict: the message to be sent, a dict with a 'label' field
            and a 'data' field."""

        if not ('label' in message and 'data' in message):
            raise ValueError(
                'Missing label or data field in message %s.' % message)

        self.logger.debug('Sending message: %s.' % message)
        json_message = json.dumps(message)

        # run the coroutine to send the message
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._get_connection_and_send(json_message))

    def _handle(self, raw_message):
        """Do something with a message received from the server.

        raw_message, string: the raw data received from the server."""

        message = json.loads(raw_message)
        self.logger.debug("Received: %s." % message)

    async def _start_websocket(self):
        """Run the loop receiving websocket messages."""
        # Must create different websocket here to that of send(), as they
        # cannot be shared across threads.
        async with websockets.connect(self.server_address) as websocket:
            try:
                while True:
                    message = await websocket.recv()
                    self._handle(message)
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("Connection closed.")

    def _start_websocket_in_new_event_loop(self):
        """Creates an event loop & runs the websocket communicationss in it."""
        # The main thread already has an event loop, but we need
        # to create a new one as we are running in a different thread.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._start_websocket())
        loop.close()

    def start(self):
        """Send the new_client message, and start the communication loop
        in a new thread."""
        self.send({'label': 'new_client', 'data': {}})
        # Create a new thread to run the websocket communications in.
        t = threading.Thread(target=self._start_websocket_in_new_event_loop,
                             name='websocket_thread')
        t.start()

    def __del__(self):
        asyncio.get_event_loop().close()
