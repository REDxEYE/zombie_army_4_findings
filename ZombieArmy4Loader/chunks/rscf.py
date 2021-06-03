from enum import IntEnum
from pathlib import Path
from typing import List

from ZombieArmy4Loader.byte_io_ac import ByteIO
from .header import ChunkHeader


class ContentType(IntEnum):
    Model = 0
    Texture = 2


class RSCF:

    def __init__(self, reader: ByteIO):
        self._reader = reader
        self.header = ChunkHeader(reader)

        self.ctype = reader.read_uint32()
        self.dummy = reader.read_uint32()
        self.size = reader.read_uint32()
        filename = reader.read_ascii_padded()

        if filename[0] == '\\':
            filename = filename[1:]
        self.filename = Path(filename)
        if self.ctype == ContentType.Model:
            self.filename = self.filename.with_suffix('.model')
        elif self.ctype == ContentType.Texture:
            self.filename = self.filename.with_suffix('.dds')

        self._data_offset = reader.tell()
        reader.skip(self.size)

    @property
    def data(self):
        with self._reader.save_current_pos():
            self._reader.seek(self._data_offset)
            data = self._reader.read(self.size)
        return data
