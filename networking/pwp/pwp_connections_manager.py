from uuid import uuid1

from model.pwp_message import PwpMessage, PwpId
from networking.pwp.handshake_manager import HandshakeManager
from networking.pwp.pwp_client import PwpClient
from networking.pwp.pwp_connection import PwpConnection
from networking.pwp.pwp_pieces_manager import PwpPiecesManager
from networking.pwp.pwp_server import PwpServer


class PwpConnectionsManager:
    def __init__(self, pieces_manager: PwpPiecesManager, handshake_manager: HandshakeManager, peers=None,
                 should_serve=True):
        if peers is None:
            peers = []
        self.peers = peers
        self.handshake_manager = handshake_manager
        self.pieces_manager = pieces_manager
        self.active_connections = []
        self.fetching_pieces = []
        self.peer_id = str(uuid1())[:20]  # todo generate somewhere else probably
        self.should_serve = should_serve  # for testing purposes remove later

    def _on_new_connection(self, connection):
        self.active_connections.append(connection)

    # built on assumption that now we have only known peer add peer cap to not serve more then n at one time
    async def run(self):
        if self.should_serve:
            server = PwpServer(handshake_manager=self.handshake_manager, on_new_connection=self._on_new_connection)
            await server.run()
        await self.connect_to_peers()
        # todo mechanism to get missing pieces

    async def connect_to_peers(self):
        for peer in self.peers:
            client = PwpClient(handshake_manager=self.handshake_manager)
            try:
                connection = await client.create_connection_and_handshake(peer)
                if connection is not None:
                    print('handshake ok')
                    await self.on_connected(connection)
                else:
                    print('handshake failed')

            except (OSError, ConnectionRefusedError):
                print(f'couldn\'t connect to peer with ip = {peer.ip}:{peer.port}')

    async def on_connected(self, connection: PwpConnection):
        self.active_connections.append(connection)
        await connection.send_message(self._generate_choke_message())  # send choke
        connection.listen()

    # todo move smwhere else?
    def _generate_choke_message(self) -> PwpMessage:
        return PwpMessage(length=1, id=PwpId.CHOKE)
