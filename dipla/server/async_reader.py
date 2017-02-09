import asyncio
import sys

class AsyncReader():

    def __init__(self, loop, pipe):
        self.async_input = AsyncReader.create_async_input(loop, pipe)

    @staticmethod
    async def create_async_input(loop, pipe):
        reader = asyncio.StreamReader()
        reader_protocol = asyncio.StreamReaderProtocol(reader)

        await loop.connect_read_pipe(lambda: reader_protocol, pipe)
        return reader

    async def read_input(self, async_reader):
        return (await async_reader.readline()).decode('utf8').strip()

    async def main(self):
        async_input = await self.create_async_input(asyncio.get_event_loop())
        print(await self.read_input(async_input))
