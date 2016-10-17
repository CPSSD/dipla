import asyncio
import websockets


class Server:
    def __init__(self, task_queue):
        self.task_queue = task_queue
        self.connected = {}
        # This dict stores the requests the server can process paired with the
        # handler function.
        self.services = {
            'get_binary': self._handle_get_binary,
            'get_data_instructions': self._handle_get_data_instructions,
        }

    async def _handle_get_binary(self, message):
        pass

    async def _handle_get_data_instructions(self, message):
        return self.task_queue.pop_task().data_instructions

    async def websocket_handler(self, websocket, path):
        user_id = path[1:]

        if user_id in self.connected.keys():
            await websocket.send("Sorry, this Agent ID is taken")
            return

        self.connected[user_id] = websocket

        try:
            # recv() raises a ConnectionClosed exception when the client
            # disconnects, which breaks out of the while True loop.
            while True:
                message = await websocket.recv()
                # TODO: Parse the message into some format rather than taking
                # as a string (to allow other params to be included in the
                # request)
                response = 'ERROR'
                if message in self.services:
                    response = self.services[message](message)
                await websocket.send(response)
        except websockets.exceptions.ConnectionClosed:
            print(user_id + " has closed the connection")
        finally:
            self.connected.pop(user_id, None)

    def start(self):
        start_server = websockets.serve(
                self.websocket_handler,
                "localhost",
                8765)

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    s = Server([])
    s.start()
