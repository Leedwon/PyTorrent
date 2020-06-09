import os
from asyncio import Lock


class FileManager:
    def __init__(self, filepath):
        self.filepath = filepath
        self.file_bytes = None
        self.lock = Lock()

        self._init()

    def _init(self):
        if not os.path.isfile(self.filepath):
            f = open(self.filepath, 'a')
            f.close()

        with open(self.filepath, 'rb') as file:
            self.file_bytes = file.read()

    async def write_with_offset_and_update_file_bytes(self, offset: int, data: bytes):
        # todo refactor to not read entire file with each piece write?
        async with self.lock:
            with open(self.filepath, 'r+b') as file:
                self.file_bytes = file.read()
                new_data = self.file_bytes[0:offset] + data + self.file_bytes[offset:]
                self.file_bytes = new_data
                file.seek(0)
                file.write(new_data)

    async def get_data(self, offset, length) -> bytes:
        async with self.lock:
            return self.file_bytes[offset: offset + length]
