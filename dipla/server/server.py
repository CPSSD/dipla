import asyncio
import websockets

class Server:
    
    def __init__(self, task_queue):
        self.task_queue = task_queue

    async def websocket_handler(self, websocket, path, connected = {}):
        user_id = path[1:]

        if(user_id in connected.keys()):
            await websocket.send("Sorry, this Agent ID is taken")
            return

        connected[user_id] = websocket

        try:
            await websocket.send("Online users: " + ", ".join(connected.keys()))
            while True:
                # recv() raises a ConnectionClosed exception when the client
                # disconnects, which breaks out of the while True loop.
                message = await websocket.recv()
                # TODO(stefankennedy) Handle received message
                print(message)
        except websockets.exceptions.ConnectionClosed:
            print(user_id + " has closed the connection")
        finally:
            del connected[user_id]

    def start(self):
        start_server = websockets.serve(
                self.websocket_handler,
                "localhost",
                8765)

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
