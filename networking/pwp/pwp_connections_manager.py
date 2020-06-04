import asyncio
from uuid import uuid1

from bitarray import bitarray

from model.pwp_message import PwpMessage, PwpId, PwpRequest, PwpPiece, PwpCancel, generate_choke_message
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
        self.should_serve = should_serve  # todo remove after develompent

    # built on assumption that now we have only known peer add peer cap to not serve more then n at one time
    async def run(self):
        await asyncio.gather(
            self._serve(),
            self.connect_to_peers()
        )

    async def _serve(self):
        if self.should_serve:
            server = PwpServer(handshake_manager=self.handshake_manager, on_new_connection=self.on_new_connection,
                               on_message_received=self.on_message_received)
            await server.run()

    async def _connect_to_others(self):
        await self.connect_to_peers()
        while self.pieces_manager.has_all_pieces() is False:
            await self.fetch_pieces()

    async def fetch_pieces(self):
        for connection in self.active_connections:
            index_to_fetch = self.pieces_manager.get_piece_index_to_fetch(connection.pieces_that_can_download)
            self.pieces_manager.add_fetching_piece_by_index(index_to_fetch)

    async def connect_to_peers(self):
        for peer in self.peers:
            client = PwpClient(handshake_manager=self.handshake_manager)
            try:
                writer, reader = await client.handshake_and_get_writer_reader_if_possible(peer)
                if writer is not None and reader is not None:
                    connection = PwpConnection(writer, reader, self.on_message_received)
                    print('handshake ok')
                    await self.on_new_connection(connection)
                else:
                    print('handshake failed')
            except (OSError, ConnectionRefusedError):
                print(f'couldn\'t connect to peer with ip = {peer.ip}:{peer.port}')

    async def on_new_connection(self, connection: PwpConnection):
        self.active_connections.append(connection)
        await connection.send_message(generate_choke_message())
        await connection.start_listening()

    def on_message_received(self, connection: PwpConnection, message: PwpMessage):
        print(f"message received = {str(message)}")
        if message.id is PwpId.CHOKE:
            connection.am_choked = True
        elif message.id is PwpId.UN_CHOKE:
            connection.am_choked = False
        elif message.id is PwpId.INTERESTED:
            connection.is_interested = True
        elif message.id is PwpId.UNINTERESTED:
            connection.is_interested = False
        elif message.id is PwpId.HAVE:
            pass  # todo implement
        elif message.id is PwpId.BITFIELD:
            arr = bitarray()
            arr.frombytes(message.payload)
            connection.pieces_that_can_download = self.pieces_manager.get_pieces_from_bitarray(arr)
        elif message.id is PwpId.REQUEST:
            request = PwpRequest.from_bytes(message.payload)
            pass  # todo do sth with request
        elif message.id is PwpId.PIECE:
            piece = PwpPiece.from_bytes(message.payload)
            pass  # todo do sth with piece
        elif message.id is PwpId.CANCEL:
            cancel = PwpCancel.from_bytes(message.payload)
            pass  # todo do sth with cancel
