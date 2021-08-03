import struct

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

def readInt16(file):
    return readShort(file)

def readUInt16(file):
    return readUShort(file)

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
