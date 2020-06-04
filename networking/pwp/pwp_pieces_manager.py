# this class should be used as shared resource for pwp connnections
# its purpose is to track what pieces we already have and what pieces should we fetch
from bitarray import bitarray


class PwpPiecesManager:
    def __init__(self, pieces_hashes, piece_length: int, owned_pieces=None):
        if owned_pieces is None:
            owned_pieces = []
        self.pieces_hashes: list = pieces_hashes  # list of bytes
        self.owned_pieces: list = owned_pieces  # list of bytes
        self.currently_fetching: list = []  # list of bytes
        self.piece_length = piece_length

    # for now we are just taking first available change algorithm later
    def get_piece_index_to_fetch(self, haves: list) -> int:
        for piece in haves:
            if piece in self.pieces_hashes and piece not in self.owned_pieces and piece not in self.currently_fetching:
                return haves.index(piece)
        return -1

    # should be called when piece is being fetched
    def add_fetching_piece_by_index(self, index: int):
        self.currently_fetching.append(self.pieces_hashes[index])

    def get_offset_for_piece(self, piece_index: int) -> int:
        return (piece_index + 1) * self.piece_length

    def get_pieces_from_bitarray(self, arr: bitarray) -> list:
        pieces = []
        for index, bit in enumerate(arr):
            if bit is True:
                pieces.append(self.pieces_hashes[index])
        return pieces

    def add_piece(self, piece: bytes):
        if piece in self.owned_pieces and piece not in self.owned_pieces:
            self.owned_pieces.append(piece)

    def get_owned_pieces(self) -> bitarray:
        arr = bitarray()
        for piece in self.pieces_hashes:
            arr.append(piece in self.owned_pieces)
        return arr

    def has_all_pieces(self) -> bool:
        return self.owned_pieces == self.pieces_hashes
