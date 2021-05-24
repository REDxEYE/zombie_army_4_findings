import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler

sys.path.append(r'F:\PYTHON_STUFF\ZombieArmy4')

from byte_io_ac import ByteIO
from utils import get_pad

file = r"D:\SteamLibrary\steamapps\common\ZombieArmy4\UNPACK\chunks\common\HMPT\1a1e3020.chunk"

class Bone:
    def __init__(self, reader: ByteIO):
        (self.unk_0, self.unk_1, self.unk_2) = reader.read_fmt('3I')
        self.pos = reader.read_fmt('3f')
        self.unk_3 = reader.read_fmt('3f')
        self.unk_4 = reader.read_fmt('3f')
        self.unk_5 = reader.read_uint32()
        self.name = reader.read_ascii_string()
        reader.skip(get_pad(self.name))

    def __str__(self):
        return f'Bone({self.name})'


mesh_name = Path(file).stem
reader = ByteIO(file)

reader.skip(0x10)

bone_count = reader.read_uint32()
skeleton_name = reader.read_ascii_string()
reader.skip(get_pad(skeleton_name))
bones = []
for _ in range(bone_count):
    bone = Bone(reader)
    bones.append(bone)

temp = np.array([a.unk_5 for a in bones]).reshape((-1,1))

armature = bpy.data.armatures.new(f"{skeleton_name}_ARM_DATA")
armature_obj = bpy.data.objects.new(f"{skeleton_name}_ARM", armature)
armature_obj.show_in_front = True
bpy.context.scene.collection.objects.link(armature_obj)

armature_obj.select_set(True)
bpy.context.view_layer.objects.active = armature_obj

bpy.ops.object.mode_set(mode='EDIT')
bl_bones = []
for bone in bones:
    bl_bone = armature.edit_bones.new(bone.name)
    bl_bones.append(bl_bone)
    bl_bone.head = Vector(bone.unk_3)
    bl_bone.tail = (Vector([0, 0, 1])) + bl_bone.head
#
# for bl_bone, s_bone in zip(bl_bones, bones):
#     if s_bone.parent_bone_index != -1:
#         bl_parent = bl_bones[s_bone.parent_bone_index]
#         bl_bone.parent = bl_parent
# bpy.ops.object.mode_set(mode='POSE')
# for se_bone in bones:
#     bl_bone = armature_obj.pose.bones.get(se_bone.name)
#     pos = Vector(se_bone.position) * 4
#     rot = Euler(se_bone.rotation)
#     mat = Matrix.Translation(pos) @ rot.to_matrix().to_4x4()
#     bl_bone.matrix_basis.identity()
