from ZombieArmy4Loader.byte_io_ac import ByteIO


class ChunkHeader:

    def __init__(self, reader: ByteIO):
        self.chunk_name = reader.read_ascii_string(4).strip()
        self.size = reader.read_uint32()
        self.version = reader.read_int32()
        self.flags = reader.read_uint32()
