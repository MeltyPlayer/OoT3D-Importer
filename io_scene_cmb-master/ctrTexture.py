import struct, array
from .cmbEnums import GLTextureFormat
#Ported from SPICA (https://github.com/gdkchan/SPICA)

SwizzleLUT = (
    0,  1,  8,  9,  2,  3, 10, 11,
    16, 17, 24, 25, 18, 19, 26, 27,
    4,  5, 12, 13,  6,  7, 14, 15,
    20, 21, 28, 29, 22, 23, 30, 31,
    32, 33, 40, 41, 34, 35, 42, 43,
    48, 49, 56, 57, 50, 51, 58, 59,
    36, 37, 44, 45, 38, 39, 46, 47,
    52, 53, 60, 61, 54, 55, 62, 63)

ETC1LUT = (
    (2, 8, -2, -8),
    (5, 17, -5, -17),
    (9, 29, -9, -29),
    (13, 42, -13, -42),
    (18, 60, -18, -60),
    (24, 80, -24, -80),
    (33, 106, -33, -106),
    (47, 183, -47, -183))

XT = ( 0, 4, 0, 4 )
YT = ( 0, 0, 4, 4 )

def getFmtBPP(format):
    if  (format == GLTextureFormat.RGBA8):           return 32
    elif(format == GLTextureFormat.RGB8):            return 24
    elif(format == GLTextureFormat.RGBA5551):        return 16
    elif(format == GLTextureFormat.RGB565):          return 16
    elif(format == GLTextureFormat.RGBA4444):        return 16
    elif(format == GLTextureFormat.LA8):             return 16
    elif(format == GLTextureFormat.L4):              return 4
    elif(format == GLTextureFormat.A4):              return 4
    elif(format & 0xFFFF == GLTextureFormat.ETC1):   return 4
    else: return 8

def __Swap64(Value):
    Value = ((Value & 0xffffffff00000000) >> 32) | ((Value & 0x00000000ffffffff) << 32)
    Value = ((Value & 0xffff0000ffff0000) >> 16) | ((Value & 0x0000ffff0000ffff) << 16)
    Value = ((Value & 0xff00ff00ff00ff00) >>  8) | ((Value & 0x00ff00ff00ff00ff) <<  8)
    return Value

def __CastSByte(value):
    if(value < -127): return value + 255
    elif(value > 127): return value - 255
    return value

def __GetUShort(Buffer, Address):
    return int((Buffer[Address + 0] << 0 | Buffer[Address + 1] << 8))

def __ReadULong(b):
    return struct.unpack("<Q", bytearray(b))[0]

def __SetColor(Buffer, Address, A, B, G, R):
    Buffer[Address + 0] = B
    Buffer[Address + 1] = G
    Buffer[Address + 2] = R
    Buffer[Address + 3] = A

def __DecodeRGBA5551(Buffer, Address, Value):
    R = ((Value >>  1) & 0x1f) << 3
    G = ((Value >>  6) & 0x1f) << 3
    B = ((Value >> 11) & 0x1f) << 3

    __SetColor(Buffer, Address, (Value & 1) * 0xff,
                B | (B >> 5),
                G | (G >> 5),
                R | (R >> 5))

def __DecodeRGB565(Buffer, Address, Value):
    R = ((Value >>  0) & 0x1f) << 3
    G = ((Value >>  5) & 0x3f) << 2
    B = ((Value >> 11) & 0x1f) << 3

    __SetColor(Buffer, Address, 0xff,
                B | (B >> 5),
                G | (G >> 6),
                R | (R >> 5))

def __DecodeRGBA4(Buffer, Address, Value):
    R = (Value >>  4) & 0xf
    G = (Value >>  8) & 0xf
    B = (Value >> 12) & 0xf

    __SetColor(Buffer, Address, (Value & 0xf) | (Value << 4),
                B | (B << 4),
                G | (G << 4),
                R | (R << 4))

def __ETC1Decompress(Input, Width, Height, Alpha):
    Offset = 0
    Output = [0 for x in range(Width * Height * 4)]

    for TY in range(0, Height, 8):
        for TX in range(0, Width, 8):
            for T in range(4):
                AlphaBlock = 0xffffffffffffffff
                col = []
                alp = []

                if (Alpha):
                    for _ in range(8):
                        alp.append(Input[Offset])
                        Offset += 1
                    AlphaBlock = __ReadULong(alp)

                for _ in range(8):
                    col.append(Input[Offset])
                    Offset += 1

                ColorBlock = __Swap64(__ReadULong(col))
                Tile = __ETC1Tile(ColorBlock)
                TileOffset = 0

                for PY in range(YT[T], 4 + YT[T], 1):
                    for PX in range(XT[T], 4 + XT[T], 1):
                        OOffs = ((Height - 1 - (TY + PY)) * Width + TX + PX) * 4

                        Output[OOffs + 0] = Tile[TileOffset + 0] / 255
                        Output[OOffs + 1] = Tile[TileOffset + 1] / 255
                        Output[OOffs + 2] = Tile[TileOffset + 2] / 255

                        AlphaShift = ((PX & 3) * 4 + (PY & 3)) << 2

                        A = (AlphaBlock >> AlphaShift) & 0xf

                        Output[OOffs + 3] = int((A << 4) | A) / 255

                        TileOffset += 4

    return Output

def __ETC1Tile(Block):
    BlockLow  = Block >> 32
    BlockHigh = Block >>  0

    Flip = (BlockHigh & 0x1000000) != 0
    Diff = (BlockHigh & 0x2000000) != 0

    R1, G1, B1 = 0, 0, 0
    R2, G2, B2 = 0, 0, 0

    if (Diff):
        B1 = (BlockHigh & 0x0000f8) >> 0
        G1 = (BlockHigh & 0x00f800) >> 8
        R1 = (BlockHigh & 0xf80000) >> 16

        #CAST AS SBYTE IS THE ISSUE

        B2 = int(__CastSByte(B1 >> 3) + (__CastSByte((BlockHigh & 0x000007) <<  5) >> 5))
        G2 = int(__CastSByte(G1 >> 3) + (__CastSByte((BlockHigh & 0x000700) >>  3) >> 5))
        R2 = int(__CastSByte(R1 >> 3) + (__CastSByte((BlockHigh & 0x070000) >> 11) >> 5))

        B1 |= B1 >> 5
        G1 |= G1 >> 5
        R1 |= R1 >> 5

        B2 = (B2 << 3) | (B2 >> 2)
        G2 = (G2 << 3) | (G2 >> 2)
        R2 = (R2 << 3) | (R2 >> 2)
    else:
        B1 = (BlockHigh & 0x0000f0) >> 0
        G1 = (BlockHigh & 0x00f000) >> 8
        R1 = (BlockHigh & 0xf00000) >> 16

        B2 = (BlockHigh & 0x00000f) << 4
        G2 = (BlockHigh & 0x000f00) >> 4
        R2 = (BlockHigh & 0x0f0000) >> 12

        B1 |= B1 >> 4
        G1 |= G1 >> 4
        R1 |= R1 >> 4

        B2 |= B2 >> 4
        G2 |= G2 >> 4
        R2 |= R2 >> 4

    Table1 = (BlockHigh >> 29) & 7
    Table2 = (BlockHigh >> 26) & 7


    Output = [0 for x in range(4 * 4 * 4)]

    if (Flip == False):
        for Y in range(4):
            for X in range(2):

                Color1 = __ETC1Pixel(R1, G1, B1, X + 0, Y, BlockLow, Table1)
                Color2 = __ETC1Pixel(R2, G2, B2, X + 2, Y, BlockLow, Table2)

                Offset1 = (Y * 4 + X) * 4

                Output[Offset1 + 0] = Color1[2]
                Output[Offset1 + 1] = Color1[1]
                Output[Offset1 + 2] = Color1[0]

                Offset2 = (Y * 4 + X + 2) * 4

                Output[Offset2 + 0] = Color2[2]
                Output[Offset2 + 1] = Color2[1]
                Output[Offset2 + 2] = Color2[0]
    else:
        for Y in range(2):
            for X in range(4):
                Color1 = __ETC1Pixel(R1, G1, B1, X, Y + 0, BlockLow, Table1)
                Color2 = __ETC1Pixel(R2, G2, B2, X, Y + 2, BlockLow, Table2)

                Offset1 = (Y * 4 + X) * 4

                Output[Offset1 + 0] = Color1[2]
                Output[Offset1 + 1] = Color1[1]
                Output[Offset1 + 2] = Color1[0]

                Offset2 = ((Y + 2) * 4 + X) * 4

                Output[Offset2 + 0] = Color2[2]
                Output[Offset2 + 1] = Color2[1]
                Output[Offset2 + 2] = Color2[0]

    return Output

def __ETC1Pixel(R, G, B, X, Y, Block, Table):
    Index = X * 4 + Y
    MSB = Block << 1

    if Index < 8:
        Pixel = ETC1LUT[Table][((Block >> (Index + 24)) & 1) + ((MSB >> (Index + 8)) & 2)]
    else:
        Pixel = ETC1LUT[Table][((Block >> (Index +  8)) & 1) + ((MSB >> (Index - 8)) & 2)]

    R = __Saturate(int((R + Pixel)))
    G = __Saturate(int((G + Pixel)))
    B = __Saturate(int((B + Pixel)))

    return ((R, G, B))

def __Saturate(Value):
    if (Value > 255): return 255
    if (Value < 0): return 0
    return Value

def DecodeBuffer(Input, width, height, format, isETC1):
        #Note: I don't think HiLo8 exist for .cmb

        Increment = int(getFmtBPP(format) / 8)
        if (Increment == 0): Increment = 1
        Output = [0 for x in range(width * height * 4)]
        IOffs = 0

        # Is ETC1(a4)
        if(isETC1):
            return __ETC1Decompress(Input, width, height, ((format & 0xFFFF) == 26459))

        for TY in range(0, height, 8):
            for TX in range(0, width, 8):
                for Px in range(64):
                    X =  SwizzleLUT[Px] & 7
                    Y = (SwizzleLUT[Px] - X) >> 3

                    OOffs = int((TX + X + ((height - 1 - (TY + Y)) * width)) * 4)

                    if(format == GLTextureFormat.RGBA8):#RGBA8
                        Output[OOffs + 0] = Input[IOffs + 3]
                        Output[OOffs + 1] = Input[IOffs + 2]
                        Output[OOffs + 2] = Input[IOffs + 1]
                        Output[OOffs + 3] = Input[IOffs + 0]
                    elif(format == GLTextureFormat.RGB8):#RGB8
                        Output[OOffs + 0] = Input[IOffs + 2]
                        Output[OOffs + 1] = Input[IOffs + 1]
                        Output[OOffs + 2] = Input[IOffs + 0]
                        Output[OOffs + 3] = 0xff
                    elif(format == GLTextureFormat.RGBA5551): __DecodeRGBA5551(Output, OOffs, __GetUShort(Input, IOffs))
                    elif(format == GLTextureFormat.RGB565):   __DecodeRGB565(Output, OOffs, __GetUShort(Input, IOffs))
                    elif(format == GLTextureFormat.RGBA4444): __DecodeRGBA4(Output, OOffs, __GetUShort(Input, IOffs))
                    elif(format == GLTextureFormat.LA8):#LA8
                        Output[OOffs + 0] = Input[IOffs + 1]
                        Output[OOffs + 1] = Input[IOffs + 1]
                        Output[OOffs + 2] = Input[IOffs + 1]
                        Output[OOffs + 3] = Input[IOffs + 0]
                    elif(format == GLTextureFormat.L8):#L8
                        Output[OOffs + 0] = Input[IOffs]
                        Output[OOffs + 1] = Input[IOffs]
                        Output[OOffs + 2] = Input[IOffs]
                        Output[OOffs + 3] = 0xff
                    elif(format == GLTextureFormat.A8):#A8
                        Output[OOffs + 0] = 0xff
                        Output[OOffs + 1] = 0xff
                        Output[OOffs + 2] = 0xff
                        Output[OOffs + 3] = Input[IOffs]
                    elif(format == GLTextureFormat.LA4):#LA4
                        Output[OOffs + 0] = ((Input[IOffs] >> 4) | (Input[IOffs] & 0xf0))
                        Output[OOffs + 1] = ((Input[IOffs] >> 4) | (Input[IOffs] & 0xf0))
                        Output[OOffs + 2] = ((Input[IOffs] >> 4) | (Input[IOffs] & 0xf0))
                        Output[OOffs + 3] = ((Input[IOffs] << 4) | (Input[IOffs] & 0x0f))
                    elif(format == GLTextureFormat.L4):#L4
                        L = (Input[IOffs >> 1] >> ((IOffs & 1) << 2)) & 0xf

                        Output[OOffs + 0] = ((L << 4) | L)
                        Output[OOffs + 1] = ((L << 4) | L)
                        Output[OOffs + 2] = ((L << 4) | L)
                        Output[OOffs + 3] = 0xff
                    elif(format == GLTextureFormat.A4):#L4
                        A = (Input[IOffs >> 1] >> ((IOffs & 1) << 2)) & 0xf

                        Output[OOffs + 0] = 0xff
                        Output[OOffs + 1] = 0xff
                        Output[OOffs + 2] = 0xff
                        Output[OOffs + 3] = ((A << 4) | A)
                    elif(format == GLTextureFormat.Gas or format == GLTextureFormat.Shadow):
                        Output[OOffs + 0] = Input[IOffs]
                        Output[OOffs + 1] = Input[IOffs]
                        Output[OOffs + 2] = Input[IOffs]
                        Output[OOffs + 3] = 0xff

                    #Convert to float for blender
                    Output[OOffs + 0] /= 255
                    Output[OOffs + 1] /= 255
                    Output[OOffs + 2] /= 255
                    Output[OOffs + 3] /= 255

                    IOffs += Increment
        return Output
