import asyncio
from uuid import uuid1

from bitarray import bitarray

from file_manager import FileManager
from model.pwp_message import PwpMessage, PwpId, PwpRequest, PwpPiece, PwpCancel, MessagesUtil, PwpHave
from networking.pwp.handshake_manager import HandshakeManager
from networking.pwp.pwp_client import PwpClient
from networking.pwp.pwp_connection import PwpConnection
from networking.pwp.pwp_pieces_manager import PwpPiecesManager
from networking.pwp.pwp_server import PwpServer
from utils.bytes_join import join_to_bytes


# todo add reacting state messages
class PwpConnectionsManager:
    def __init__(self, pieces_manager: PwpPiecesManager, handshake_manager: HandshakeManager, file_manager: FileManager,
                 peers=None,
                 should_serve=True):
        if peers is None:
            peers = []
        self.peers = peers
        self.handshake_manager = handshake_manager
        self.pieces_manager = pieces_manager
        self.file_manager = file_manager
        self.active_connections = []
        self.peer_id = str(uuid1())[:20]  # todo generate somewhere else probably
        self.should_serve = should_serve  # todo remove after development
        self.received_blocks = []
        self.block_len = 8192
        if pieces_manager.piece_length < 8192:
            self.block_len = pieces_manager.piece_length

    # built on assumption that now we have only known peer add peer cap to not serve more then n at one time
    async def run(self):
        await asyncio.gather(
            self._serve(),
            self._connect_to_others(),
            self._fetch_pieces_until_all_gathered(),
            self._save_received_pieces(),
            self._upload_pieces(),
            self._print_progress()
        )

    # todo stop fetching when choked
    async def _fetch_piece(self, connection: PwpConnection, piece_index: int):
        full_blocks_in_piece = int(self.pieces_manager.piece_length / self.block_len)
        leftover_block_len = self.pieces_manager.piece_length % self.block_len

        for i in range(0, full_blocks_in_piece):
            msg = PwpRequest(piece_index, i * self.block_len, self.block_len)
            await connection.send_message(msg.to_pwp_message())
        if leftover_block_len > 0:
            msg = PwpRequest(piece_index, full_blocks_in_piece * self.block_len, leftover_block_len)
            await connection.send_message(msg.to_pwp_message())

    # todo prettify
    async def _save_received_pieces(self):
        while True:
            if self.received_blocks:
                indexes = list(set(map(lambda block: block.piece_index, self.received_blocks)))
                for index in indexes:
                    blocks_per_index = list(filter(lambda block: block.piece_index == index, self.received_blocks))
                    bytes_len_per_index = list(map(lambda block: len(block.block_data), blocks_per_index))
                    if self._is_entire_piece_acquired(bytes_len_per_index, index):
                        data = self._get_data_from_blocks(blocks_per_index)
                        if self.pieces_manager.validate_piece(index, data):
                            offset = self.pieces_manager.get_offset_for_piece_index(index)
                            await self.file_manager.write_with_offset_and_update_file_bytes(offset, data)
                            self._cleanup_after_saved_to_file(blocks_per_index, index)
                        else:
                            print("piece is not valid and won't be saved - be careful there might be malicious peer")
            await asyncio.sleep(0)  # todo investigate why asyncio.gather() is not working properly without it

    def _is_entire_piece_acquired(self, bytes_lengths_per_index: list, piece_index: int):
        total_length = sum(bytes_lengths_per_index)
        return total_length == self.pieces_manager.piece_length or self.pieces_manager.is_last_piece(
            piece_index) and total_length == self.pieces_manager.get_len_for_last_piece()

    def _get_data_from_blocks(self, blocks_per_index: list):
        sorted_blocks = sorted(blocks_per_index, key=lambda block: block.block_offset)
        return join_to_bytes(list(map(lambda block: block.block_data, sorted_blocks)))

    def _cleanup_after_saved_to_file(self, blocks: list, index: int):
        self.pieces_manager.piece_downloaded(index)
        for block in blocks:
            self.received_blocks.remove(block)

    async def _serve(self):
        if self.should_serve:
            server = PwpServer(handshake_manager=self.handshake_manager, on_new_connection=self.on_new_connection,
                               on_message_received=self.on_message_received, on_disconnected=self.on_disconnected)
            await server.run()

    async def _connect_to_others(self):
        await self._connect_to_peers()

    async def _fetch_pieces_until_all_gathered(self):
        while self.pieces_manager.has_all_pieces() is False:
            await asyncio.sleep(0)
            await self._fetch_pieces()
        print("has all pieces - uploading only")

    async def _fetch_pieces(self):
        for connection in self.active_connections:
            index_to_fetch = self.pieces_manager.get_piece_index_to_fetch(connection.pieces_that_can_download)
            if index_to_fetch != -1:
                self.pieces_manager.add_fetching_piece_by_index(index_to_fetch)
                await self._fetch_piece(connection, index_to_fetch)

    # todo add some algorithm to choose in what order to send add parallel connection sending
    async def _upload_pieces(self):
        while True:
            for connection in self.active_connections:
                for request in connection.requests:
                    offset = self.pieces_manager.get_offset_for_piece_index(request.piece_index) + request.block_offset
                    data_to_send = await self.file_manager.get_data(offset, request.block_length)
                    piece = PwpPiece(request.piece_index, request.block_offset, data_to_send)
                    print(f'sending piece with index {piece.piece_index}')
                    await connection.send_message(piece.to_pwp_message())
                    connection.on_request_sent(request)
            await asyncio.sleep(0)

    async def _connect_to_peers(self):
        for peer in self.peers:
            client = PwpClient(handshake_manager=self.handshake_manager)
            try:
                writer, reader = await client.handshake_and_get_writer_reader_if_possible(peer)
                if writer is not None and reader is not None:
                    connection = PwpConnection(writer, reader, self.on_message_received, self.on_disconnected)
                    print('handshake ok')
                    await self.on_new_connection(connection)
                else:
                    print('handshake failed - dropping connection')
            except (OSError, ConnectionRefusedError):
                print(f'couldn\'t connect to peer with ip = {peer.ip}:{peer.port}')

    def on_disconnected(self, connection: PwpConnection):
        self.active_connections.remove(connection)

    async def on_new_connection(self, connection: PwpConnection):
        self.active_connections.append(connection)
        if self.pieces_manager.has_any_piece():
            msg = MessagesUtil.generate_bitfield_message(self.pieces_manager.get_owned_pieces())
            await connection.send_message(msg)
        await connection.send_message(MessagesUtil.generate_choke_message())
        await connection.start_listening()

    # todo refactor to handle message receiving in connection and use fewer callbacks
    def on_message_received(self, connection: PwpConnection, message: PwpMessage):
        # print(f"message received = {str(message)}")
        if message.id is PwpId.CHOKE:
            connection.am_choked = True
        elif message.id is PwpId.UN_CHOKE:
            connection.am_choked = False
        elif message.id is PwpId.INTERESTED:
            connection.is_interested = True
        elif message.id is PwpId.UNINTERESTED:
            connection.is_interested = False
        elif message.id is PwpId.HAVE:
            have_msg = PwpHave.from_bytes(message.payload)
            connection.add_piece_that_can_download(self.pieces_manager.pieces_hashes[have_msg.piece_index])
        elif message.id is PwpId.BITFIELD:
            arr = bitarray()
            arr.frombytes(message.payload)
            connection.pieces_that_can_download = self.pieces_manager.get_pieces_from_bitarray(arr)
        elif message.id is PwpId.REQUEST:
            request = PwpRequest.from_bytes(message.payload)
            connection.add_request(request)
        elif message.id is PwpId.PIECE:
            piece = PwpPiece.from_bytes(message.payload)
            self.received_blocks.append(piece)
        elif message.id is PwpId.CANCEL:
            cancel = PwpCancel.from_bytes(message.payload)
            connection.on_request_cancel(cancel)

    # todo move to another file?
    async def _print_progress(self):
        while self.pieces_manager.has_all_pieces() is False:
            percentage_acquired = self.pieces_manager.get_owned_pieces_percentage() * 100
            progress = "|"
            for i in range(0, 100):
                if percentage_acquired <= i:
                    progress = progress + "-"
                else:
                    progress = progress + "="
            progress = progress + "|"
            progress = progress + f" connected to {len(self.active_connections)} peers"
            print(progress)
            await asyncio.sleep(0.15)
        progress = "|"
        for i in range(0, 100):
            progress = progress + "="
        progress = progress + "|"
        print(progress)
