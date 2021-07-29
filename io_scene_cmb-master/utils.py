import struct
import math
import mathutils
from .cmbEnums import DataTypes

def getFlag(value, index, increment):
    index += increment
    return ((value >> index) & 1) != 0

def align(file, size = 4):
    while(file.tell() % size): file.seek(file.tell() + 1)

def readUByte(file):
	return struct.unpack("B", file.read(1))[0]

def readByte(file):
	return struct.unpack("b", file.read(1))[0]

def readBytes(file, count):
    return [readUByte(file) for _ in range(count)]

def readUShort(file):
	return struct.unpack("<H", file.read(2))[0]

def readShort(file):
	return struct.unpack("<h", file.read(2))[0]

def readUInt32(file):
	return struct.unpack("<I", file.read(4))[0]

def readInt32(file):
	return struct.unpack("<i", file.read(4))[0]

def readFloat(file):
    return struct.unpack("<f", file.read(4))[0]

# Note: Default data type is float
def readArray(file, elements, datatype = 0):
    return [readDataType(file, datatype) for _ in range(elements)]

def readDataType(file, dt):
    if  (dt == DataTypes.Byte):   return readByte(file)
    elif(dt == DataTypes.UByte):  return readUByte(file)
    elif(dt == DataTypes.Short):  return readShort(file)
    elif(dt == DataTypes.UShort): return readUShort(file)
    elif(dt == DataTypes.Int):    return readInt32(file)
    elif(dt == DataTypes.UInt):   return readUInt32(file)
    else:                         return readFloat(file)

def getDataTypeSize(dt):
    if(dt == DataTypes.Byte or dt == DataTypes.UByte): return 1
    elif(dt == DataTypes.Short or dt == DataTypes.UShort): return 2
    else: return 4
        
def readString(file, length = 0):
    if(length > 0): return file.read(length).decode("ASCII").replace("\x00", '')
    else: return ''.join(iter(lambda: file.read(1).decode('ascii'), '\x00' and ''))
    # The "and" is required or else python will loop forever if you hit the end of the file


# Ported from OpenTK 
# blender might have something but I'm too lazy to check
def dot(left, right):
    return left[0] * right.x + left[1] * right.y + left[2] * right.z

def transformPosition(pos, mat):
    p = [0.0, 0.0, 0.0]
    p[0] = dot(pos, mat.col[0].xyz) + mat.row[3].x
    p[1] = dot(pos, mat.col[1].xyz) + mat.row[3].y
    p[2] = dot(pos, mat.col[2].xyz) + mat.row[3].z
    return p

def transformNormalInverse(norm, invMat):
    n = [0.0, 0.0, 0.0]
    n[0] = dot(norm, invMat[0].xyz)
    n[1] = dot(norm, invMat[1].xyz)
    n[2] = dot(norm, invMat[2].xyz)
    return n

def transformNormal(norm, mat):
    invMat = mat.inverted()
    return transformNormalInverse(norm, invMat)

# Taken from https://gitlab.com/Worldblender/io_scene_numdlb (Thank you!)
def getWorldTransform(bones, i):
    T = bones[i].translation
    S = bones[i].scale
    R = bones[i].rotation
    
    T = mathutils.Matrix.Translation(T).to_4x4().transposed()
    Sm = mathutils.Matrix.Translation((0, 0, 0)).to_4x4()
    Sm[0][0] = S[0]
    Sm[1][1] = S[1]
    Sm[2][2] = S[2]
    S = Sm
    R = fromEulerAngles(R).to_matrix().to_4x4().transposed()

    if (bones[i].parentId != -1): P = getWorldTransform(bones, bones[i].parentId)
    else: P = mathutils.Matrix.Translation((0, 0, 0)).to_4x4()
    M = mathutils.Matrix.Translation((0, 0, 0)).to_4x4()

    M = M * S
    M = M * R
    M = M * T
    M = M * P

    return M

def fromAxisAngle(axis, angle):
    return mathutils.Quaternion((
        math.cos(angle / 2),
        axis[0] * math.sin(angle / 2),
        axis[1] * math.sin(angle / 2),
        axis[2] * math.sin(angle / 2),
    ))

def fromEulerAngles(rot):
    x = fromAxisAngle((1,0,0), rot[0])
    y = fromAxisAngle((0,1,0), rot[1])
    z = fromAxisAngle((0,0,1), rot[2])
    q = z * y * x
    if q.w < 0: q *= -1
    return q