import asyncio

from model.peer import Peer
from networking.pwp.handshake_manager import HandshakeManager, HANDSHAKE_LENGTH
from networking.pwp.pwp_connection import PwpConnection

TIMEOUT = 10


class PwpClient:
    def __init__(self, handshake_manager: HandshakeManager):
        self.handshake_manager = handshake_manager

    # return pwpConnection or None - think of sth better to return?
    async def create_connection_and_handshake(self, peer: Peer):
        reader, writer = await asyncio.open_connection(host=peer.ip, port=peer.port)

        await self._send_handshake(writer)
        read_and_validate = await self._read_handshake_and_validate(reader)

        if read_and_validate:
            return PwpConnection(writer, reader)
        else:
            writer.close()
            return None

    async def _send_handshake(self, writer):
        data_to_send = self.handshake_manager.prepare_data_to_send()

        writer.write(data_to_send)
        await writer.drain()

    async def _read_handshake_and_validate(self, reader) -> bool:
        data = await asyncio.wait_for(reader.read(HANDSHAKE_LENGTH), TIMEOUT)
        return self.handshake_manager.is_handshake_data_valid(data)
