import asyncio
from uuid import uuid1
from networking.pwp.pwp_client import PWPClient
from torrent_reader import TorrentFileReader

if __name__ == '__main__':
    meta_file = TorrentFileReader.read_file('test_resources/test.jpg.torrent')  # read torrent
    print(str(meta_file))
    # generate and store our peer id
    peer_id = str(uuid1())[:20]  # 20bytes long as in protocol docs
    # announce our id and ip + port to tracker
    # todo:: THP protocol read more http://jonas.nitro.dk/bittorrent/bittorrent-rfc.html#RFC2119
    # get url from tracker to connect to
    url_rpi = '192.168.100.26:8888'
    url_local = '127.0.0.1:8888'
    info_hash = meta_file.torrent_file.pieces[0]  # take piece that is missing todo piece choosing algorithm
    # perform handshake / open connection on free port - which peer should initialize connection? does it matter?
    pwp_client = PWPClient(meta_file, peer_id)

    # for test sake we'll try to connect and if error occurs we'll start serving as host
    try:
        asyncio.run(pwp_client.handshake(url_rpi))
    except ConnectionRefusedError:
        asyncio.run((pwp_client.handle_handshake()))
