from enum import IntEnum
from pathlib import Path
from typing import List

from ZombieArmy4Loader.byte_io_ac import ByteIO
from .header import ChunkHeader


class ContentType(IntEnum):
    Model = 1
    Texture = 2


class RSFL:

    def __init__(self, reader: ByteIO):
        self._reader = reader
        self.header = ChunkHeader(reader)

        file_count = reader.read_uint32()
        self._files_data = []
        for _ in range(file_count):
            filename = reader.read_ascii_padded()

            if filename[0] == '\\':
                filename = filename[1:]
            filename = Path(filename)
            relative_file_offset, file_size, unk = reader.read_fmt('3I')
            file_offset = relative_file_offset + self.header.size
            self._files_data.append((file_offset, file_size, filename))

    @property
    def file_ids(self):
        return range(len(self._files_data))

    def file_info(self, file_id):
        file_data = self._files_data[file_id]
        return file_data[1], file_data[2]

    def file_data(self, file_id):
        reader = self._reader
        file_data = self._files_data[file_id]
        with reader.save_current_pos():
            reader.seek(file_data[0])
            data = reader.read(file_data[1])
        return data
