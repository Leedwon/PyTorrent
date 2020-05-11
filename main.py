import asyncio
from uuid import uuid1
from networking.pwp.pwp_client import PWPClient
from torrent_reader import TorrentFileReader

async def run_server():
    server = await asyncio.start_server(pwp_client.handle_handshake, '127.0.0.1', 8888)
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    torrent = TorrentFileReader.read_file('test_resources/test.jpg.torrent')
    print(str(torrent))
    url = '192.168.100.26:8888'
    info_hash = torrent.info.pieces[:20]  # first piece for testing reasons hash length is 20 todo move to separate var
    print(info_hash)
    uuid = uuid1()
    pwp_client = PWPClient()
    asyncio.run(pwp_client.handshake(url, info_hash, str(uuid)))
    #asyncio.run(run_server())
