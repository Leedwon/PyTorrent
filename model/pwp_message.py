from dataclasses import dataclass
from enum import Enum


# todo add block handling according to 3.2 http://jonas.nitro.dk/bittorrent/bittorrent-rfc.html#RFC2119
# for now we will take block size = piece size

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

    def to_bytes(self) -> bytes:
        return bytes([self.value])


@dataclass
class PwpMessage:
    length: int  # denotes the length of the message, excluding the length part itself. If a message has no payload, its size is 1. Messages of size 0 MAY be sent periodically as keep-alive messages.
    id: PwpId
    payload: bytes = None

    def to_bytes(self) -> bytes:
        b = bytes([self.length])
        b += self.id.to_bytes()
        if self.payload is not None:
            b += self.payload
        return b

    @staticmethod
    def from_bytes(data: bytes):
        length = data[0]
        pwp_id = PwpId(data[1])
        payload = data[2:]
        return PwpMessage(length, pwp_id, payload)


@dataclass
class PwpRequest:
    piece_index: int
    block_offset: int
    block_length: int

    def to_bytes(self) -> bytes:
        return bytes([self.piece_index, self.block_offset, self.block_length])


@dataclass
class PwpPiece:
    piece_index: int
    block_offset: int
    block_data: bytes

    def to_bytes(self) -> bytes:
        b = bytes([self.piece_index, self.block_offset])
        b += self.block_data
        return b


@dataclass
class PwpCancel:
    piece_index: int
    block_offset: int
    block_length: int
