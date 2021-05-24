from typing import List

from ZombieArmy4Loader.byte_io_ac import ByteIO
from .header import ChunkHeader


class PosRot:
    def __init__(self, reader: ByteIO):
        self.pos = reader.read_fmt('3f')
        self.rot = reader.read_fmt('4f')


class Bone:
    def __init__(self, reader: ByteIO, version: int):
        self.name = reader.read_ascii_padded()
        if version >= 10:
            self.unk_0 = reader.read_uint8()
        self.unk_1 = reader.read_uint32()
        if self.unk_1:
            self.bone_data = reader.read(self.unk_1)

    def __repr__(self):
        return f"Bone(\"{self.name}\")"


class HSKN:

    def __init__(self, reader: ByteIO):
        self.header = ChunkHeader(reader)
        version = self.header.version
        flags = self.header.flags
        self.unk, self.bone_count = reader.read_fmt('2I')
        self.name = reader.read_ascii_padded()

        if self.unk and not (flags & 0x40):
            if version >= 25:
                reader.skip(144)
            else:
                reader.skip(72)

        self.bone_parents = reader.read_fmt(f'{self.bone_count}I')
        self.pos_rot_data = [PosRot(reader) for _ in range(self.bone_count)]

        if version >= 10:
            self.unk_byte = reader.read_uint8()
        self.bones: List[Bone] = [Bone(reader, version) for _ in range(self.bone_count)]

        if version >= 5 and (flags & 2) != 0:
            self.unk_5 = reader.read_fmt('6I')

        if version >= 6 and (flags & 4) != 0:
            self.unk_4 = reader.read_uint32()

        if version >= 7:
            self.unk_5 = reader.read_fmt(f'{self.bone_count}I')

        if version >= 8 and (flags & 0x10) != 0:
            self.unk_6 = [reader.read(28) for _ in range(self.bone_count)]

        if version >= 9 and (flags & 0x20) != 0:
            self.unk_7 = reader.read_fmt(f'{self.bone_count}I')

        if version >= 11:
            self.unk_8 = reader.read_uint32()

        if (flags & 0x00FF) != 0 and version >= 12:
            self.unk_9 = reader.read_uint32()
            if self.bone_count > 0:
                self.unk_10 = reader.read_fmt(f'{self.bone_count}I')

        if version >= 13:
            self.unk_11 = reader.read_uint32()
