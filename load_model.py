import random
import sys, os
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector, Quaternion, Matrix, Euler

sys.path.append(r'F:\PYTHON_STUFF\ZombieArmy4')

from ZombieArmy4Loader.byte_io_ac import ByteIO
from ZombieArmy4Loader.model import Model
from ZombieArmy4Loader.chunks.hskn import HSKN


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


def create_armature(hskn: HSKN):
    model_name = Path(hskn.name).stem
    armature = bpy.data.armatures.new(f"{model_name}_ARM_DATA")
    armature_obj = bpy.data.objects.new(f"{model_name}_ARM", armature)
    armature_obj.show_in_front = True
    bpy.context.scene.collection.objects.link(armature_obj)

    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj

    bpy.ops.object.mode_set(mode='EDIT')
    bl_bones = []
    for n, bone in enumerate(hskn.bones):
        parent_id = hskn.bone_parents[n]
        bl_bone = armature.edit_bones.new(bone.name)
        bl_bone.tail = (Vector([0, 0, 0.1])) + bl_bone.head
        bl_bones.append(bl_bone)
        if n != 0:
            bl_bone.parent = armature.edit_bones.get(hskn.bones[parent_id].name)
    bl_bones.clear()

    bpy.ops.object.mode_set(mode='POSE')
    for n, bone in enumerate(hskn.bones):
        bone_pos_rot = hskn.pos_rot_data[n]
        bl_bone = armature_obj.pose.bones.get(bone.name)
        x, y, z = bone_pos_rot.pos
        pos = Vector([x, y, z])
        w, x, y, z = bone_pos_rot.rot
        rot = Quaternion([x, -y, -z, w])
        rot.rotate(Euler([math.radians(0), math.radians(180), math.radians(0)]))
        mat = Matrix.Translation(pos) @ rot.to_matrix().to_4x4()
        bl_bone.matrix_basis.identity()

        bl_bone.matrix = bl_bone.parent.matrix @ mat if bl_bone.parent else mat
    bpy.ops.pose.armature_apply()
    bpy.ops.object.mode_set(mode='OBJECT')

    return armature_obj


def import_model(model_path: Path):
    assert model_path.exists(), f'Missing "{model_path}" file'
    skeleton_path = model_path.with_suffix('.skeleton')
    if skeleton_path.exists():
        skeleton_reader = ByteIO(skeleton_path)
        hskn_file = HSKN(skeleton_reader)
        armature = create_armature(hskn_file)
    else:
        hskn_file = None
        armature = None
    mesh_reader = ByteIO(model_path)

    mesh_name = Path(model_path).stem
    model_file = Model(mesh_reader)

    vertex_data = model_file.vertex_data

    pos = ((vertex_data['pos'] / 32767) * (model_file.scale / 2)) + model_file.offset / 2
    normals = vertex_data['unk'].copy() / 32768
    unk_const = vertex_data['unk_const']

    mesh_data = bpy.data.meshes.new(f'{mesh_name}_MESH')
    mesh_obj = bpy.data.objects.new(f'{mesh_name}', mesh_data)

    mesh_data.from_pydata(pos, [], model_file.indices.tolist())
    mesh_data.update()
    if armature:
        modifier = mesh_obj.modifiers.new(
            type="ARMATURE", name="Armature")
        modifier.object = armature
        mesh_obj.parent = armature

    # offset = 0
    material_indices_array = np.array([], dtype=np.uint32)
    for mesh in model_file.meshes:
        mesh_polygon_count = mesh.indices_count // 3
        mat_name = f'{mesh.key:08X}'
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
    if hskn_file:
        bone_names = [bone.name for bone in hskn_file.bones]
    else:
        bone_names = [f"bone_{a}" for a in np.unique(vertex_data['bone_ids'])]

    weight_groups = {bone: mesh_obj.vertex_groups.new(name=bone) for bone in bone_names}

    for n, (bone_indices, bone_weights) in enumerate(zip(vertex_data['bone_ids'], vertex_data['weights'] / 255)):
        for bone_index, weight in zip(bone_indices, bone_weights):
            if weight > 0.0:
                weight_groups[bone_names[bone_index]].add([n], weight, 'REPLACE')

    bpy.context.scene.collection.objects.link(mesh_obj)


if __name__ == '__main__':
    file_path = Path(r"D:\SteamLibrary\steamapps\common\ZombieArmy4\UNPACK\witheredzombie_n.model")
    import_model(file_path)
