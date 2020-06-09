import asyncio
from uuid import uuid1

from file_manager import FileManager
from model.peer import Peer
from networking.pwp.handshake_manager import HandshakeManager
from networking.pwp.pwp_connections_manager import PwpConnectionsManager
from networking.pwp.pwp_pieces_manager import PwpPiecesManager
from torrent_reader import TorrentFileReader

# todo add logic for multi file torrents
if __name__ == '__main__':
    meta_file = TorrentFileReader.read_file('test_resources/test.jpg.torrent')
    print(str(meta_file))
    peer_id = str(uuid1())[:20]
    handshake_manager = HandshakeManager(
        meta_file_info_hash=meta_file.info_hash,
        peer_id=peer_id,
        served_peers=[peer_id]  # todo manage it in pwp_connections_manager?
    )

    empty_peers = []
    non_empty_peers = [Peer('01234567890123456789'[:20], '127.0.0.1', 8888)]

    pieces_manager = PwpPiecesManager(pieces_hashes=meta_file.torrent_file.piece_hashes,
                                      piece_length=meta_file.torrent_file.piece_length,
                                      file_length=meta_file.torrent_file.get_length(),
                                      owned_pieces=meta_file.torrent_file.piece_hashes)

    file_manager = FileManager('test_resources/test.jpg')
    print(len(meta_file.torrent_file.piece_hashes))

    connManager = PwpConnectionsManager(
        pieces_manager=pieces_manager,
        handshake_manager=handshake_manager,
        peers=empty_peers,
        file_manager=file_manager,
        should_serve=True
    )

    asyncio.get_event_loop().create_task(connManager.run()).get_loop().run_forever()
