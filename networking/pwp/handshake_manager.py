HANDSHAKE_LENGTH = 68


# todo raise detailed errors when handshake fails instead of checking if its valid in create_connection_and_handshake
# todo add checking peer's id we know it from thp now peer_id - our peer_id
class HandshakeManager:
    def __init__(self, meta_file_info_hash: bytes, peer_id: str, served_peers: list):
        self.meta_file_info_hash = meta_file_info_hash
        self.served_peers = served_peers
        self.peer_id = peer_id

    def prepare_data_to_send(self) -> bytes:
        name_length = 19
        protocol_name = b'BitTorrent protocol'
        reserved = b'12345678'  # 8 bytes are reserved change to sth better
        peer_id = self.peer_id[:20]  # peer id can't be longer than 20 bytes
        to_send: bytes = bytes([name_length])  # has to be called on iterable
        to_send += protocol_name
        to_send += reserved
        to_send += self.meta_file_info_hash
        to_send += bytes(
            peer_id.encode())  # todo should it be utf8 encoded? if so find a way to encode and still stay on 68bytes
        return to_send

    def is_handshake_data_valid(self, data: bytes) -> bool:
        if len(data) != HANDSHAKE_LENGTH:
            return False
        name_length_check = data[0] == 19
        protocol_name_check = data[1:20] == b'BitTorrent protocol'
        info_hash: bytes = data[28:48]
        peer_id: str = data[48:68].decode()
        info_hash_check = info_hash == self.meta_file_info_hash
        peer_id_check = peer_id not in self.served_peers
        return name_length_check and protocol_name_check and info_hash_check and peer_id_check
