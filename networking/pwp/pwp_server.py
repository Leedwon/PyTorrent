import asyncio

from networking.pwp.handshake_manager import HandshakeManager, HANDSHAKE_LENGTH
from networking.pwp.pwp_connection import PwpConnection

TIMEOUT = 10


class PwpServer:
    def __init__(self, handshake_manager: HandshakeManager, on_new_connection, on_message_received, on_disconnected):
        self.handshake_manager = handshake_manager
        self.on_new_connection = on_new_connection  # todo add type of this callback smh?
        self.on_message_received = on_message_received  # todo avoid this callback hell
        self.on_disconnected = on_disconnected  # todo avoid callbacks

    async def run(self):
        try:
            server = await asyncio.start_server(self.handler, '127.0.0.1', 8888)
            print(f'serving on {server.sockets[0].getsockname()}')
        except OSError:
            print(f'already serving')

    async def handler(self, reader, writer):
        print("new peer connected to us")
        data = await asyncio.wait_for(reader.read(HANDSHAKE_LENGTH), TIMEOUT)
        if data is not None:
            handshake_validated = self.handshake_manager.is_handshake_data_valid(data)
            if handshake_validated:
                print("server handshake ok")
                writer.write(self.handshake_manager.prepare_data_to_send())
                await writer.drain()
                await self.on_new_connection(
                    PwpConnection(writer=writer, reader=reader, on_message_received=self.on_message_received,
                                  on_disconnected=self.on_disconnected))
            else:
                writer.close()
                await writer.wait_closed()
