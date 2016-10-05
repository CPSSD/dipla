import asyncio
import websockets

connected = set()

async def handler(websocket, path):
  connected.add(websocket)
  await websocket.send(str(connected));

start_server = websockets.serve(handler, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
