# this class should be used as shared resource for pwp connnections
# its purpose is to track what pieces we already have and what pieces should we fetch


class PwpPiecesManager:
    def __init__(self, pieces_hashes, owned_pieces=None):
        if owned_pieces is None:
            owned_pieces = []
        self.pieces_hashes: list = pieces_hashes  # list of bytes
        self.owned_pieces: list = owned_pieces

    def get_piece_index_to_fetch(self, available_pieces: list) -> int:
        for piece in available_pieces:
            if piece in self.pieces_hashes and piece not in self.owned_pieces:
                return self.pieces_hashes.index(piece)
        return -1

    def add_piece(self, piece: bytes):
        if piece in self.owned_pieces and piece not in self.owned_pieces:
            self.owned_pieces.append(piece)
