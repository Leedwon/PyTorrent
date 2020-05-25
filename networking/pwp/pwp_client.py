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
            print(f'is_data_valid = {is_data_valid}')
            if is_data_valid and not self.has_shook_hands:
                await self._send_handshake(writer)

        server = await asyncio.start_server(handler, '0.0.0.0', 8888)
        async with server:
            print("serving")
            await server.serve_forever()

    async def handshake(self, url_port) -> bool:
        url = url_port[:-5]  # last 4 chars are for port
        port: str = url_port[-4:]

        reader, writer = await asyncio.open_connection(host=url, port=int(port))

        await self._send_handshake(writer)
        read_and_validate = await self._read_handshake_and_validate(reader)
        print(f'read and validate = {read_and_validate}')

        writer.close()
        return read_and_validate

    async def _send_handshake(self, writer):
        print("sending handshake")
        data_to_send = self._prepare_data_to_send()
        print(f'data to send length {len(data_to_send)}')

        writer.write(data_to_send)
        self.has_shook_hands = True
        await writer.drain()

    # is there more elegant solution?
    async def _read_handshake_and_validate(self, reader) -> bool:
        # try reading every 5sec for 1min todo make more generic solution to reuse later
        async def read_data():
            while True:
                data = await reader.read(self.handshake_bytes_length)
                print(f'received handshake data = ${data}')
                if len(data) == self.handshake_bytes_length:
                    return self.is_handshake_data_valid(data)
                else:
                    await asyncio.sleep(5)

        try:
            return await asyncio.wait_for(read_data(), timeout=60)
        except asyncio.TimeoutError:
            return False

    def _prepare_data_to_send(self) -> bytes:
        name_length = 19
        protocol_name = b'BitTorrent protocol'
        reserved = b'12345678'  # 8 bytes are reserved change to sth better
        peer_id = self.peer_id[:20]  # peer id can't be longer than 20 bytes

        to_send: bytes = bytes([name_length])  # has to be called on iterable
        to_send = to_send + protocol_name
        to_send = to_send + reserved
        to_send = to_send + self.meta_file.info_hash
        to_send = to_send + bytes(
            peer_id.encode())  # todo should it be utf8 encoded? if so find a way to encode and still stay on 68bytes
        return to_send

    def is_handshake_data_valid(self, data: bytes) -> bool:
        name_length_check = data[0] == 19
        protocol_name_check = data[1:20] == b'BitTorrent protocol'
        info_hash: bytes = data[28:48]
        peer_id: str = data[48:68].decode()
        info_hash_check = info_hash == self.meta_file.info_hash
        peer_id_check = peer_id not in self.served_peers
        return name_length_check and protocol_name_check and info_hash_check and peer_id_check
