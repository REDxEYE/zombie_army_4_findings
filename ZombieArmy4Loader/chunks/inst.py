from enum import IntEnum
from pathlib import Path
from typing import List

from ZombieArmy4Loader.byte_io_ac import ByteIO
from ZombieArmy4Loader.chunks.header import ChunkHeader


class PropPos:
    def __init__(self, reader: ByteIO):
        self.offset = reader.read_fmt('3f')
        self.unk = reader.read(52)


# noinspection PyPep8Naming
class BlockV15_V16:
    def __init__(self, reader: ByteIO):
        self.unk = reader.read(60)


class BlockV18:
    def __init__(self, reader: ByteIO):
        self.unk = reader.read_fmt('4I')
        self.unk2_vec3 = reader.read_fmt('3f')
        self.unk3 = reader.read_fmt('4I')
        self.unk4_vec2 = reader.read_fmt('2f')
        self.unk5, self.unk6_id, self.unk7 = reader.read_fmt('3I')


class Block2:
    def __init__(self, reader: ByteIO):
        (self.unk,
         self.unk1_count, self.unk2_count,
         self.unk3_zero, self.unk4_offset,
         self.unk5_zero, self.unk6_offset,
         self.unk7_start, self.unk8_count, self.unk9_zero) = reader.read_fmt('10i')
        self.offset = reader.read_fmt('3f')
        self.scale = reader.read_fmt('3f')


class INST:
    def __init__(self, reader: ByteIO):
        self._reader = reader
        header = self.header = ChunkHeader(reader)
        pos_count = reader.read_uint32()
        self.pose_blocks = [PropPos(reader) for _ in range(pos_count)]
        block_count = reader.read_uint32()
        if header.version < 18:
            self.unk_v18 = reader.read_fmt('5I')
        if header.version in (15, 16):
            self.blocks = [BlockV15_V16(reader) for _ in range(block_count)]
        else:
            self.blocks = [BlockV18(reader) for _ in range(block_count)]
        block2_count = reader.read_uint32()
        self.blocks2 = [Block2(reader) for _ in range(block2_count)]


if __name__ == '__main__':
    a = INST(ByteIO(r"D:\SteamLibrary\steamapps\common\ZombieArmy4\UNPACK\chunks\h_hellbase\INST\103c3832.chunk"))
    print(a)
