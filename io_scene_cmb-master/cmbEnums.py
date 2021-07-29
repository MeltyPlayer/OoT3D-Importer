from enum import IntEnum

class CmbVersion(IntEnum):
    # Not literally an enum for the game, just more informative
    OoT3D = 6,     # Ocarina of Time: 3D
    MM3D = 10,     # Majora's Mask: 3D
    EverOasis = 12,# Ever Oasis
    LM3D = 15      # Luigi's Mansion: 3D

class GLTextureFormat(IntEnum):
    RGB8 = 0x14016754,
    RGBA8 = 0x14016752,
    RGBA5551 = 0x80346752,
    RGB565 = 0x83636754,
    RGBA4444 = 0x80336752,
    LA8 = 0x14016758,
    Gas = 0x00006050
    HiLo8 = 0x14016759,# TODO: Test
    L8 = 0x14016757,
    A8 = 0x14016756,
    LA4 = 0x67606758,
    L4 = 0x67616757,
    A4 = 0x67616756,
    ETC1 = 0x0000675A or 0x1401675A,
    ETC1a4 = 0x0000675B or 0x1401675B,
    Shadow = 0x00006040
    #ETC1 = 0x1401675A,
    #ETC1a4 = 0x1401675B

class DataTypes(IntEnum):
    Byte = 0x1400,
    UByte = 0x1401,
    Short = 0x1402,
    UShort = 0x1403,
    Int = 0x1404,
    UInt = 0x1405,
    Float = 0x1406

class TestFunc(IntEnum):
    Invalid = 0,
    Never = 512,
    Less = 513,
    Equal = 514,
    Lequal = 515,
    Greater = 516,
    Notequal = 517,
    Gequal = 518,
    Always = 519

class CullMode(IntEnum):
    FrontAndBack = 0,
    Front = 1,
    BackFace = 2,
    Never = 3

class BumpMode(IntEnum):
    NotUsed   = 25288,
    AsBump    = 25289,
    AsTangent = 25290# Doesn't exist in OoT3D

class BumpTexture(IntEnum):
    Texture0 = 0x84C0,
    Texture1 = 0x84C0,
    Texture2 = 0x84C0

class BlendEquation(IntEnum):
    FuncAdd = 0x8006,
    FuncSubtract = 0x800A,
    FuncReverseSubtract = 0x800B,
    Min = 0x8007,
    Max = 0x8008

class BlendMode(IntEnum):
    BlendNone = 0,
    Blend = 1,
    BlendSeparate = 2,
    LogicalOp = 3

class BlendFactor(IntEnum):
    Zero = 0,
    One = 1,
    SourceColor = 768,
    OneMinusSourceColor = 769,
    DestinationColor = 774,
    OneMinusDestinationColor = 775,
    SourceAlpha = 770,
    OneMinusSourceAlpha = 771,
    DestinationAlpha = 772,
    OneMinusDestinationAlpha = 773,
    ConstantColor = 32769,
    OneMinusConstantColor = 32770,
    ConstantAlpha = 32771,
    OneMinusConstantAlpha = 32772,
    SourceAlphaSaturate = 776

class TexCombineMode(IntEnum):
    Replace = 0x1E01,
    Modulate = 0x2100,
    Add = 0x0104,
    AddSigned = 0x8574,
    Interpolate = 0x8575,
    Subtract = 0x84E7,
    DotProduct3Rgb = 0x86AE,
    DotProduct3Rgba = 0x86AF,
    MultAdd = 0x6401,
    AddMult = 0x6402

class TexCombineScale(IntEnum):
    One = 1,
    Two = 2,
    Four = 4

class TexCombinerSource(IntEnum):
    PrimaryColor = 0x8577,
    FragmentPrimaryColor = 0x6210,
    FragmentSecondaryColor = 0x6211,
    Texture0 = 0x84C0,
    Texture1 = 0x84C1,
    Texture2 = 0x84C2,
    Texture3 = 0x84C3,
    PreviousBuffer = 0x8579,
    Constant = 0x8576,
    Previous = 0x8578

class TexCombinerColorOp(IntEnum):
    Color = 0x0300,
    OneMinusColor = 0x0301,
    Alpha = 0x0302,
    OneMinusAlpha = 0x0303,
    Red = 0x8580,
    OneMinusRed = 0x8583,
    Green = 0x8581,
    OneMinusGreen = 0x8584,
    Blue = 0x8582,
    OneMinusBlue = 0x8585

class TexCombinerAlphaOp(IntEnum):
    Alpha = 0x0302,
    OneMinusAlpha = 0x0303,
    Red = 0x8580,
    OneMinusRed = 0x8583,
    Green = 0x8581,
    OneMinusGreen = 0x8584,
    Blue = 0x8582,
    OneMinusBlue = 0x8585

class TextureMinFilter(IntEnum):
    Nearest = 0x2600,
    Linear = 0x2601,
    NearestMipmapNearest = 0x2700,
    LinearMipmapNearest = 0x2701,
    NearestMipmapLinear = 0x2702,
    LinearMipmapLinear = 0x2703

class TextureMagFilter(IntEnum):
    Nearest = 0x2600,
    Linear = 0x2601,

class TextureWrapMode(IntEnum):
    ClampToBorder = 0x2900,
    Repeat = 0x2901,
    ClampToEdge = 0x812F,
    Mirror = 0x8370

class TextureMappingType(IntEnum):
    Empty = 0,
    UvCoordinateMap = 1,
    CameraCubeEnvMap = 2,
    CameraSphereEnvMap = 3,
    ProjectionMap = 4

class TextureMatrixMode(IntEnum):
    DccMaya = 0,
    DccSoftImage = 1,
    Dcc3dsMax = 2

class LutInput(IntEnum):
    CosNormalHalf = 25248,
    CosViewHalf = 25249,
    CosNormalView = 25250,
    CosLightNormal = 25251,
    CosLightSpot = 25252,
    CosPhi = 25253

class LayerConfig(IntEnum):
    LayerConfig0 = 25264,
    LayerConfig1 = 25265,
    LayerConfig2 = 25266,
    LayerConfig3 = 25267,
    LayerConfig4 = 25268,
    LayerConfig5 = 25269,
    LayerConfig6 = 25270,
    LayerConfig7 = 25271

class FresnelConfig(IntEnum):
	No = 25280,
	Pri = 25281,
	Sec = 25282,
	PriSec = 25283

class StencilTestOp(IntEnum):
    Keep = 7680,
    Zero = 0,
    Replace = 7681,
    Increment = 7682,
    Decrement = 7683,
    Invert = 5386,
    IncrementWrap = 34055,
    DecrementWrap = 34055

class VertexAttributeMode(IntEnum):
    Array = 0,
    Constant = 1,

class SkinningMode(IntEnum):
    Single = 0,
    Rigid = 1,
    Smooth = 2,

class PrimitiveMode(IntEnum):
    Triangles = 0,
    TriangleStrip = 1,
    TriangleFan = 2,