import asyncio

from networking.pwp.handshake_manager import HandshakeManager, HANDSHAKE_LENGTH
from networking.pwp.pwp_connection import PwpConnection

TIMEOUT = 10


class PwpServer:
    def __init__(self, handshake_manager: HandshakeManager, on_new_connection):
        self.handshake_manager = handshake_manager
        self.on_new_connection = on_new_connection  # todo add type of this callback smh?
        self.serving_task = None

    async def run(self):
        server = await asyncio.start_server(self.handler, '127.0.0.1', 8888)
        print(f'serving on {server.sockets[0].getsockname()}')

    async def handler(self, reader, writer):
        data = await asyncio.wait_for(reader.read(HANDSHAKE_LENGTH), TIMEOUT)
        if data is not None:
            handshake_validated = self.handshake_manager.is_handshake_data_valid(data)
            if handshake_validated:
                print("server handshake ok")
                writer.write(self.handshake_manager.prepare_data_to_send())
                await writer.drain()
                self.on_new_connection(PwpConnection(writer=writer, reader=reader))
            else:
                writer.close()
                await writer.wait_closed()

    async def kill_server(self):
        if self.serving_task is not None:
            self.serving_task.cancel()
