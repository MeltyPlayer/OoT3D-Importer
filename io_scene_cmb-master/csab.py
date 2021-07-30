#!/usr/bin/env python3
'''CSAB file format (Legend of Zelda: Ocarina of Time 3D animation)

The same format is used in Majora's Mask 3D, but this hasn't been tested with those files.
'''
#To those trying to read the source: start at the bottom (at csab_file) and work your way up.

try:
    from .construct import * #For running this script as a module imported by a Blender addon
except ModuleNotFoundError:
    from construct import * #For running this script directly
    import sys

frame_type1 = Struct(
    "num" / Int32ul, #frame number
    "unknown4" / Float32l,
    "unknown8" / Float32l,
    "value" / Float32l #transform value, e.g. position
)

frame_type2 = Struct(
    "num" / Int32ul, #frame number
    "value" / Float32l, #transform value, e.g. position
    "unknown8" / Float32l,
    "unknownC" / Float32l,
)

axis_data_type1 = Struct(
    "num_frames" / Int32ul,
    "frames" / frame_type1[this.num_frames]
)

axis_data_type2 = Struct(
     "num_frames" / Int32ul,
     "zeroval" / Const(0, Int32ul),
     "last_frame" / Int32ul,
     "frames" / frame_type2[this.num_frames]
)

anod_axis_OoT = Struct(
    #significance of type1 vs type2 is currently unknown
    "type" / Enum(Int32ul, type1=1, type2=2),
    "data" / Switch(this.type, {"type1": axis_data_type1, "type2": axis_data_type2}, default=Error)
)

frame_type0 = Struct(
    "value" / Int16ul #Float16l?
)

axis_data_type0 = Struct (
    "num_frames" / Int16ul,
    "unk" / Int16ul[4],
    "frames" / Aligned(4, frame_type0[this.num_frames], pattern=b'\x00')
)

anod_axis_MM = Struct(
    "type" / Enum(Int8ul, type0=0, type1=1),#Const(0, Int8ul), #XXX = 1 in bee_attack
    "unk01" / Const(1, Int8ul),
    "data" / Switch(this.type, {'type0':axis_data_type0, 'type1':axis_data_type0}, default=Error)
)

anod_axis = Switch(this._._._._.game, {'Ocarina3D':anod_axis_OoT, 'Majora3D':anod_axis_MM}, default=Error) #TODO wiki update once this gets sorted out

anod_chunk_data = Struct(
    "offset" / Tell,
    "magic" / Const(b"anod"),
    #"bone_id" / Int32ul, #TODO update wiki
    "bone_id" / Int16ul,
    "unk06" / Int8ul,
    "unk07" / Int8ul,

    "posx_offset" / Int16ul,
    "posy_offset" / Int16ul,
    "posz_offset" / Int16ul,
    "rotx_offset" / Int16ul,
    "roty_offset" / Int16ul,
    "rotz_offset" / Int16ul,
    "unk7_offset" / Int16ul, #no apparent effect in OoT
    "unk8_offset" / Int16ul, #no apparent effect in OoT
    "unk9_offset" / Int16ul, #no apparent effect in OoT
    "unk10_offset" / Int16ul, #no apparent effect in OoT, might just be 0 padding

    #turn offsets into absolute offsets, or None if there is no data
    "posx_abs_offset" / If(this.posx_offset > 0, Computed(this.offset + this.posx_offset)),
    "posy_abs_offset" / If(this.posy_offset > 0, Computed(this.offset + this.posy_offset)),
    "posz_abs_offset" / If(this.posz_offset > 0, Computed(this.offset + this.posz_offset)),
    "rotx_abs_offset" / If(this.rotx_offset > 0, Computed(this.offset + this.rotx_offset)),
    "roty_abs_offset" / If(this.roty_offset > 0, Computed(this.offset + this.roty_offset)),
    "rotz_abs_offset" / If(this.rotz_offset > 0, Computed(this.offset + this.rotz_offset)),
    "unk7_abs_offset" / If(this.unk7_offset > 0, Computed(this.offset + this.unk7_offset)),
    "unk8_abs_offset" / If(this.unk8_offset > 0, Computed(this.offset + this.unk8_offset)),
    "unk9_abs_offset" / If(this.unk9_offset > 0, Computed(this.offset + this.unk9_offset)),
    "unk10_abs_offset" / If(this.unk10_offset > 0, Computed(this.offset + this.unk10_offset)),

    "posx"/ If(this.posx_abs_offset != None, Pointer(this.posx_abs_offset, anod_axis)),
    "posy"/ If(this.posy_abs_offset != None, Pointer(this.posy_abs_offset, anod_axis)),
    "posz"/ If(this.posz_abs_offset != None, Pointer(this.posz_abs_offset, anod_axis)),
    "rotx"/ If(this.rotx_abs_offset != None, Pointer(this.rotx_abs_offset, anod_axis)),
    "roty"/ If(this.roty_abs_offset != None, Pointer(this.roty_abs_offset, anod_axis)),
    "rotz"/ If(this.rotz_abs_offset != None, Pointer(this.rotz_abs_offset, anod_axis)),
    "unk7"/ If(this.unk7_abs_offset != None, Pointer(this.unk7_abs_offset, anod_axis)),
    "unk8"/ If(this.unk8_abs_offset != None, Pointer(this.unk8_abs_offset, anod_axis)),
    "unk9"/ If(this.unk9_abs_offset != None, Pointer(this.unk9_abs_offset, anod_axis)),
    "unk10"/ If(this.unk10_abs_offset != None, Pointer(this.unk10_abs_offset, anod_axis)),
)

anod_chunk = Struct(
    "offset" / Int32ul,
    "absolute_offset" / Computed(this._._.offset + this.offset),
    "data" / Pointer(this.absolute_offset, anod_chunk_data)
)

animation_data = Struct(
    "zeroval00" / Const(0, Int32ul),
    "zeroval04" / Const(0, Int32ul),
    "zeroval08" / Const(0, Int32ul),
    "zeroval0C" / Const(0, Int32ul),

    "last_frame" / Int32ul, #amosOT=23, amosMM=22
    "zeroval14" / Int32ul,#Const(0, Int32ul), #XXX = 1 in bee_attack

    "num_anod_chunks" / Int32ul, #amosOT=3, amosMM=5
    "num_bones" / Int32ul, #amosOT=amosMM=5
    
    #if per_bone_indices[2]=3, that means bone 2 uses anod chunk 3
    "per_bone_indices" / Aligned(4, Int16sl[this.num_bones]), #amosOT=(-1,-1,0,1,2), amosMM=(0,1,2,3,4)

    "anod_chunks" / anod_chunk[this.num_anod_chunks] #amosOT=(56,356,688), amosMM=(64,92,240,448,596)
)

csab_animation = Struct(
    "offset" / Int32ul,
    "data" / Pointer(this.offset, animation_data)
)

csab_file = Struct(
    "magic" / Const(b"csab"),
    "file_size" / Int32ul,
    
    "unknown08" / Int32ul,
    "game" / Switch(this.unknown08, {3:Computed('Ocarina3D'), 5:Computed('Majora3D')}, default=Error), #TODO add to wiki
    "unknown0C" / Const(0, Int32ul), #XXX 0? amosOT=amosMM=0
    
    #something for MM3D
    "junkMM3D" / If(this.game == "Majora3D", Const(b'\0\0 B\0\0 B\0\0 B')),

    "num_animations" / Const(1, Int32ul),#XXX testing
    "animations" / csab_animation[this.num_animations]
)

def parse(filename):
    '''parses the csab file and returns the parsed contents'''
    with open(filename, 'rb') as f:
        data = f.read()
    return csab_file.parse(data)

def parse_and_print(filename): #test function
    '''parses the csab file and prints its contents'''
    with open(filename, 'rb') as f:
        data = f.read()
    csab_parsed = csab_file.parse(data)
    print(csab_parsed)

if __name__ == '__main__':
    args = sys.argv[1:]
    if args:
        PATH = args[0]
    else:
        PATH = "/media/whatagotchi/EXTRA/OoT_work/romfs-extracted/actor/zelda_am/Anim/am_jump.csab"
        PATH = "/media/whatagotchi/EXTRA/OoT_work/romfs_extracted_mm3D/actors/zelda2_am.gar.lzs/am_jump.csab"
    parse_and_print(PATH)

    