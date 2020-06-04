import struct
from asyncio import StreamWriter, StreamReader

from model.pwp_message import PwpMessage

HANDSHAKE_LENGTH = 68
TIMEOUT = 10


class PwpConnection:
    def __init__(self, writer: StreamWriter, reader: StreamReader, on_message_received):
        self.writer = writer
        self.reader = reader
        self.on_message_received = on_message_received  # Type Function(Connection, PwpMessage) think of something better then callbacks?
        self.am_choked = False  # whether we are choked
        self.am_interested = False
        self.is_choked = False  # whether another part of connection is choked
        self.is_interested = False
        self.pieces_that_can_download = []

    async def send_message(self, message: PwpMessage):
        self.writer.write(message.to_bytes())
        await self.writer.drain()

    async def start_listening(self):
        length_fmt = '!I'
        length_to_read = struct.calcsize(length_fmt)
        while True:
            length_struct = await self.reader.readexactly(length_to_read)
            if length_struct is not None:
                msg_len = struct.unpack(length_fmt, length_struct)
                data = await self.reader.readexactly(msg_len[0])
                self.on_message_received(self, PwpMessage.from_bytes(length_struct + data))

    # todo mb try with resources?
    async def kill_connection(self):
        self.writer.close()
        await self.writer.wait_closed()
