import asyncio


class PWPClient:
    def __init__(self):
        self.handshake_bytes_length = 68

    async def handshake(self, url_port, info_hash: bytes, peer_id: str):
        data_to_send = self.prepare_data_to_send(info_hash, peer_id)

        url = url_port[:-5]  # last 4 chars are for port
        port: str = url_port[-4:]

        reader, writer = await asyncio.open_connection(host=url, port=int(port))

        print(f'data to send length {len(data_to_send)}')

        writer.write(data_to_send)
        await writer.drain()
        writer.close()

        # data = await reader.read(handshake_bytes_length)

    def prepare_data_to_send(self, info_hash: bytes, peer_id: str) -> bytearray:
        name_length = 19
        protocol_name = b'BitTorrent protocol'
        reserved = b'12345678'  # 8 bytes are reserved
        peer_id = peer_id[:20] #peer id can't be longer than 20 bytes

        data_to_send = bytearray()
        data_to_send.append(name_length)
        data_to_send.extend(protocol_name)
        data_to_send.extend(reserved)
        data_to_send.extend(info_hash)
        data_to_send.extend(peer_id.encode(encoding='utf-8'))
        return data_to_send

    async def handle_handshake(self, reader, writer):
        data = await reader.read(self.handshake_bytes_length)
        print(data)
        print(data.decode())
