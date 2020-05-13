import asyncio

from model.meta_info_file import MetaInfoFile


# todo store info about peers to not loop in infinite handshake - that should be provided from the tracker
class PWPClient:
    def __init__(self, meta_file: MetaInfoFile, peer_id: str):
        self.handshake_bytes_length = 68
        self.meta_file = meta_file  # entire torrent file here or just peer? or mb another data structure
        self.peer_id = peer_id
        self.served_peers = [peer_id]
        self.has_shook_hands = False  # todo get rid of it when we get peers infos from tracker for now on just perform handshake once for testing reasons

    # should this be in this class? should return server or just fire it?
    async def handle_handshake(self):
        async def handler(reader, writer):
            is_data_valid = await self._read_handshake_and_validate(reader)
            print(is_data_valid)
            if is_data_valid and not self.has_shook_hands:
                await self._send_handshake(writer)

        server = await asyncio.start_server(handler, '0.0.0.0', 8888)
        async with server:
            await server.serve_forever()

    async def handshake(self, url_port) -> bool:
        url = url_port[:-5]  # last 4 chars are for port
        port: str = url_port[-4:]

        reader, writer = await asyncio.open_connection(host=url, port=int(port))

        await self._send_handshake(writer)
        return await self._read_handshake_and_validate(reader)

    async def _send_handshake(self, writer):
        data_to_send = self._prepare_data_to_send()
        print(f'data to send length {len(data_to_send)}')

        writer.write(data_to_send)
        self.has_shook_hands = True
        await writer.drain()
        writer.close()

    async def _read_handshake_and_validate(self, reader) -> bool:
        data = await reader.read(self.handshake_bytes_length)
        print(f'received handshake data = ${data}')
        return self.is_handshake_data_valid(data)

    def _prepare_data_to_send(self) -> bytearray:
        name_length = 19
        protocol_name = b'BitTorrent protocol'
        reserved = b'12345678'  # 8 bytes are reserved
        peer_id = self.peer_id[:20]  # peer id can't be longer than 20 bytes

        data_to_send = bytearray()
        data_to_send.append(name_length)
        data_to_send.extend(protocol_name)
        data_to_send.extend(reserved)
        data_to_send.extend(self.meta_file.info_hash)
        data_to_send.extend(peer_id.encode(encoding='utf-8'))
        return data_to_send

    def is_handshake_data_valid(self, data: bytearray) -> bool:
        name_length_check = data[0] == 19
        protocol_name_check = data[1:20] == b'BitTorrent protocol'
        info_hash: bytes = data[28:48]
        peer_id: str = data[48:68].decode()
        info_hash_check = info_hash == self.meta_file.info_hash
        peer_id_check = peer_id not in self.served_peers
        return name_length_check and protocol_name_check and info_hash_check and peer_id_check
