import random
import sys, os
from pathlib import Path

import bpy
import numpy as np

from ZombieArmy4Loader.byte_io_ac import ByteIO

sys.path.append(r'F:\PYTHON_STUFF\ZombieArmy4')



def get_material(mat_name, model_ob):
    md = model_ob.data
    mat = bpy.data.materials.get(mat_name, None)
    if mat:
        if md.materials.get(mat.name, None):
            for i, material in enumerate(md.materials):
                if material == mat:
                    return i
        else:
            md.materials.append(mat)
            return len(md.materials) - 1
    else:
        mat = bpy.data.materials.new(mat_name)
        mat.diffuse_color = [random.uniform(.4, 1) for _ in range(3)] + [1.0]
        md.materials.append(mat)
        return len(md.materials) - 1


file = r"D:\SteamLibrary\steamapps\common\ZombieArmy4\UNPACK\inst (static).model"

mesh_name = Path(file).stem

reader = ByteIO(file)

vertices_count = reader.read_uint32()
indices_count = reader.read_uint32()
polygon_count = reader.read_uint32()

meshes = []

vertices_dtype = np.dtype(
    [
        ('pos', np.uint16, (3,)),
        ('minus_one', np.int16, (1,)),
        ("uv_0", np.float16, (2,)),
        ("uv_1", np.float16, (2,)),
        ("unk1", np.uint8, (2,)),
        ('normals', np.int16, (3,)),
    ]
)

vertex_data = np.frombuffer(reader.read(vertices_count * vertices_dtype.itemsize), dtype=vertices_dtype)
pos = ((vertex_data['pos'] / 32767))

indices = np.frombuffer(reader.read(indices_count * 2), dtype=np.uint16).reshape((-1, 3)).astype(np.uint32)

splits = np.where((indices == [0, 1, 2]).sum(axis=1) == 3)[0]
offsets = [0]
for i in range(0, len(splits)):
    start = splits[i]
    if i + 1 == len(splits):
        end = len(indices)
    else:
        end = splits[i + 1]
    prev_max = indices[start:end].max()
    indices[start:end] += offsets[-1]+1
    offsets.append(prev_max + offsets[-1])

limit = splits[10]

mesh_data = bpy.data.meshes.new(f'{mesh_name}_MESH')
mesh_obj = bpy.data.objects.new(f'{mesh_name}', mesh_data)

mesh_data.from_pydata(pos, [], indices[:limit].tolist())
mesh_data.update()

vertex_indices = np.zeros((len(mesh_data.loops, )), dtype=np.uint32)
mesh_data.loops.foreach_get('vertex_index', vertex_indices)

uv_layer = mesh_data.uv_layers.new()
uv_data = uv_layer.data
uv_0 = vertex_data['uv_0'].copy()
uv_0[:, 1] = 1 - uv_0[:, 1]
uv_data.foreach_set('uv', uv_0[vertex_indices].flatten())

uv_layer = mesh_data.uv_layers.new()
uv_data = uv_layer.data
uv_1 = vertex_data['uv_1'].copy()
uv_1[:, 1] = 1 - uv_0[:, 1]
uv_data.foreach_set('uv', uv_1[vertex_indices].flatten())

bpy.context.scene.collection.objects.link(mesh_obj)
