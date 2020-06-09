import struct
from asyncio import StreamWriter, StreamReader

from model.pwp_message import PwpMessage, PwpRequest, PwpCancel

HANDSHAKE_LENGTH = 68
TIMEOUT = 10


# todo too many callback refactor
class PwpConnection:
    def __init__(self, writer: StreamWriter, reader: StreamReader, on_message_received, on_disconnected):
        self.writer = writer
        self.reader = reader

        self.on_message_received = on_message_received  # Type Function(Connection, PwpMessage) think of something better then callbacks?
        self.on_disconnected = on_disconnected  # Type Function(Connection)

        self.am_choked = False  # whether we are choked
        self.am_interested = False
        self.is_choked = False  # whether another part of connection is choked
        self.is_interested = False
        self.is_connected = True

        self.pieces_that_can_download = []  # list of piece hashes
        self.requests = []  # Type List<PwpRequest>

    async def send_message(self, message: PwpMessage):
        self.writer.write(message.to_bytes())
        await self.writer.drain()

    async def start_listening(self):
        length_fmt = '!I'
        length_to_read = struct.calcsize(length_fmt)
        while self.is_connected:
            try:
                length_struct = await self.reader.readexactly(length_to_read)
                if length_struct is not None:
                    msg_len = struct.unpack(length_fmt, length_struct)
                    data = await self.reader.readexactly(msg_len[0])
                    self.on_message_received(self, PwpMessage.from_bytes(length_struct + data))
            except ConnectionResetError:
                print("peer disconected")
                self.is_connected = False
                self.on_disconnected(self)

    # todo mb try with resources?
    async def kill_connection(self):
        self.writer.close()
        await self.writer.wait_closed()

    def add_piece_that_can_download(self, piece: bytes):
        if piece not in self.pieces_that_can_download:
            self.pieces_that_can_download.append(piece)
        else:
            print("have message return information that we already had")

    def add_request(self, request: PwpRequest):
        self.requests.append(request)

    def on_request_sent(self, request: PwpRequest):
        self.requests.remove(request)

    def on_request_cancel(self, cancel: PwpCancel):
        request_from_cancel = PwpRequest(cancel.piece_index, cancel.block_offset, cancel.block_length)
        self.requests.remove(request_from_cancel)
