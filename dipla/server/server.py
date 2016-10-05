import asyncio
import websockets

connected = {}

async def handler(websocket, path):
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
            print(message)
    finally:
        del connected[user_id]


start_server = websockets.serve(handler, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
