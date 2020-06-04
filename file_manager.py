from asyncio import Lock


class FileManager:
    def __init__(self, filepath):
        self.filepath = filepath
        self.file_bytes = None
        self.lock = Lock()

        self._init()

    def _init(self):
        file = open(self.filepath, 'a+')
        file.close()

        with open(self.filepath, 'rb') as file:
            self.file_bytes = file.read()

    async def write_with_offset_and_update_file_bytes(self, offset: int, data: bytes):
        async with self.lock:
            with open(self.filepath, 'wb') as file:
                file.seek(offset)
                file.write(data)

            # todo refcator to not perfom reading whole file
            with open(self.filepath, 'rb') as file:
                self.file_bytes = file.read()
