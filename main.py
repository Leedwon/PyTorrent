import asyncio
from uuid import uuid1

from model.peer import Peer
from networking.pwp.handshake_manager import HandshakeManager
from networking.pwp.pwp_connections_manager import PwpConnectionsManager
from networking.pwp.pwp_pieces_manager import PwpPiecesManager
from torrent_reader import TorrentFileReader

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

    piecesManager = PwpPiecesManager(meta_file.torrent_file.piece_hashes)
    connManager = PwpConnectionsManager(
        pieces_manager=piecesManager,
        handshake_manager=handshake_manager,
        peers=empty_peers,
        should_serve=True
    )

    # todo asyncio.run start's a server but since there is no connection the whole process finishes instantly this run forever workaround works for now but find some different solution
    # asyncio.run(connManager.run())
    asyncio.get_event_loop().create_task(connManager.run()).get_loop().run_forever()
