import asyncio
import websockets
import json
import threading
import logging
import os


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
        # need to be pased into all of the ClientServices.
        self.services = services

    def get_logger(self):
        return self.logger

    def send(self, message, websocket): # I dont like passing the websocket here, queue approach was nicer
        if not ('label' in message and 'data' in message):
            raise ValueError(
                'Missing label or data field in message %s.' % message)

        self.logger.debug('Sending message: %s.' % message)
        json_message = json.dumps(message)

        # run the coroutine to send the message
        print("Sending " + json_message)
        asyncio.ensure_future(self._send_async(websocket, json_message))
        # TODO(iandioch): Investigate ways of closing this loop automatically
        # once the connection is dropped and the client is shutting down.

    async def _send_async(self, websocket, message):
        """Send a message to the server.

        message, dict: the message to be sent, a dict with a 'label' field
            and a 'data' field."""
        await websocket.send(message)

    async def receive_loop(self, websocket):
        try:
            while True:
                message = await websocket.recv()
                print("Received message: " + message)
                self._handle(message) 
        except websockets.exceptions.ConnectionClosed:
            print("Disconnected from server")
            self.logger.warning("Connection closed.")

    def _handle(self, raw_message):
        """Do something with a message received from the server.

        raw_message, string: the raw data received from the server."""
        self.logger.debug("Received: %s." % raw_message)
        message = json.loads(raw_message)
        self._run_service(message['label'], message['data'])

    def _run_service(self, label, data):
        try:
            service = self.services[label]
            service.execute(data)
        except KeyError:
            self.logger.error("Failed to find service: {}".format(label))

    async def start_websocket(self):
        """Run the loop receiving websocket messages."""
        return await websockets.connect(self.server_address)
        
    def _get_platform(self):
        """Get some information about the platform the client is running on."""
        if os.name == 'posix':
            return os.uname()
        # TODO(ndonn): Add better info for Windows and Mac versions
        return os.name

    def start(self):
        """Send the get_binary message, and start the communication loops
        in a new thread."""
        loop = asyncio.get_event_loop()
        websocket = loop.run_until_complete(self.start_websocket())
        
        asyncio.ensure_future(self.receive_loop(websocket))
        self.send({
            'label': 'get_binary',
            'data': {'platform': self._get_platform()}}, websocket)
        
        loop.run_forever()
