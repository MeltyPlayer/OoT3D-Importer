#!/usr/bin/env python3
'''CMB file format (Legend of Zelda: Ocarina of Time 3D model)

'''
#To those trying to read the source: start at the bottom (at cmb_file) and work your way up.

from itertools import chain

try:
    from .construct import *  #For running this script as a module imported by a Blender addon
except (ModuleNotFoundError, ImportError):
    from construct import * #For running this script directly

FROM_CURRENT_POS = 1 #option for seeking ahead in the file

pica_data_type = Enum(Int16ul,
    none = 0,
    Int8sl = 0x1400,
    Int8ul = 0x1401,
    Int16sl = 0x1402,
    Int16ul = 0x1403,
    Int32sl = 0x1404,
    Int32ul = 0x1405,
    Float32l = 0x1406,

    UnsignedByte44DMP = 0x6760, #TODO would need to create data types for these
    Unsigned4BitsDMP = 0x6761,
    UnsignedShort4444 = 0x8033,
    UnsignedShort5551 = 0x8034,
    UnsignedShort565 = 0x8363
)

vatr_data = Struct (
    "size" / Int32ul,
    "offset" / Int32ul,
    "absolute_offset" / Computed(this._._.vatr_chunk_offset + this.offset)
    #There is array data following this, but it is read by sepd_chunk instead.
)

vatr_data_OoT = Struct(
    "positions" / vatr_data,
    "normals" / vatr_data,
    "colors" / vatr_data,
    "texcoords" / vatr_data,
    "unknown1" / vatr_data,
    "unknown2" / vatr_data,
    "bone_index_lookup" / vatr_data,
    "bone_weights" / vatr_data
)

vatr_data_MM = Struct(
    "positions" / vatr_data,
    "normals" / vatr_data,
    "unknown0" / vatr_data,
    "colors" / vatr_data,
    "texcoords" / vatr_data,
    "unknown1" / vatr_data,
    "unknown2" / vatr_data,
    "bone_index_lookup" / vatr_data,
    "bone_weights" / vatr_data
)

vatr_chunk = Struct(
    "vatr_chunk_offset" / Tell,
    "magic" / Const(b"vatr"),
    "size" / Int32ul,
    "max_vertex_index_or_something" / Int32ul,
    "vertex_data" / Switch(this._.game, {'Ocarina3D': vatr_data_OoT, 'Majora3D' : vatr_data_MM})
)

prm_chunk = Struct(
    "magic" / Const(b"prm "),
    "size" / Int32ul,
    
    "unknown08" / Int32ul,
    "unknown0C" / Int32ul,
    "data_type" / pica_data_type,
    "data_type_size" / Switch(this.data_type, { #XXX not needed after first_index_absolute_offset's change?
        'Int8ul' : Computed(1),
        'Int16ul' : Computed(2),
        'Int32ul' : Computed(4),
    }),
    "unknown12" / Int16ul,
    "num_indices" / Int16ul,
    "first_index" / Int16ul, #consider renaming in light of recent changes? e.g. first_index_offset_mul2
    #"first_index_absolute_offset" / Computed(this._._._._._.vertex_indices_offset + this.first_index * this.data_type_size),
    "first_index_absolute_offset" / Computed(this._._._._._.vertex_indices_offset + this.first_index * 2), #XXX need to test this change. If it works consistently, update the CMB wiki page with this change
    "indices" / Switch(this.data_type, {
        'Int8ul' : Pointer(this.first_index_absolute_offset, Int8ul[this.num_indices]),
        'Int16ul' : Pointer(this.first_index_absolute_offset, Int16ul[this.num_indices]),
        'Int32ul' : Pointer(this.first_index_absolute_offset, Int32ul[this.num_indices])
    })
)

prms_chunk = Struct(
    "magic" / Const(b"prms"),
    "size" / Int32ul,
    "unknown08" / Int32ul,
    "skinning_mode" / Enum(Int16ul, single_bone=0, skinning=1, skinning_no_pretransform=2),
    "num_bone_indices" / Int16ul,
    "bone_indices_offset" / Int32ul,
    "prm_chunk_offset" / Int32ul,
    "bone_indices" / Aligned(4, Int16ul[this.num_bone_indices]),
    "prm_chunk" / prm_chunk
)

data_offset_OoT = Switch(this._index, {
    0: Computed(this._._._._.vatr_chunk.vertex_data.positions.absolute_offset),
    1: Computed(this._._._._.vatr_chunk.vertex_data.normals.absolute_offset),
    2: Computed(this._._._._.vatr_chunk.vertex_data.colors.absolute_offset),
    3: Computed(this._._._._.vatr_chunk.vertex_data.texcoords.absolute_offset),
    4: Computed(this._._._._.vatr_chunk.vertex_data.unknown1.absolute_offset),
    5: Computed(this._._._._.vatr_chunk.vertex_data.unknown2.absolute_offset),
    6: Computed(this._._._._.vatr_chunk.vertex_data.bone_index_lookup.absolute_offset),
    7: Computed(this._._._._.vatr_chunk.vertex_data.bone_weights.absolute_offset)
})

data_size_OoT = Switch(this._index, {
    0: Computed(this._._._._.vatr_chunk.vertex_data.positions.size),
    1: Computed(this._._._._.vatr_chunk.vertex_data.normals.size),
    2: Computed(this._._._._.vatr_chunk.vertex_data.colors.size),
    3: Computed(this._._._._.vatr_chunk.vertex_data.texcoords.size),
    4: Computed(this._._._._.vatr_chunk.vertex_data.unknown1.size),
    5: Computed(this._._._._.vatr_chunk.vertex_data.unknown2.size),
    6: Computed(this._._._._.vatr_chunk.vertex_data.bone_index_lookup.size),
    7: Computed(this._._._._.vatr_chunk.vertex_data.bone_weights.size)
})

data_offset_MM = Switch(this._index, {
    0: Computed(this._._._._.vatr_chunk.vertex_data.positions.absolute_offset),
    1: Computed(this._._._._.vatr_chunk.vertex_data.normals.absolute_offset),
    2: Computed(this._._._._.vatr_chunk.vertex_data.unknown0.absolute_offset),
    3: Computed(this._._._._.vatr_chunk.vertex_data.colors.absolute_offset),
    4: Computed(this._._._._.vatr_chunk.vertex_data.texcoords.absolute_offset),
    5: Computed(this._._._._.vatr_chunk.vertex_data.unknown1.absolute_offset),
    6: Computed(this._._._._.vatr_chunk.vertex_data.unknown2.absolute_offset),
    7: Computed(this._._._._.vatr_chunk.vertex_data.bone_index_lookup.absolute_offset),
    8: Computed(this._._._._.vatr_chunk.vertex_data.bone_weights.absolute_offset)
})

data_size_MM = Switch(this._index, {
    0: Computed(this._._._._.vatr_chunk.vertex_data.positions.size),
    1: Computed(this._._._._.vatr_chunk.vertex_data.normals.size),
    2: Computed(this._._._._.vatr_chunk.vertex_data.unknown0.size),
    3: Computed(this._._._._.vatr_chunk.vertex_data.colors.size),
    4: Computed(this._._._._.vatr_chunk.vertex_data.texcoords.size),
    5: Computed(this._._._._.vatr_chunk.vertex_data.unknown1.size),
    6: Computed(this._._._._.vatr_chunk.vertex_data.unknown2.size),
    7: Computed(this._._._._.vatr_chunk.vertex_data.bone_index_lookup.size),
    8: Computed(this._._._._.vatr_chunk.vertex_data.bone_weights.size)
})

sepd_array = Struct(
    "offset" / Int32ul,
    "scale" / Float32l,
    "data_type" / pica_data_type,
    "unknown2E" / Int16ul,
    "unknown30" / Int32ul,
    "unknown34" / Int32ul,
    "unknown38" / Int32ul,
    "unknown3C" / Int32ul,

    "vatr_data_offset" / Switch(this._._._._.game, {'Ocarina3D': data_offset_OoT, 'Majora3D': data_offset_MM}), #beginning of the raw vertex/normal/etc data in the vatr chunk
    "vatr_data_size" / Switch(this._._._._.game, {'Ocarina3D': data_size_OoT, 'Majora3D': data_size_MM}), #size of the raw vertex/normal/etc data in the vatr chunk
    "absolute_offset" / Computed(this.vatr_data_offset + this.offset),
    "max_size" / Computed(this.vatr_data_size - this.offset),

    "data" / Pointer(
        this.absolute_offset,
        Switch(this.data_type, {
            'Int8ul' : Int8ul[this.max_size],
            'Int8sl' : Int8sl[this.max_size],
            'Int16ul' : Int16ul[this.max_size // 2],
            'Int16sl' : Int16sl[this.max_size // 2],
            'Int32ul' : Int32ul[this.max_size // 4],
            'Int32sl' : Int32sl[this.max_size // 4],
            'Float32l' : Float32l[this.max_size // 4],
        })
    )
)

sepd_arrays_OoT = NamedTuple(
    "vertex_arrays",
    (
        "positions",
        "normals",
        "colors",
        "texcoords",
        "unknown1",
        "unknown2",
        "bone_index_lookup",
        "bone_weights"
    ),
    sepd_array[8]
)

sepd_arrays_MM = NamedTuple(
    "vertex_arrays",
    (
        "positions",
        "normals",
        "unknown0",
        "colors",
        "texcoords",
        "unknown1",
        "unknown2",
        "bone_index_lookup",
        "bone_weights"
    ),
    sepd_array[9]
)

autogen_flags_OoT = FlagsEnum(Int16ul,
    positions = 0x01, #not yet confirmed
    normals = 0x02,   #not yet confirmed
    colors = 0x04,    #not yet confirmed
    texcoords = 0x08, #not yet confirmed
    unknown1 = 0x10,  #not yet confirmed
    unknown2 = 0x20,  #not yet confirmed
    bone_index_lookup = 0x40,
    bone_weights = 0x80
)

autogen_flags_MM = FlagsEnum(Int16ul,
    positions = 0x01, #not yet confirmed
    normals = 0x02,   #not yet confirmed
    colors = 0x04,    #not yet confirmed
    unknown0 = 0x08,  #not yet confirmed
    texcoords = 0x10, #not yet confirmed
    unknown1 = 0x20,  #not yet confirmed
    unknown2 = 0x40,  #not yet confirmed
    bone_index_lookup = 0x80,
    bone_weights = 0x100
)

sepd_chunk = Struct(
    "magic" / Const(b"sepd"),
    "size" / Int32ul,

    "num_prms_chunks" / Int16ul,
    "unknown0A" / Int16ul,
    "float0C" / Float32l,
    "float10" / Float32l,
    "float14" / Float32l,
    "unknown18" / Int32ul,
    "unknown1C" / Int32ul,
    "unknown20" / Int32ul,

    "vertex_arrays" / Switch(this._._._.game, {'Ocarina3D' : sepd_arrays_OoT, 'Majora3D' : sepd_arrays_MM}),
    
    "bones_per_vertex" / Int16ul,
    "autogen_flags" / Switch(this._._._.game, {'Ocarina3D' : autogen_flags_OoT, 'Majora3D' : autogen_flags_MM}), #TODO update the wiki with this
    "prms_data_offsets" / Aligned(4, Int16ul[this.num_prms_chunks]), #TODO this can be done as pointers
    "prms_chunks" / prms_chunk[this.num_prms_chunks]
)

shp_chunk = Struct(
    "magic" / Const(b"shp "),
    "size" / Int32ul,

    "num_sepd_chunks" / Int32ul,
    "unknown0C" / Int32ul,
    "sepd_offsets" / Aligned(4, Int16ul[this.num_sepd_chunks]), #TODO this can be done as pointers
    "sepd_chunks" / sepd_chunk[this.num_sepd_chunks]
)

mshs_mesh = Struct(
    "sepd_id" / Int16ul,
    "material_id" / Int8ul,
    "unknown03" / Int8ul,
    "unknown04" / If(this._._._.game == 'Majora3D', Int32ul), #XXX untested
    "unknown08" / If(this._._._.game == 'Majora3D', Int32ul) #XXX untested
)

mshs_chunk = Struct(
    "magic" / Const(b"mshs"),
    "size" / Int32ul, #this doesn't match the actual chunk size in Majora3D

    "num_meshes" / Int32ul,
    "unknown0C" / Int16ul,
    "unknown0E" / Int16ul,

    "meshes" / mshs_mesh[this.num_meshes]
)

sklm_chunk = Struct(
    "magic" / Const(b"sklm"),
    "size" / Int32ul,
    "mshs_chunk_offset" / Int32ul,
    "shp_chunk_offset" / Int32ul,

    "mshs_chunk" / mshs_chunk,
    "shp_chunk" / shp_chunk
)


pica_color_format = Enum(Int16ul,
    RGBANativeDMP = 0x6752,
    RGBNativeDMP = 0x6754,
    AlphaNativeDMP = 0x6756,
    LuminanceNativeDMP = 0x6757,
    LuminanceAlphaNativeDMP = 0x6758,
    ETC1RGB8NativeDMP = 0x675A,
    ETC1AlphaRGB8A4NativeDMP = 0x675B
)

def texture_format(this):
    col_dat = (this.color_format, this.data_type)
    if col_dat == ("ETC1RGB8NativeDMP", "none"):
        return "ETC1"
    elif col_dat == ("ETC1AlphaRGB8A4NativeDMP", "none"):
        return "ETC1A4"
    elif col_dat == ("RGBANativeDMP", "Int8ul"):
        return "RGBA8"
    elif col_dat == ("RGBNativeDMP", "Int8ul"):
        return "RGB8"
    elif col_dat == ("RGBANativeDMP", "UnsignedShort4444"):
        return "RGBA4"
    elif col_dat == ("RGBANativeDMP", "UnsignedShort5551"):
        return "RGBA5551"
    elif col_dat == ("RGBNativeDMP", "UnsignedShort565"):
        return "RGB565"
    elif col_dat == ("LuminanceAlphaNativeDMP", "UnsignedByte44DMP"):
        return "LA4"
    elif col_dat == ("LuminanceAlphaNativeDMP", "Int8ul"):
        return "LA8"
    elif col_dat == ("AlphaNativeDMP", "Int8ul"):
        return "A8"
    elif col_dat == ("LuminanceNativeDMP", "Int8ul"):
        return "L8"
    elif col_dat == ("LuminanceNativeDMP", "Unsigned4BitsDMP"):
        return "L4"
    else:
        return "unknown"

pixels_rgba8 = Pointer(this.abs_offset, Int8ul[4][this.data_length // 4])

pixels_rgb8 = Pointer(this.abs_offset, Int8ul[3][this.data_length // 3])

pixel_rgb565 = Bitwise(
    Sequence(
        BitsInteger(5),
        BitsInteger(6),
        BitsInteger(5)
    )
)

pixels_rgb565 = Pointer(this.abs_offset, pixel_rgb565[this.data_length // 2])

#TODO move all this etc1 stuff to etc1.py.

class Bits16Reversed(Adapter):
    '''16 bits, but reverse the order of bits within each byte
    
    decode: takes an int (typically a BitsInteger) and returns a list of int bits
    encode: takes a list of int bits, returns an int
    
    '''
    def _decode(self, obj, context, path):
        bits_str = bin(obj)[2:]
        rbits_str = chain(reversed(bits[:8]), reversed(bits[8:]))
        return [int(b) for b in rbits]
    
    def _encode(self, obj, context, path):
        rbits_ints = chain(reversed(obj[:8]), reversed(obj[8:]))

etc1_pixels = NamedTuple(
    "etc1_pixels",
    "h g f e d c b a  p o n m l k j i",
    Bit[16]
)

etc1_individual = BitStruct(
    #"pixels_lsb" / Bits16Reversed(BitsInteger(16)),
    "pixels_lsb" / etc1_pixels,
    #"pixels_msb" / Bits16Reversed(BitsInteger(16)), #0F -> 11110000, not 00001111
    "pixels_msb" / etc1_pixels,

    "tablecw1" / BitsInteger(3),
    "tablecw2" / BitsInteger(3),
    "diffbit" / Bit,
    "flipbit" / Bit,
    
    "B1" / BitsInteger(4),
    "B2" / BitsInteger(4),
    "G1" / BitsInteger(4),
    "G2" / BitsInteger(4),
    "R1" / BitsInteger(4),
    "R2" / BitsInteger(4),
)

etc1_differential = BitStruct(
    "pixels_lsb" / etc1_pixels,
    #"pixels_lsb" / Bits16Reversed(BitsInteger(16)),
    "pixels_msb" / etc1_pixels,
    #"pixels_msb" / Bits16Reversed(BitsInteger(16)),

    "tablecw1" / BitsInteger(3),
    "tablecw2" / BitsInteger(3),
    "diffbit" / Bit,
    "flipbit" / Bit,
    
    "B1p" /  BitsInteger(5),
    "dB2" / BitsInteger(3, signed=True),
    "G1p" /  BitsInteger(5),
    "dG2" / BitsInteger(3, signed=True),
    "R1p" /  BitsInteger(5),
    "dR2" / BitsInteger(3, signed=True),
)

etc1_block_raw = Struct(
    Seek(4, FROM_CURRENT_POS),
    "diffbitraw" / Peek(Int8ul),
    Seek(-4, FROM_CURRENT_POS),
    "diffbit" / Computed(this.diffbitraw >> 1 & 1),
    
    "now" / Tell, #XXX
    "data" / Switch(
        this.diffbit, {
            0: etc1_individual,
            1: etc1_differential
        }
    )
)

etc1_modifier_tables = {
    0: (  -8,  -2,  2,   8),
    1: ( -17,  -5,  5,  17),
    2: ( -29,  -9,  9,  29),
    3: ( -42, -13, 13,  42),
    4: ( -60, -18, 18,  60),
    5: ( -80, -24, 24,  80),
    6: (-106, -33, 33, 106),
    7: (-183, -47, 47, 183),
}

def clamp255(x):
    return min(max(x, 0), 255)

def decode_etc1_block(this):
    data = this.etc1_blocks_raw[this._index].data
    if data.diffbit == 0:
        basecolor1 = [(x << 4) + x for x in (data.R1, data.G1, data.B1)]
        basecolor2 = [(x << 4) + x for x in (data.R2, data.G2, data.B2)]
        # baseR1 = (data.R1 << 4) + data.R1
        # baseG1 = (data.G1 << 4) + data.G1
        # baseB1 = (data.B1 << 4) + data.B1
        # baseR2 = (data.R2 << 4) + data.R2
        # baseG2 = (data.G2 << 4) + data.G2
        # baseB2 = (data.B2 << 4) + data.B2
    else:
        basecolor1 = [(x << 3) + ((x >> 2) & 7) for x in (data.R1p, data.G1p, data.B1p)]
        # baseR1 = (data.R1p << 3) + ((data.R1p >> 2) & 7)
        # baseG1 = (data.G1p << 3) + ((data.G1p >> 2) & 7)
        # baseB1 = (data.B1p << 3) + ((data.B1p >> 2) & 7)

        color2p = (sum(x) for x in ((data.R1p, data.dR2), (data.G1p, data.dG2), (data.B1p, data.dB2)))
        basecolor2 = [(col2p << 3) + ((col2p >> 2) & 7) for col2p in color2p]
        # R2p = data.R1p + data.dR2
        # baseR2 = (R2p << 3) + ((R2p >> 2) & 7)
        # G2p = data.G1p + data.dG2
        # baseG2 = (G2p << 3) + ((G2p >> 2) & 7)
        # B2p = data.B1p + data.dB2
        # baseR2 = (B2p << 3) + ((B2p >> 2) & 7)
    
    block_pixels = [None]*16
    pixels_in_order = chain(reversed(range(8)), reversed(range(8,16)))
    for pixel_idx, pixel_idx_reverse in zip(range(16), pixels_in_order):
        if data.flipbit == 0:
            if pixel_idx < 8:
                basecolor = basecolor1
                modifier_table = etc1_modifier_tables[data.tablecw1]
            else:
                basecolor = basecolor2
                modifier_table = etc1_modifier_tables[data.tablecw2]
        else:
            if pixel_idx % 4 < 2:
                basecolor = basecolor1
                modifier_table = etc1_modifier_tables[data.tablecw1]
            else:
                basecolor = basecolor2
                modifier_table = etc1_modifier_tables[data.tablecw2]

        msb = data.pixels_msb[pixel_idx]
        lsb = data.pixels_lsb[pixel_idx]
        if (msb, lsb) == (1, 1):
            pixel_modifier = modifier_table[0]
        elif (msb, lsb) == (1, 0):
            pixel_modifier = modifier_table[1]
        elif (msb, lsb) == (0, 0):
            pixel_modifier = modifier_table[2]
        elif (msb, lsb) == (0, 1):
            pixel_modifier = modifier_table[3]

        pixel = [clamp255(col + pixel_modifier) for col in basecolor]
        #TODO ^ make it a generator later, once it's tested?
        block_pixels[pixel_idx_reverse] = pixel

    return block_pixels

def get_etc1_pixels(this):
    width = this.width
    height = this.height

    width_blocks = width // 4

    blocks = this.etc1_data.etc1_blocks_decoded

    #blocks_rows = (blocks[x:x+width_blocks for x in range(0, len(blocks), width_blocks))
    
    blocks_rows = [blocks[x:x+width_blocks] for x in range(0, len(blocks) - width_blocks + 1, width_blocks)]

    pixels = []
    for block_row in blocks_rows: #a row of 4x4-pixel blocks
        
        pixel_rows =[list() for x in range(4)]
        for block in block_row:   #a single 4x4-pixel block in the row
            for i in range(4):    #a single row of pixels in the block
                pixel_block_row = block[i::4]
                pixel_rows[i].extend(pixel_block_row)
        
        for r in pixel_rows:
            pixels.extend(r)
    
    return pixels
                
            

    #(r,g,b)[numpixels]

pixels_etc1 = Computed(get_etc1_pixels)

etc1_data = Struct(
    "etc1_blocks_raw" / Pointer(this._.abs_offset, etc1_block_raw[this._.data_length // 8]),
    "etc1_blocks_decoded" / Computed(decode_etc1_block)[this._.data_length // 8]
)    

tex_texture = Struct(
    "data_length" / Int32ul,
    "unknown04" / Int16ul,
    "unknown06" / Int16ul,
    "width" / Int16ul,
    "height" / Int16ul,
    
    "color_format" / pica_color_format,
    "data_type" / pica_data_type,
    "format" / Computed(texture_format),
    
    #"color_scale" / Computed(),
    
    "data_offset" / Int32ul,
    "abs_offset" / Computed(this._._.texture_data_offset + this.data_offset),
    "name" / Padded(16, CString(encoding='ascii')),
    
    "etc1_data" / If(this.format == "ETC1", etc1_data),
    
    "pixels" / Switch(this.format, {
        "ETC1": pixels_etc1,
        # "ETC1A4": pixels_etc1a4,
        "RGBA8": pixels_rgba8,
        "RGB8": pixels_rgb8,
        # "RGBA4": pixels_rgba4,
        # "RGBA5551": pixels_rgba5551,
        "RGB565": pixels_rgb565,
        # "LA4": pixels_la4,
        # "LA8": pixels_la8,
        # "A8": pixels_a8,
        # "L8": pixels_l8,
        # "L4": pixels_l4,
    }),
    
    "data" / Pointer(this.abs_offset, HexDump(Bytes(this.data_length))) #TODO this will need parsing
)

tex_chunk = Struct(
    "magic" / Const(b"tex "),
    "size" / Int32ul,
    "num_textures" / Int32ul,
    "textures" / tex_texture[this.num_textures]
)

mats_texture_env_setting = Struct(
    #TODO check out the enums for actual meanings of values
    "combine_rgb" / Int16ul, #(Constants.PicaTextureEnvModeCombine) 
    "combine_alpha" / Int16ul, # (Constants.PicaTextureEnvModeCombine)
    "unknown_u16pair_1" / Int16ul[2],
    "unknown_glconstant" / Int16ul[2],
    "source_rgb" / Int16ul[3], #(Constants.PicaTextureEnvModeSource)
    "operand_rgb" / Int16ul[3], #(Constants.PicaTextureEnvModeOperandRgb)
    "source_alpha" / Int16ul[3], #(Constants.PicaTextureEnvModeSource)
    "operand_alpha" / Int16ul[3], #(Constants.PicaTextureEnvModeOperandAlpha)
    "unknown_u16pair_2" / Int16ul[2]
)

mats_material = Struct(
    #TODO check out the enums for actual meanings of values
    "unknown000" / Int32ul,
    "unknown004" / Int32ul,
    "unknown008" / Int32ul,
    "unknown00C" / Int32ul,

    #TODO maybe change these 3 textures to an array of 3 structs, like in the CMB doc
    "texture_id_0"  / Int16sl,
    "unknown012"  / Int16sl,
    "texture_min_filter_0" / Int16ul, #(TextureMinFilter)
    "texture_mag_filter_0" / Int16ul, #(TextureMagFilter)
    "texture_wrapmodeS_0" / Int16ul, #(TextureWrapMode)
    "texture_wrapmodeT_0" / Int16ul, #(TextureWrapMode)
    "unknown01C" / Int32ul,
    "unknown020" / Int32ul,
    "unknown024" / Int32ul,

    "texture_id_1" / Int16sl,
    "unknown02A" / Int16ul,
    "texture_min_filter_1" / Int16ul, #(TextureMinFilter)
    "texture_mag_filter_1" / Int16ul, #(TextureMagFilter)
    "texture_wrapmodeS_1" / Int16ul, #(TextureWrapMode)
    "texture_wrapmodeT_1" / Int16ul, #(TextureWrapMode)
    "unknown034" / Int32ul,
    "unknown038" / Int32ul,
    "unknown03C" / Int32ul,

    "texture_id_2" / Int16sl,
    "unknown042" / Int16ul,
    "texture_min_filter_2" / Int16ul, #(TextureMinFilter)
    "texture_mag_filter_2" / Int16ul, #(TextureMagFilter)
    "texture_wrapmodeS_2" / Int16ul, #(TextureWrapMode)
    "texture_wrapmodeT_2" / Int16ul, #(TextureWrapMode)
    "unknown04C" / Int32ul,
    "unknown050" / Int32ul,
    "unknown054" / Int32ul,

    "unknown058" / Int32ul,
    "float05C" / Float32l,
    "float060" / Float32l,
    "unknown064" / Int32ul,
    "unknown068" / Int32ul,
    "unknown06C" / Int32ul,
    "unknown070" / Int32ul,
    "float074" / Float32l,
    "float078" / Float32l,
    "unknown07C" / Int32ul,
    "unknown080" / Int32ul,
    "unknown084" / Int32ul,
    "unknown088" / Int32ul,
    "float08C" / Float32l,
    "float090" / Float32l,
    "unknown094" / Int32ul,
    "unknown098" / Int32ul,
    "unknown09C" / Int32ul,
    "unknown0A0" / Int32ul,
    "unknown0A4" / Int32ul,
    "unknown0A8" / Int32ul,
    "unknown0AC" / Int32ul,
    "unknown0B0" / Int32ul,
    "unknown0B4" / Int32ul,
    "unknown0B8" / Int32ul,
    "unknown0BC" / Int32ul,
    "unknown0C0" / Int32ul,
    "unknown0C4" / Int32ul,
    'unknown0C8' / Int32ul,
    "unknown0CC" / Int32ul,
    "unknown0D0" / Int32ul,
    "unknown0D4" / Int32ul,
    "float0D8" / Float32l,
    "unknown0DC" / Int32ul,
    "unknown0E0" / Int32ul,
    "float0E4" / Float32l,
    "unknown0E8" / Int32ul,
    "unknown0EC" / Int32ul,
    "unknown0F0" / Int32ul,
    "float0F4" / Float32l,
    "unknown0F8" / Int32ul,
    "float0FC" / Float32l,
    "unknown100" / Int32ul,
    "float104" / Float32l,
    "unknown108" / Int32ul,
    "float10C" / Float32l,
    "unknown110" / Int32ul,
    "float114" / Float32l,
    "unknown118" / Int32ul,
    "float11C" / Float32l,

    "num_indices_to_unknown" / Int32ul,
    "indices_to_unknown" / Padded(12, Int16ul[this.num_indices_to_unknown], pattern=b"\xff"),

    "alpha_test_enable" / Flag,
    "alpha_reference" / Int8ub,
    "alpha_function" / Int16ul, #(AlphaFunction)

    "maybe_stencil_unknown134" / Int16ul,
    "maybe_stencil_function" / Int16ul, #(StencilFunction)

    "unknown138" / Int32ul,
    "blending_factor_src" / Int16ul, #(BlendingFactorSrc) 
    "blending_factor_dest" / Int16ul, #(BlendingFactorDest) 

    "unknown140" / Int32ul,
    "unknown144" / Int32ul,
    "unknown148" / Int32ul,
    "unknown14C" / Int32ul,
    "unknown150" / Int32ul,
    "unknown154" / Int32ul,
    "blend_color_alpha" / Float32l,

    "unknown15C" / If(this._._.game == 'Majora3D', Int16ul), #XXX these are untested
    "unknown15E" / If(this._._.game == 'Majora3D', Int16ul),
    "unknown160" / If(this._._.game == 'Majora3D', Int16ul),
    "unknown162" / If(this._._.game == 'Majora3D', Int16ul),
    "unknown164" / If(this._._.game == 'Majora3D', Int16ul),
    "unknown166" / If(this._._.game == 'Majora3D', Int16ul),
    "unknown168" / If(this._._.game == 'Majora3D', Int32ul)
)

mats_chunk = Struct(
    "magic" / Const(b"mats"),
    "size" / Int32ul, #doesn't match the actual chunk size
    "num_materials" / Int32ul,

    "materials" / mats_material[this.num_materials],
    "texture_env_settings" / mats_texture_env_setting[this.num_materials],
    #XXX Why does zelda_am.zar/amos.cmb have 2 materials but apparently 8 texture_env_settings?
)

qtrs_chunk = Struct(
    "magic" / Const(b"qtrs"),
    "size" / Int32ul, #is actually size - 4

    "unknown08" / Int32ul,
    "unknown0C" / Int32ul, #type unknown
    "unknown10" / Int32ul, #type unknown
    "unknown14" / Float32l,
    "unknown18" / Float32l, #type unknown
    "unknown1C" / Float32l,
    "unknown20" / Float32l,
    "unknown24" / Float32l,
    "unknown28" / Float32l,

    "unknown2C" / Int32sl,
    "unknown30" / Int32sl,
    "unknown34" / Int32ul, #type unknown
)

skl_bone = Struct(
    "bone_id" / Int8sl,
    "unknown01" / Int8ul,
    "parent_bone_id" / Int8sl,
    "unknown03" / Int8ul,
    
    "unknown04" / Float32l[3],
    "rotation" / Float32l[3],
    "position" / Float32l[3],

    "unknown28" / If(this._._.game == 'Majora3D', Int32ul) #XXX untested
)

skl_chunk = Struct(
    "magic" / Const(b"skl "),
    "size" / Int32ul,
    "num_bones" / Int32ul,
    "unknown0C" / Int32ul,
    "bones" / skl_bone[this.num_bones]
)

cmb_file = Struct(
    "magic" / Const(b"cmb "),
    "size" / Int32ul,
    "num_chunks" / Int32ul,
    "game" / IfThenElse(this.num_chunks == 0x0A, Computed('Majora3D'), Computed('Ocarina3D')),
    "unknown" / Int32ul,
    "name" / Padded(16, CString(encoding='ascii')),
    "num_vertex_indices" / Int32ul,
    
    "skl_chunk_offset" / Int32ul,
    "qtrs_chunk_offset" / If(this.game=='Majora3D', Int32ul),
    "mats_chunk_offset" / Int32ul,
    "tex_chunk_offset" / Int32ul,
    "sklm_chunk_offset" / Int32ul,
    "luts_chunk_offset" / Int32ul,
    "vatr_chunk_offset" / Int32ul,
    "vertex_indices_offset" / Int32ul,
    "texture_data_offset" / Int32ul,

    "skl_chunk" / Pointer(this.skl_chunk_offset, skl_chunk),
    "qtrs_chunk" / If(this.qtrs_chunk_offset != None, Pointer(this.qtrs_chunk_offset, qtrs_chunk)), #XXX untested
    "mats_chunk" / Pointer(this.mats_chunk_offset, mats_chunk),
    "tex_chunk" / Pointer(this.tex_chunk_offset, tex_chunk),
    "vatr_chunk" / Pointer(this.vatr_chunk_offset, vatr_chunk), #parsing the vatr chunk early so the sklm chunk's sepd chunks can use the vatr chunk's data
    "sklm_chunk" / Pointer(this.sklm_chunk_offset, sklm_chunk),
    #"luts_chunk" / Pointer(this.luts_chunk_offset, luts_chunk),

    #Vertex indices and texture data are beyond this point and are read by other chunks.
)

def parse(filename):
    '''parses the cmb file and returns the parsed contents'''
    with open(filename, 'rb') as f:
        data = f.read()
    return cmb_file.parse(data)

def parse_and_print(filename): #test function
    '''parses the cmb file and prints its contents'''
    with open(filename, 'rb') as f:
        data = f.read()
    cmb_parsed = cmb_file.parse(data)
    print(cmb_parsed)

if __name__ == '__main__':
    #cmb_path = "insert path to .cmb model file here"
    #parse_and_print(cmb_path)
    #return

    #PATH = "/media/whatagotchi/EXTRA/OoT_work/romfs-extracted/actor/zelda_xc/Model/sheik.cmb"
    #PATH = "/media/whatagotchi/EXTRA/OoT_work/romfs_extracted_mm3D/actors/zelda2_bee.gar.lzs/giant_bee.cmb"
    PATH = "/media/whatagotchi/EXTRA/OoT_work/romfs_extracted_mm3D/actors/zelda2_kerfay.gar.lzs/kafai.cmb"
    
    parse_and_print(PATH)