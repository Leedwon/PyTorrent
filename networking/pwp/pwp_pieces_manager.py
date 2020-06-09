# this class should be used as shared resource for pwp connnections
# its purpose is to track what pieces we already have and what pieces should we fetch
from collections import Counter

from bitarray import bitarray
import hashlib


class PwpPiecesManager:
    def __init__(self, pieces_hashes, piece_length: int, file_length: int, owned_pieces=None):
        if owned_pieces is None:
            owned_pieces = []
        self.pieces_hashes: list = pieces_hashes  # list of bytes
        self.owned_pieces: list = owned_pieces  # list of bytes
        self.currently_fetching: list = []  # list of bytes
        self.piece_length = piece_length
        self.file_length = file_length  # todo what about multi file torrents?

    # for now we are just taking first available change algorithm later
    def get_piece_index_to_fetch(self, haves: list) -> int:
        for piece in haves:
            if piece in self.pieces_hashes and piece not in self.owned_pieces and piece not in self.currently_fetching:
                return haves.index(piece)
        return -1

    # should be called when piece is being fetched
    def add_fetching_piece_by_index(self, index: int):
        self.currently_fetching.append(self.pieces_hashes[index])

    def get_offset_for_piece_index(self, piece_index: int) -> int:
        return piece_index * self.piece_length

    def get_pieces_from_bitarray(self, arr: bitarray) -> list:
        pieces = []
        for index, bit in enumerate(arr):
            if bit is True:
                pieces.append(self.pieces_hashes[index])
        return pieces

    def is_last_piece(self, piece_index: int) -> bool:
        return len(self.pieces_hashes) - 1 == piece_index

    def piece_downloaded(self, piece_index: int):
        piece = self.pieces_hashes[piece_index]
        if piece in self.currently_fetching:
            self.currently_fetching.remove(piece)
        else:
            print("error : piece_downloaded when it wasn't in currently fetching")
        if piece not in self.owned_pieces:
            self.owned_pieces.append(piece)
        else:
            print("error : we already have that piece")

    def validate_piece(self, piece_index: int, piece: bytes) -> bool:
        actual_hash = self.pieces_hashes[piece_index]
        piece_hash = hashlib.sha1(piece)
        return piece_hash.digest() == actual_hash

    def get_owned_pieces(self) -> bitarray:
        arr = bitarray()
        for piece in self.pieces_hashes:
            arr.append(piece in self.owned_pieces)
        return arr

    def has_all_pieces(self) -> bool:
        return len(self.pieces_hashes) - len(self.owned_pieces) == 0

    def get_owned_pieces_percentage(self) -> float:
        return len(self.owned_pieces) / len(self.pieces_hashes)

    def has_any_piece(self) -> bool:
        return bool(self.owned_pieces)

    def get_len_for_last_piece(self) -> int:
        return self.file_length - (len(self.pieces_hashes) - 1) * self.piece_length
