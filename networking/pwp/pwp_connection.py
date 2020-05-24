import asyncio
from asyncio import StreamWriter, StreamReader, Task
from venv import logger

from model.pwp_message import PwpMessage

HANDSHAKE_LENGTH = 68
TIMEOUT = 10


class PwpConnection:
    def __init__(self, writer: StreamWriter, reader: StreamReader):
        self.writer = writer
        self.reader = reader
        self.is_connected = False

    async def send_message(self, message: PwpMessage):
        self.writer.write(message.to_bytes())
        await self.writer.drain()

    def listen(self) -> Task:
        return asyncio.create_task(self.read_messages())

    async def read_messages(self):
        while self.is_connected:
            length = await self.reader.read(1)
            length = length[0]
            if length is not None:
                data = await self.reader.read(length)
                msg = PwpMessage.from_bytes(bytes([length]) + data)  # todo handle messages
                logger.info(f'received msg  = {str(msg)}')  # todo remove after impl

    # todo mb try with resources?
    async def kill_connection(self):
        self.writer.close()
        await self.writer.wait_closed()
