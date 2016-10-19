import asyncio
import websockets
import worker_group


class Server:

    def __init__(self, task_queue, worker_group):
        self.task_queue = task_queue
        self.worker_group = worker_group

    async def websocket_handler(self, websocket, path):
        user_id = path[1:]

        try:
            self.worker_group.add_worker(
                    worker_group.Worker(user_id, 0.5, websocket))
        except(worker_group.UniqueError):
            await websocket.send("Sorry, this Agent ID is taken")
            return
        
        self.worker_group.lease_worker()

        try:
            await websocket.send(self.task_queue.pop_task().data_instructions)
            while True:
                # recv() raises a ConnectionClosed exception when the client
                # disconnects, which breaks out of the while True loop.
                message = await websocket.recv()
                # TODO(stefankennedy) Handle received message
        except websockets.exceptions.ConnectionClosed:
            print(user_id + " has closed the connection")
        finally:
            self.worker_group.return_worker(user_id)
            self.worker_group.remove_worker(user_id)

    def start(self):
        start_server = websockets.serve(
                self.websocket_handler,
                "localhost",
                8765)

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
