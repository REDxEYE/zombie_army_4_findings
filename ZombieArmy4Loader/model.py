import numpy as np

from ZombieArmy4Loader.byte_io_ac import ByteIO


class Mesh:
    def __init__(self, reader: ByteIO):
        (self.key, self.unk_1, self.indices_count,
         self.unk_2, self.unk_3, self.unk_4) = reader.read_fmt('6I')


class Model:
    vertices_se4_dtype = np.dtype(
        [
            ('pos', np.uint16, (3,)),
            ('minus_one', np.int16, (1,)),
            ('normals', np.int16, (3,)),
            ('unk', np.int16, (3,)),
            ('unk_const', np.uint16, (2,)),
            ("uv_0", np.float16, (2,)),
            ("uv_1", np.float16, (2,)),
            ("weights", np.uint8, (8,)),
            ("bone_ids", np.uint8, (8,)),
        ]
    )
    vertices_se3_dtype = np.dtype(
        [
            ('pos', np.uint16, (3,)),
            ('minus_one', np.int16, (1,)),
            ("uv_0", np.float16, (2,)),
            ('normals', np.int16, (3,)),
            ('unk', np.int8, (10,)),
            ("uv_1", np.float16, (2,)),
            ("weights", np.uint8, (4,)),
            ("bone_ids", np.uint8, (4,)),
        ]
    )

    def __init__(self, reader: ByteIO, is_se3=False):
        mesh_count, vertices_count, indices_count, polygon_count, unk_count = reader.read_fmt('5I')
        self.meshes = [Mesh(reader) for _ in range(mesh_count)]
        self.scale = np.array(reader.read_fmt('3f'), dtype=np.float32)
        self.offset = np.multiply(reader.read_fmt('3f'), 2, dtype=np.float32)
        vertex_type = self.vertices_se3_dtype if is_se3 else self.vertices_se4_dtype
        self.vertex_data = np.frombuffer(reader.read(vertices_count * vertex_type.itemsize),
                                         dtype=vertex_type)
        self.indices = np.frombuffer(reader.read(indices_count * 2), dtype=np.uint16).reshape((-1, 3))
