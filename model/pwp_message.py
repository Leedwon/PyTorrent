import struct
from dataclasses import dataclass
from enum import Enum

# todo add block handling according to 3.2 http://jonas.nitro.dk/bittorrent/bittorrent-rfc.html#RFC2119
from bitarray import bitarray


class PwpId(Enum):
    CHOKE = 0
    UN_CHOKE = 1
    INTERESTED = 2
    UNINTERESTED = 3
    HAVE = 4
    BITFIELD = 5
    REQUEST = 6
    PIECE = 7
    CANCEL = 8


# todo read about and use memoryview?
@dataclass
class PwpMessage:
    length: int  # denotes the length of the message, excluding the length part itself. If a message has no payload, its size is 1. Messages of size 0 MAY be sent periodically as keep-alive messages.
    id: PwpId
    payload: bytes = None
    pack_fmt = '!IB'

    def to_bytes(self) -> bytes:
        data = struct.pack(self.pack_fmt, self.length, self.id.value)
        if self.payload is not None:
            data = data + self.payload
        return data

    @staticmethod
    def get_id_length():
        return struct.calcsize('!B')

    @staticmethod
    def from_bytes(data: bytes):
        length, id = struct.unpack_from('!IB', data)
        pwp_id = PwpId(id)
        payload = data[struct.calcsize('!I') + 1:]
        return PwpMessage(length, pwp_id, payload)


class PwpMessageFactoryInterface:
    def get_id(self) -> PwpId:
        pass

    def get_length(self) -> int:
        pass

    def to_bytes(self) -> bytes:
        pass

    def to_pwp_message(self) -> PwpMessage:
        length = self.get_length() + PwpMessage.get_id_length()
        return PwpMessage(length, self.get_id(), self.to_bytes())


@dataclass
class PwpRequest(PwpMessageFactoryInterface):
    piece_index: int
    block_offset: int
    block_length: int
    pack_fmt = '!3I'

    def get_id(self) -> PwpId:
        return PwpId.REQUEST

    def to_bytes(self) -> bytes:
        return struct.pack(self.pack_fmt, self.piece_index, self.block_offset, self.block_length)

    def get_length(self):
        return struct.calcsize(self.pack_fmt)

    @staticmethod
    def from_bytes(data: bytes):
        piece_index, block_offset, block_length = struct.unpack('!3I', data)
        return PwpRequest(
            piece_index=piece_index,
            block_offset=block_offset,
            block_length=block_length)


@dataclass
class PwpPiece(PwpMessageFactoryInterface):
    piece_index: int
    block_offset: int
    block_data: bytes
    pack_fmt = '!2I'

    def get_id(self) -> PwpId:
        return PwpId.PIECE

    def to_bytes(self) -> bytes:
        return struct.pack(self.pack_fmt, self.piece_index, self.block_offset) + self.block_data

    def get_length(self):
        return struct.calcsize(self.pack_fmt) + len(self.block_data)

    @staticmethod
    def from_bytes(data: bytes):
        fmt = '!2I'
        piece_index, block_offset = struct.unpack_from(fmt, data)
        block_data = data[struct.calcsize(fmt):]
        return PwpPiece(
            piece_index=piece_index,
            block_offset=block_offset,
            block_data=block_data
        )


@dataclass
class PwpHave(PwpMessageFactoryInterface):
    piece_index: int
    pack_fmt = '!I'

    def get_id(self) -> PwpId:
        return PwpId.HAVE

    def to_bytes(self):
        return struct.pack(self.pack_fmt, self.piece_index)

    def get_length(self):
        return struct.calcsize(self.pack_fmt)

    @staticmethod
    def from_bytes(data: bytes):
        fmt = '!I'
        return PwpHave(piece_index=struct.unpack(fmt, data)[0])


@dataclass
class PwpCancel(PwpMessageFactoryInterface):
    piece_index: int
    block_offset: int
    block_length: int
    pack_fmt = '!3I'

    def get_id(self) -> PwpId:
        return PwpId.CANCEL

    def to_bytes(self) -> bytes:
        return struct.pack(self.pack_fmt, self.piece_index, self.block_offset, self.block_length)

    def get_length(self):
        return struct.calcsize(self.pack_fmt)

    @staticmethod
    def from_bytes(data: bytes):
        index, offset, length = struct.unpack('!3I', data)
        return PwpCancel(
            piece_index=index,
            block_offset=offset,
            block_length=length
        )


def generate_choke_message() -> PwpMessage:
    return PwpMessage(length=PwpMessage.get_id_length(), id=PwpId.CHOKE)


def generate_unchoke_message() -> PwpMessage:
    return PwpMessage(length=PwpMessage.get_id_length(), id=PwpId.UN_CHOKE)


def generate_interested_message() -> PwpMessage:
    return PwpMessage(length=PwpMessage.get_id_length(), id=PwpId.INTERESTED)


def generate_uninterested_message() -> PwpMessage:
    return PwpMessage(length=PwpMessage.get_id_length(), id=PwpId.UNINTERESTED)


def generate_bitfield_message(data: bitarray) -> PwpMessage:
    data = data.tobytes()
    length = PwpMessage.get_id_length() + len(data)
    return PwpMessage(length, PwpId.BITFIELD, data)
