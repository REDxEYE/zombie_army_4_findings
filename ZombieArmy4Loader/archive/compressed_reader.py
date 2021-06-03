import io
import struct
from pathlib import Path
from typing import Union, BinaryIO
from zlib import decompress
import bisect

from ZombieArmy4Loader.byte_io_ac import ByteIO


class ZlibByteIO(ByteIO):

    def __init__(self, archive_reader: ByteIO, utility_offset, chunked):
        self._archive_reader = archive_reader
        self.file = self._archive_reader.file
        self._uoffset = utility_offset
        self._current_block = io.BytesIO()
        self._chunked = chunked
        if chunked:
            self._compressed_size = self._archive_reader.read_uint32()
            self._decompressed_size = self._archive_reader.read_uint32()
        else:
            self._decompressed_size = self._archive_reader.read_uint32()
        self._decompressed_offset = 0

        self._current_block_offset = 0

        self._offsets = [0]
        self._block_offsets = []
        self._collect_blocks()

    def _collect_blocks(self):
        reader = self._archive_reader
        with reader.save_current_pos():
            accumulator = 0
            while reader:
                compressed_block_size = reader.read_uint32()
                decompressed_block_size = reader.read_uint32()

                if not self._chunked:
                    compressed_block_size = reader.size()
                    compressed_block_size -= self._uoffset
                self._block_offsets.append((reader.tell(), decompressed_block_size, compressed_block_size))
                accumulator += decompressed_block_size
                self._offsets.append(accumulator)
                reader.skip(compressed_block_size)

    @property
    def preview(self):
        return b''

    @property
    def preview_f(self):
        return b''

    def read(self, size=-1) -> bytes:
        left_to_read = size
        buffer = bytearray()
        current_block_offset, current_block_leftover, _ = self._get_offset_and_leftover_bytes()
        while left_to_read > 0 and self._decompressed_offset < self._decompressed_size:
            self._ensure_buffer()
            if current_block_leftover < left_to_read:
                to_read = current_block_leftover
            else:
                to_read = left_to_read
            data_chunk = self._current_block.read(to_read)
            buffer.extend(data_chunk)
            self._decompressed_offset += len(data_chunk)
            left_to_read -= len(data_chunk)
        return buffer

    def _get_offset_and_leftover_bytes(self):
        index = bisect.bisect_right(self._offsets, self._decompressed_offset) - 1
        offset, size, _ = self._block_offsets[index]
        relative_offset = self._offsets[index]
        assert index < len(self._offsets)
        leftover = (relative_offset + size) - self._decompressed_offset
        return offset, leftover, size

    def _ensure_buffer(self):
        block_offset, block_leftover, block_size = self._get_offset_and_leftover_bytes()
        if self._current_block_offset == block_offset:
            self._current_block.seek(block_size - block_leftover)
            return
        self._current_block_offset = block_offset
        self.file.seek(block_offset)
        self._current_block.close()
        self._current_block = io.BytesIO(decompress(self.file.read(block_size)))
        self._current_block.seek(block_size - block_leftover)

    def _read(self, t):
        return struct.unpack(t, self.read(struct.calcsize(t)))[0]

    def read_fmt(self, fmt):
        return struct.unpack(fmt, self.read(struct.calcsize(fmt)))

    def seek(self, off, pos=io.SEEK_SET):
        if pos == io.SEEK_SET:
            self._decompressed_offset = off
        elif pos == io.SEEK_CUR:
            self._decompressed_offset += off
        elif pos == io.SEEK_END:
            self._decompressed_offset = self._decompressed_size - off
        else:
            raise Exception('Invalid operation')

        self._ensure_buffer()

    def skip(self, amount):
        self.seek(amount, io.SEEK_CUR)

    def rewind(self, amount):
        self.seek(amount, io.SEEK_CUR)

    def size(self):
        return self._decompressed_size

    def tell(self):
        return self._decompressed_offset

    def read_ascii_string(self, length=None):
        if length is not None:
            buffer = self.read(length).strip(b'\x00')
            if b'\x00' in buffer:
                buffer = buffer[:buffer.index(b'\x00')]
            return buffer.decode('latin', errors='replace')

        buffer = bytearray()

        while True:
            chunk = self.read(32)
            chunk_end = chunk.find(b'\x00')
            if chunk_end >= 0:
                buffer += chunk[:chunk_end]
            else:
                buffer += chunk
            if chunk_end >= 0:
                self.seek(-(len(chunk) - chunk_end - 1), io.SEEK_CUR)
                return buffer.decode('latin', errors='replace')
