import asyncio
import websockets

connected = {}

async def handler(websocket, path):
    if(path[1:] in connected.keys()):
        await websocket.send("Sorry, this Agent ID is taken")
        return
    connected[path[1:]]=(websocket)
    await websocket.send("Online users: " + ", ".join(connected.keys()))
    
    

start_server = websockets.serve(handler, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
