import sys, os
from .utils import (align, readDataType, readString, readArray, readFloat,
                    readUInt32, readInt32, readUShort,
                    readShort, readByte, readUByte)
from .cmbEnums import *

Version = CmbVersion.OoT3D

class Cmb(object):
    def __init__(self):
        self.version = Version
        self.name = "Dummy CMB"
        self.texDataOfs = 0
        self.indicesOfs = 0
        self.vatrOfs = 0
        self.skeleton = [Bone()]
        self.materials = [Material()]
        self.textures = [Texture()]
        self.meshes = [Mesh()]
        self.shapes = [Sepd()]
        self.vatr = Vatr()

    def read(self, f, startOff):
        f.seek(startOff)

        header = CmbHeader().read(f)
        skl = Skl().read(f)# Skeleton
        #qtrs = Qtrs().read(f) if (Version > 6) else Qtrs()
        f.seek(header.matsOfs + startOff)
        mat = Mat().read(f)# Materials
        tex = Tex().read(f)# Textures
        sklm = Sklm().read(f)# Skeleton Meshes
        f.seek(header.vatrOfs + startOff)
        vatr = Vatr().read(f)# Vertex Attributes

        # Add face indices to primitive sets
        for shape in sklm.shapes:
            for pset in shape.primitiveSets:
                f.seek((header.faceIndicesOfs + pset.primitive.offset * 2) + startOff)# Always * 2 even if ubyte is used...
                pset.primitive.indices = [int(readDataType(f, pset.primitive.dataType)) for _ in range(pset.primitive.indicesCount)]

        self.skeleton = skl.bones
        self.materials = mat.materials# TODO: Combiners
        self.textures = tex.textures
        self.meshes = sklm.meshes
        self.shapes = sklm.shapes
        self.vatr = vatr

        self.texDataOfs = header.textureDataOfs
        self.indicesOfs = header.faceIndicesOfs
        self.vatrOfs = header.vatrOfs
        self.name = header.name
        self.version = Version

        return self

class CmbHeader(object):
    def __init__(self):
        self.magic = "cmb\x20"
        self.filesize = 0xF8
        self.version = Version
        self.unused = 0# Reserved? (Always 0)
        self.name = "OoT3D dummy MDL"

        self.faceIndicesCount = 0
        self.sklOfs = 68# SKeLeton
        self.qtrsOfs = 0# Mix/Max coordinate of this MODEL. qtrs = "QuaTeRnionS"...?
        self.matsOfs = 0# MATerialS
        self.texOfs  = 0# TEXture
        self.sklmOfs = 0# SKeLetal Model
        self.lutsOfs = 0# LookUpTableS
        self.vatrOfs = 0# Vertex AtTRibutes
        self.faceIndicesOfs = 0# Face indices buffer Offset
        self.textureDataOfs = 0# Texture data buffer Offset
        self.unk0 = 0# Always 0

    def read(self,f):
        self.magic = readString(f, 4)
        self.filesize = readUInt32(f)
        self.version = readUInt32(f)
        self.unused = readUInt32(f)
        self.name = readString(f, 16)
        self.faceIndicesCount = readUInt32(f)
        self.sklOfs = readUInt32(f)
        self.qtrsOfs = readUInt32(f) if (self.version > 6) else 0
        self.matsOfs = readUInt32(f)
        self.texOfs = readUInt32(f)
        self.sklmOfs = readUInt32(f)
        self.lutsOfs = readUInt32(f)
        self.vatrOfs = readUInt32(f)
        self.faceIndicesOfs = readUInt32(f)
        self.textureDataOfs = readUInt32(f)
        self.unk0 = readUInt32(f) if (self.version > 6) else 0

        global Version
        Version = self.version
        return self

class Mesh(object):
    def __init__(self):
        self.shapeIndex = 0
        self.materialIndex = 0
        self.ID = 0

    def read(self,f):
        self.shapeIndex = readUShort(f)
        self.materialIndex = readUByte(f)
        self.ID = readUByte(f)

        # Some of these values are possibly crc32
        if(Version == CmbVersion.MM3D): f.seek(f.tell() + 0x8)
        if(Version == CmbVersion.EverOasis): f.seek(f.tell() + 0xC)
        if(Version == CmbVersion.LM3D): f.seek(f.tell() + 0x54)# LOL Wtf luigi's mansion
        return self

class Primitive(object):
    def __init__(self):
        self.magic = "prm\x20"# PRiMitive
        self.chunkSize = 0
        self.isVisible = True
        self.primitiveMode = PrimitiveMode.Triangles
        self.dataType = DataTypes.UShort
        self.indicesCount = 3
        self.indices = [0,1,2]
        self.offset = 0

    def read(self,f):
        self.magic = readString(f,4)
        self.chunkSize = readUInt32(f)
        self.isVisible = readUInt32(f) != 0
        self.primitiveMode = PrimitiveMode(readUInt32(f))# Other modes don't exist in OoT3D's shader so we'd never know
        self.dataType = DataTypes(readUInt32(f))
        self.indicesCount = readUShort(f)
        self.offset = readUShort(f)
        return self

class PrimitiveSet(object):
    def __init__(self):
        self.magic = "prms"# PRiMitiveSet
        self.chunkSize = 0
        self.primitiveCount = 1
        self.skinningMode = SkinningMode.Single# Rigged to one bone
        self.boneTableCount = 1
        self.boneTableOffset = 24
        self.primitiveOffset = 28
        self.boneTable = [0]
        self.primitive = Primitive()

    def read(self,f):
        self.magic = readString(f, 4)
        self.chunkSize = readUInt32(f)
        self.primitiveCount = readUInt32(f)
        self.skinningMode = readUShort(f)
        self.boneTableCount = readUShort(f)
        self.boneTableOffset = readUInt32(f)
        self.primitiveOffset = readUInt32(f)
        self.boneTable = [readShort(f) for _ in range(self.boneTableCount)]
        align(f)
        self.primitive = Primitive().read(f)# Actually an array but more than one is never used
        return self

class VertexAttribute(object):
    def __init__(self):
        self.start = 0
        self.scale = 1.0
        self.dataType = DataTypes.Float
        self.mode = VertexAttributeMode.Array
        self.constants = [0.0, 0.0, 0.0, 0.0]
    def read(self,f):
        self.start = readUInt32(f)
        self.scale = readFloat(f)
        self.dataType = DataTypes(readUShort(f))
        self.mode = VertexAttributeMode(readUShort(f))
        self.constants = readArray(f, 4)
        return self

class Sepd(object):
    def __init__(self):
        self.magic = "sepd"# SEParateDataShape
        self.chunkSize = 0
        self.primSetCount = 1
        self.vertFlags = 1

        self.meshCenter = [0.0, 0.0, 0.0]
        self.positionOffset = [0.0, 0.0, 0.0]
        self.Mix = [-1.0, -1.0, -1.0]
        self.Max = [0.0, 0.0, 0.0]

        self.position = VertexAttribute()
        self.normal = VertexAttribute()
        self.tangents = VertexAttribute()
        self.color = VertexAttribute()
        self.uv0 = VertexAttribute()
        self.uv1 = VertexAttribute()
        self.uv2 = VertexAttribute()
        self.bIndices = VertexAttribute()
        self.bWeights = VertexAttribute()

        self.boneDimensions = 1
        self.constantFlags = 0
        self.primitiveSets = [PrimitiveSet()]

    def read(self,f):
        self.magic = readString(f,4)
        self.chunkSize = readUInt32(f)
        self.primSetCount = readUShort(f)# PrimitiveSet Count

    #Bit Flags: (HasTangents was added in versions > OoT:3D (aka 6))
        # HasPosition : 00000001
        # HasNormals  : 00000010
        # HasTangents : 00000100 (MM3D/LM3D/EO only)
        # HasColors   : 00000100
        # HasUV0      : 00001000
        # HasUV1      : 00010000
        # HasUV2      : 00100000
        # HasIndices  : 01000000
        # HasWeights  : 10000000
        self.vertFlags = readUShort(f)

        self.meshCenter = readArray(f, 3)
        self.positionOffset = readArray(f, 3)

        if(Version > 12):
            self.Min = readArray(f, 3)# Max coordinate of the shape
            self.Max = readArray(f, 3)# Min coordinate of the shape

        self.position = VertexAttribute().read(f)
        self.normal = VertexAttribute().read(f)
        self.tangents = VertexAttribute().read(f) if (Version > 6) else self.tangents
        self.color = VertexAttribute().read(f)
        self.uv0 = VertexAttribute().read(f)
        self.uv1 = VertexAttribute().read(f)
        self.uv2 = VertexAttribute().read(f)
        self.bIndices = VertexAttribute().read(f)
        self.bWeights = VertexAttribute().read(f)

        self.boneDimensions = readUShort(f)# How many weights each vertex has for this shape

        # Note: Constant values are set in "VertexAttribute" (Use constants instead of an array to save space, assuming all values are the same)
        #Bit Flags:
        # PositionUseConstant : 00000001
        # NormalsUseConstant  : 00000010
        # TangentsUseConstant : 00000100 (MM3D/LM3D/EO only)
        # ColorsUseConstant   : 00000100
        # UV0UseConstant      : 00001000
        # UV1UseConstant      : 00010000
        # UV2UseConstant      : 00100000
        # IndicesUseConstant  : 01000000
        # WeightsUseConstant  : 10000000
        self.constantFlags = readUShort(f)

        [readShort(f) for _ in range(self.primSetCount)]# PrimitiveSetOffset(s)
        align(f)# 4 byte alignment
        self.primitiveSets = [PrimitiveSet().read(f) for _ in range(self.primSetCount)]

        return self

class TexMapper(object):
    def __init__(self):
        self.textureID = -1
        self.minFilter = TextureMinFilter.Linear
        self.magFilter = TextureMagFilter.Linear
        self.wrapS = TextureWrapMode.Repeat
        self.wrapT = TextureWrapMode.Repeat
        self.minLodBias = 0.0
        self.lodBias = 0.0
        self.borderColor = [0,0,0,255]

    def read(self,f):
        self.textureID = readShort(f)# Not an int because "-1" is 0xFFFF0000 and not 0xFFFFFFFF
        readShort(f)# Alignment
        self.minFilter = readUShort(f)
        self.magFilter = readUShort(f)
        self.wrapS = readUShort(f)
        self.wrapT = readUShort(f)
        self.minLodBias = readFloat(f)
        self.lodBias = readFloat(f)
        self.borderColor = readArray(f, 4, DataTypes.UByte)
        return self

class TexCoords(object):
    def __init__(self):
        self.matrixMode = TextureMatrixMode.DccMaya
        self.referenceCameraIndex = 0
        self.mappingMethod = TextureMappingType.UvCoordinateMap
        self.coordinateIndex = 0
        self.scale = [1.0, 1.0]
        self.rotation = 0.0
        self.translation = [0.0, 0.0]

    def read(self,f):
        self.matrixMode = TextureMatrixMode(readUByte(f))
        self.referenceCameraIndex = readUByte(f)
        self.mappingMethod = TextureMappingType(readUByte(f))
        self.coordinateIndex = readUByte(f)
        self.scale = readArray(f, 2)
        self.rotation = readFloat(f)
        self.translation = readArray(f, 2)
        return self

class Sampler(object):
    def __init__(self):
        self.isAbs = False
        self.index = -1
        self.input = LutInput.CosNormalHalf
        self.scale = 1.0
        # TODO: LutScale only accepts these values
        # Quarter = 0.25,
	    # Half = 0.5,
	    # One = 1.0,
	    # Two = 2.0,
	    # Four = 4.0,
	    # Eight = 8.0

    def read(self,f):
        self.isAbs = readUByte(f) != 0
        self.index = readByte(f)
        self.input = LutInput(readUShort(f))
        self.scale = readFloat(f)
        return self

class Combiner(object):
    def __init__(self):
        self.combinerModeColor = TexCombineMode.Modulate
        self.combinerModeAlpha = TexCombineMode.Modulate
        self.scaleColor = TexCombineScale.One
        self.scaleAlpha = TexCombineScale.One
        self.bufferColor = TexCombinerSource.PreviousBuffer
        self.bufferAlpha = TexCombinerSource.PreviousBuffer
        self.sourceColor0 = TexCombinerSource.PrimaryColor
        self.sourceColor1 = TexCombinerSource.Texture0
        self.sourceColor2 = TexCombinerSource.Constant
        self.operandColor0 = TexCombinerColorOp.Color
        self.operandColor1 = TexCombinerColorOp.Color
        self.operandColor2 = TexCombinerColorOp.Color
        self.sourceAlpha0 = TexCombinerSource.PrimaryColor
        self.sourceAlpha1 = TexCombinerSource.Texture0
        self.sourceAlpha2 = TexCombinerSource.Constant
        self.operandAlpha0 = TexCombinerAlphaOp.Alpha
        self.operandAlpha1 = TexCombinerAlphaOp.Alpha
        self.operandAlpha2 = TexCombinerAlphaOp.Alpha
        self.constColorIndex = 0

    def read(self,f):
        self.combinerModeColor = TexCombineMode(readUShort(f))
        self.combinerModeAlpha = TexCombineMode(readUShort(f))
        self.scaleColor = TexCombineScale(readUShort(f))
        self.scaleAlpha = TexCombineScale(readUShort(f))
        self.bufferColor = TexCombinerSource(readUShort(f))
        self.bufferAlpha = TexCombinerSource(readUShort(f))
        self.sourceColor0 = TexCombinerSource(readUShort(f))
        self.sourceColor1 = TexCombinerSource(readUShort(f))
        self.sourceColor2 = TexCombinerSource(readUShort(f))
        self.operandColor0 = TexCombinerColorOp(readUShort(f))
        self.operandColor1 = TexCombinerColorOp(readUShort(f))
        self.operandColor2 = TexCombinerColorOp(readUShort(f))
        self.sourceAlpha0 = TexCombinerSource(readUShort(f))
        self.sourceAlpha1 = TexCombinerSource(readUShort(f))
        self.sourceAlpha2 = TexCombinerSource(readUShort(f))
        self.operandAlpha0 = TexCombinerAlphaOp(readUShort(f))
        self.operandAlpha1 = TexCombinerAlphaOp(readUShort(f))
        self.operandAlpha2 = TexCombinerAlphaOp(readUShort(f))
        self.constColorIndex = readInt32(f)
        return self

class Texture(object):
    def __init__(self):
        self.dataLength = 0
        self.mimapCount = 1
        self.isETC1 = False
        self.isCubemap = False
        self.width = 8
        self.height = 8
        self.imageFormat = GLTextureFormat.RGBA8# Composed of (ushort)PixelFormat + (ushort)DataType (in this order)
        self.dataOffset = 0
        self.name = "Dummy"

    def read(self,f):
        self.dataLength = readUInt32(f)
        self.mimapCount = readUShort(f)
        self.isETC1 = readUByte(f) != 0
        self.isCubemap = readUByte(f) != 0
        self.width = readUShort(f)
        self.height = readUShort(f)
        self.imageFormat = GLTextureFormat(readUInt32(f))
        self.dataOffset = readUInt32(f)
        self.name = readString(f, 16)
        return self

class Material(object):
    def __init__(self):
        self.isFragmentLightingEnabled = False
        self.isVertexLightingEnabled = True
        self.isHemiSphereLightingEnabled = True
        self.isHemiSphereOcclusionEnabled = False
        self.faceCulling = CullMode.Front
        self.isPolygonOffsetEnabled = False
        self.polygonOffset = 0.0

        self.Unk0 = 0# Sometimes 1 (Haven't tested changes in-game yet)
        self.TextureMappersUsed = 0
        self.TextureCoordsUsed = 0
        self.TextureMappers = [TexMapper() for _ in range(3)]
        self.TextureCoords  = [TexCoords() for _ in range(3)]

        self.emissionColor  = [0, 0, 0, 0]
        self.ambientColor   = [102, 102, 102, 0]
        self.diffuseColor   = [127, 127, 127, 255]
        self.specular0Color = [255, 255, 255, 255]
        self.specular1Color = [0, 0, 0, 0]
        self.constantColors = [[0, 0, 0, 255] for _ in range(6)]
        self.bufferColor    = [0.0, 0.0, 0.0, 1.0]

        self.bumpTexture = BumpTexture.Texture0
        self.bumpMode = BumpMode.NotUsed
        self.isBumpRenormalize = False

        self.layerConfig = LayerConfig.LayerConfig0
        self.FresnelSelector = FresnelConfig.No
        self.isClampHighlight = False
        self.isDistribution0Enabled = False
        self.isDistribution1Enabled = False
        self.isGeometricFactor0Enabled = False
        self.isGeometricFactor1Enabled = False
        self.IsReflectionEnabled = False

        self.reflectanceRSampler = Sampler()
        self.reflectanceGSampler = Sampler()
        self.reflectanceBSampler = Sampler()
        self.distibution0Sampler = Sampler()
        self.distibution1Sampler = Sampler()
        self.fresnelSampler      = Sampler()
        self.texEnvStageCount = 0
        self.texEnvStagesIndices = [-1,-1,-1,-1,-1,-1]
        self.texEnvStages = [Combiner()]

        self.alphaTestEnabled = True
        self.alphaTestReferenceValue = 128
        self.alphaTestFunction = TestFunc.Greater
        self.depthTestEnabled = True
        self.depthWriteEnabled = True
        self.depthTestFunction = TestFunc.Less
        self.blendMode = BlendMode.BlendNone

        self.alphaSrcFunc = BlendFactor.SourceAlpha
        self.alphaDstFunc = BlendFactor.OneMinusSourceAlpha
        self.alphaEquation = BlendEquation.FuncAdd
        self.colorSrcFunc = BlendFactor.One
        self.colorDstFunc = BlendFactor.Zero
        self.colorEquation = BlendEquation.FuncAdd
        self.blendColor = [0.0, 0.0, 0.0, 1.0]

        self.stencilEnabled = False
        self.stencilReferenceValue = 0
        self.bufferMask = 255
        self.buffer = 0
        self.StencilFunc = TestFunc.Never
        self.failOP = StencilTestOp.Keep
        self.zFailOP = StencilTestOp.Keep
        self.zPassOP = StencilTestOp.Keep
        self.Unk1 = 0

    def read(self,f):
        self.isFragmentLightingEnabled = readUByte(f) != 0
        self.isVertexLightingEnabled = readUByte(f) != 0
        self.isHemiSphereLightingEnabled = readUByte(f) != 0
        self.isHemiSphereOcclusionEnabled = readUByte(f) != 0
        self.faceCulling = CullMode(readUByte(f))
        self.isPolygonOffsetEnabled = readUByte(f) != 0
        self.polygonOffset = float(readShort(f) / 65534)

        if(Version > 10):
            self.Unk0 = readUInt32(f)
            self.TextureMappersUsed = readShort(f)
            self.TextureCoordsUsed = readShort(f)
        else:
            self.TextureMappersUsed = readUInt32(f)
            self.TextureCoordsUsed = readUInt32(f)

        self.TextureMappers = [TexMapper().read(f) for _ in range(3)]
        self.TextureCoords = [TexCoords().read(f) for _ in range(3)]

        self.emissionColor = readArray(f, 4, DataTypes.UByte)
        self.ambientColor = readArray(f, 4, DataTypes.UByte)
        self.diffuseColor = readArray(f, 4, DataTypes.UByte)
        self.specular0Color = readArray(f, 4, DataTypes.UByte)
        self.specular1Color = readArray(f, 4, DataTypes.UByte)
        self.constantColors = [readArray(f, 4, DataTypes.UByte) for _ in range(6)]
        self.bufferColor = readArray(f, 4)

        self.bumpTexture = BumpTexture(readUShort(f))
        self.bumpMode = BumpMode(readUShort(f))
        self.isBumpRenormalize = readUInt32(f) != 0

        self.layerConfig = LayerConfig(readUInt32(f))
        self.FresnelSelector = FresnelConfig(readUShort(f))
        self.isClampHighlight = readUByte(f) != 0
        self.isDistribution0Enabled = readUByte(f) != 0
        self.isDistribution1Enabled = readUByte(f) != 0
        self.isGeometricFactor0Enabled = readUByte(f) != 0
        self.isGeometricFactor1Enabled = readUByte(f) != 0
        self.IsReflectionEnabled = readUByte(f) != 0

        self.reflectanceRSampler = Sampler().read(f)
        self.reflectanceGSampler = Sampler().read(f)
        self.reflectanceBSampler = Sampler().read(f)
        self.distibution0Sampler = Sampler().read(f)
        self.distibution1Sampler = Sampler().read(f)
        self.fresnelSampler      = Sampler().read(f)

        self.texEnvStageCount = readUInt32(f)
        self.texEnvStagesIndices = [readShort(f) for _ in range(6)]

        self.alphaTestEnabled = readUByte(f) != 0
        self.alphaTestReferenceValue = readUByte(f) / 255
        self.alphaTestFunction = TestFunc(readUShort(f))
        self.depthTestEnabled = readUByte(f) != 0
        self.depthWriteEnabled = readUByte(f) != 0
        self.depthTestFunction = TestFunc(readUShort(f))
        self.blendMode = BlendMode(readUByte(f))
        align(f)

        self.alphaSrcFunc = BlendFactor(readUShort(f))
        self.alphaDstFunc = BlendFactor(readUShort(f))
        self.alphaEquation = BlendEquation(readUInt32(f))
        self.colorSrcFunc = BlendFactor(readUShort(f))
        self.colorDstFunc = BlendFactor(readUShort(f))
        self.colorEquation = BlendEquation(readUInt32(f))
        self.blendColor = readArray(f, 4)

        if(Version > 6):
            self.stencilEnabled = readUByte(f) != 0
            self.stencilReferenceValue = readUByte(f)
            self.bufferMask = readUByte(f)
            self.buffer = readUByte(f)
            self.StencilFunc = TestFunc(readUShort(f))
            self.failOP = StencilTestOp(readUShort(f))
            self.zFailOP = StencilTestOp(readUShort(f))
            self.zPassOP = StencilTestOp(readUShort(f))
            self.Unk1 = readUInt32(f)# CRC32 of something?
        return self

class Bone(object):
    def __init__(self):
        self.id = 0
        self.parentId = -1
        self.hasSkinningMatrix = False
        self.scale = {1,1,1}
        self.rotation = {0,0,0}
        self.translation = {0,0,0}
        self.unk0 = 0

    def read(self,f):
        # Because only 12 bits are used, 4095 is the max bone count. (In versions > OoT3D anyway)
        self.id = readUShort(f)
        # Other 4 bits are probably more flags, but they're not used in any of the three games
        # Though I probably missed a few compressed files. It's most likely these flags below:
        # IsSegmentScaleCompensate, IsCompressible, IsNeededRendering, HasSkinningMatrix
        self.hasSkinningMatrix = ((self.id >> 4) & 1) != 0
        self.id = (self.id & 0xFFF)# Get boneID
        self.parentId = readShort(f)
        self.scale = readArray(f,3)
        self.rotation = readArray(f,3)
        self.translation = readArray(f,3)
        self.unk0 = readUInt32(f) if (Version > 6) else 0 # I assume a crc32 of the bone name
        return self

class Skl(object):
    def __init__(self):
        self.magic = "skl\x20"
        self.chunkSize = 16
        self.boneCount = 0
        self.unkFlags = 0
        self.bones = []

    def read(self,f):
        self.magic = readString(f, 4)
        self.chunkSize = readUInt32(f)
        self.boneCount = readUInt32(f)
        self.unkFlags  = readUInt32(f)# Only value found is "2", possibly "IsTranslateAnimationEnabled" flag (I can't find a change in-game)
        self.bones = [Bone().read(f) for _ in range(self.boneCount)]
        return self

class BoundingBox(object):
    #I checked all files, and Min/Max are the only values to ever change
    def __init__(self):
        self.unk0
        self.unk1
        self.min = [-1.0, -1.0, -1.0]
        self.max = [1.0, 1.0, 1.0]
        self.unk2 = -1# Unknown Index
        self.unk3 = -1
        self.unk4 = 0# No idea
    def read(self,f):
        self.unk0 = readUInt32(f)
        self.unk1 = readUInt32(f)
        self.min = readArray(f, 3)
        self.max = readArray(f, 3)
        self.unk2 = readInt32(f)
        self.unk3 = readInt32(f)
        self.unk4 = readUInt32(f)
        return self

class Qtrs(object):
    def __init__(self):
        self.magic = "qtrs"# dunno
        self.chunkSize = 348
        self.boxCount = 0
        self.boundingboxes = []
    def read(self,f):
        self.magic = readString(f, 4)
        self.chunkSize = readUInt32(f)
        self.boxCount = readUInt32(f)
        self.boundingboxes = [BoundingBox().read(f) for _ in range(self.boxCount)]
        return self

class Mat(object):
    def __init__(self):
        self.magic = "mats"# MATerials
        self.chunkSize = 348
        self.matCount = 0
        self.materials = []

    def read(self,f):
        self.magic = readString(f, 4)
        self.chunkSize = readUInt32(f)
        self.matCount = readUInt32(f)
        self.materials = [Material().read(f) for _ in range(self.matCount)]
        combiners = []

        for m in self.materials:
            for _ in range(m.texEnvStageCount): combiners.append(Combiner().read(f))

        for m in self.materials:
            m.texEnvStages = []# Make sure combiners are empty
            for index in m.texEnvStagesIndices:
                if(index != -1):
                    m.texEnvStages.append(combiners[index])
        return self

class Tex(object):
    def __init__(self):
        self.magic = "tex\x20"#TEXtures
        self.chunkSize = 12
        self.texCount = 0
        self.textures = []

    def read(self,f):
        self.magic = readString(f, 4)
        self.chunkSize = readUInt32(f)
        self.texCount = readUInt32(f)
        self.textures = [Texture().read(f) for _ in range(self.texCount)]
        return self

class Mshs(object):
    def __init__(self):
        self.magic = "mshs"#MeSHeS
        self.chunkSize = 16
        # Note: Mesh order = draw order
        self.meshCount = 0
        self.OpaqueMeshCount = 0# The remainder are translucent meshes and always packed at the end
        self.idCount = 1# MeshNodeNameCount
        self.meshes = []

    def read(self,f):
        self.magic = readString(f, 4)
        self.chunkSize = readUInt32(f)
        self.meshCount = readUInt32(f)
        self.OpaqueMeshCount = readUShort(f)
        self.idCount = readUShort(f)
        self.meshes = [Mesh().read(f) for _ in range(self.meshCount)]
        return self

class Shp(object):
    def __init__(self):
        self.magic = "shp\x20"#SHaPe
        self.chunkSize = 16
        self.shapeCount = 0
        #No idea... but it does something to materials and it's never used on ANY model but link's in OoT3D
        #Set to 0x58 on "link_v2.cmb"
        self.flags = 0
        self.shapes = []

    def read(self,f):
        self.magic = readString(f, 4)
        self.chunkSize = readUInt32(f)
        self.shapeCount = readUInt32(f)
        self.flags = readUInt32(f)

        [readShort(f) for _ in range(self.shapeCount)]# ShapeOffset(s)
        align(f)
        self.shapes = [Sepd().read(f) for _ in range(self.shapeCount)]
        return self

class Sklm(object):
    def __init__(self):
        self.magic = "sklm"# SKeLetal Model
        self.chunkSize = 0
        self.mshOffset = 0
        self.shpOffset = 0
        self.meshes = []
        self.shapes = []

    def read(self,f):
        self.magic = readString(f, 4)
        self.chunkSize = readUInt32(f)
        self.mshOffset = readUInt32(f)
        self.shpOffset = readUInt32(f)
        self.meshes = Mshs().read(f).meshes
        self.shapes = Shp().read(f).shapes
        return self

class AttributeSlice(object):
    def __init__(self):
        self.size = 0
        self.startOfs = 0
    def read(self,f):
        self.size = readUInt32(f)
        self.startOfs = readUInt32(f)
        return self

class Vatr(object):
    def __init__(self):
        self.magic = "vatr"
        self.chunkSize = 0
        self.maxIndex = 3

        self.position = AttributeSlice()
        self.normal = AttributeSlice()
        self.tangent = AttributeSlice()
        self.color = AttributeSlice()
        self.uv0 = AttributeSlice()
        self.uv1 = AttributeSlice()
        self.uv2 = AttributeSlice()
        self.bIndices = AttributeSlice()
        self.bWeights = AttributeSlice()

    def read(self,f):
        self.magic = readString(f, 4)
        self.chunkSize = readUInt32(f)
        self.maxIndex = readUInt32(f)# i.e., vertex count of model

        # Basically just used to get each attibute into it's own byte[] (We won't be doing that here)
        self.position = AttributeSlice().read(f)
        self.normal = AttributeSlice().read(f)
        self.tangent = AttributeSlice().read(f) if (Version > 6) else self.tangent
        self.color = AttributeSlice().read(f)
        self.uv0 = AttributeSlice().read(f)
        self.uv1 = AttributeSlice().read(f)
        self.uv2 = AttributeSlice().read(f)
        self.bIndices = AttributeSlice().read(f)
        self.bWeights = AttributeSlice().read(f)
        return self

def readCmb(fileio, startOff):
    return Cmb().read(fileio, startOff)
