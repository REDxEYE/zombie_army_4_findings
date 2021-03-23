import random
import sys, os
from pathlib import Path

import bpy
import numpy as np

sys.path.append(r'F:\PYTHON_STUFF\ZombieArmy4')

from byte_io_ac import ByteIO


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


file = r"D:\SteamLibrary\steamapps\common\ZombieArmy4\UNPACK\zombie_tank_body.model"

mesh_name = Path(file).stem

reader = ByteIO(file)

mesh_count = reader.read_uint32()
vertices_count = reader.read_uint32()
indices_count = reader.read_uint32()
polygon_count = reader.read_uint32()
unk_count = reader.read_uint32()

vertices_dtype = np.dtype(
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

mesh_dtype = np.dtype(
    [
        ('unk1', np.uint32, (1,)),
        ('unk2', np.uint32, (1,)),
        ('indices_count', np.uint32, (1,)),
        ('unk3', np.uint32, (1,)),
        ('unk4', np.uint32, (1,)),
        ('unk5', np.uint32, (1,)),

    ]
)

# meshes:np.ndarray = np.frombuffer(reader.read(mesh_dtype.itemsize * mesh_count), mesh_dtype)
meshes: np.ndarray = np.frombuffer(reader.read(mesh_count * 6 * 4), np.uint32).reshape((-1, 6))
bbox = reader.read_fmt('6f')
bmax = np.array(bbox[:3])
bmin = np.array(bbox[3:]) * 2

vertex_data = np.frombuffer(reader.read(vertices_count * 48), dtype=vertices_dtype)
indices = np.frombuffer(reader.read(polygon_count * 3 * 2), dtype=np.uint16).reshape((-1, 3))

# offset = 0
# for mesh in meshes:
#     mesh_name += str(mesh[0])

pos = ((vertex_data['pos'] / 32767) * -bmax) - bmin
normals = vertex_data['unk'].copy() / 32768
unk_const = vertex_data['unk_const']

mesh_data = bpy.data.meshes.new(f'{mesh_name}_MESH')
mesh_obj = bpy.data.objects.new(f'{mesh_name}', mesh_data)

# mesh_data.from_pydata(pos, [], indices[offset:offset + mesh[2]//3].tolist())
mesh_data.from_pydata(pos, [], indices.tolist())
# offset += mesh[2]//3
mesh_data.update()

# offset = 0
material_indices_array = np.array([], dtype=np.uint32)
for mesh_key, _, mesh_indices_count, _, _, _ in meshes:
    mesh_polygon_count = mesh_indices_count // 3
    mat_name = f'{mesh_key:08X}'
    mat_id = get_material(mat_name, mesh_obj)
    material_indices_array = np.hstack([material_indices_array, np.full(mesh_polygon_count, mat_id)])
    # material_indices_array[offset:offset + mesh_polygon_count] = mat_id
    # offset += mesh_polygon_count
mesh_data.polygons.foreach_set('material_index', material_indices_array.tolist())

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

# mesh_data.polygons.foreach_set("use_smooth", np.ones(len(mesh_data.polygons)))
# mesh_data.normals_split_custom_set_from_vertices(normals)
# mesh_data.use_auto_smooth = True

bone_names = [f'bone_{a}' for a in np.unique(vertex_data['bone_ids'])]

weight_groups = {bone: mesh_obj.vertex_groups.new(name=bone) for bone in bone_names}

for n, (bone_indices, bone_weights) in enumerate(zip(vertex_data['bone_ids'], vertex_data['weights'] / 255)):
    for bone_index, weight in zip(bone_indices, bone_weights):
        if weight > 0.0:
            weight_groups[f'bone_{bone_index}'].add([n], weight, 'REPLACE')

bpy.context.scene.collection.objects.link(mesh_obj)
