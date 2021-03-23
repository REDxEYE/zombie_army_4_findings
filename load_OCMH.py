import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler

sys.path.append(r'F:\PYTHON_STUFF\ZombieArmy4')

from byte_io_ac import ByteIO
from utils import get_pad


def tristrip_to_trilist(polylist):
    trilist = []
    for i in range(len(polylist) - 2):
        if i % 2 == 0:
            trilist.append([
                polylist[i + 0],
                polylist[i + 1],
                polylist[i + 2], ]
            )
        else:
            trilist.append([
                polylist[i + 2],
                polylist[i + 1],
                polylist[i + 0], ]
            )
    return trilist


file = r"D:\SteamLibrary\steamapps\common\ZombieArmy4\UNPACK\chunks\hellbase\OCMH\03288841.chunk"

mesh_name = Path(file).stem
reader = ByteIO(file)

reader.skip(0x10)

vertex_count = reader.read_uint32()
indices_count = reader.read_uint32()

vertices = np.frombuffer(reader.read(3 * 4 * vertex_count), np.float32).reshape((-1, 3))
indices = np.frombuffer(reader.read(indices_count * 2), np.int16).copy()
mone = np.where(indices == -1)[0]
mone = np.hstack([[0], mone])

polygons = []
for i in range(0, len(mone)):
    start = mone[i]
    if i + 1 == len(mone):
        end = len(indices)
    else:
        end = mone[i + 1]
    if indices[start] == -1:
        start += 1
    prev_max = indices[start:end].max()
    trilist = indices[start:end].tolist()
    if len(trilist) % 3 != 0:
        a = math.ceil(len(trilist) / 3) * 3
        trilist.extend([0] * (a - len(trilist)))
        polygons.extend(np.array(trilist).reshape((-1, 3)).tolist())
    else:
        polygons.append(trilist)

mesh_data = bpy.data.meshes.new(f'{mesh_name}_MESH')
mesh_obj = bpy.data.objects.new(f'{mesh_name}', mesh_data)

mesh_data.from_pydata(vertices, [], polygons)
# offset += mesh[2]//3
mesh_data.update()

bpy.context.scene.collection.objects.link(mesh_obj)
