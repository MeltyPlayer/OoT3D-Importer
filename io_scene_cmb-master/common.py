#!/usr/bin/env python3
'''Common values and functions used for the CMB/CSAB addons'''

from collections import OrderedDict
from itertools import cycle

import bpy.path
from bpy_extras.io_utils import axis_conversion

from .construct import Adapter, IntegerError
#from construct import Adapter, IntegerError


GLOBAL_SCALE = 0.001 #used to scale meshes, armature, and animations so they aren't huge

CLIP_START = .1
CLIP_END = 1000

axis_correction_matrix = axis_conversion(
        from_forward = 'Z',
        from_up = 'X',
        to_forward = "-X",
        to_up = "Z"
).to_4x4()

class ValueHolder:
    '''an empty object to hold values (such as options or Blender data)'''
    pass


#XXX Majora3D CSAB may not use this kind of float16 after all
class Float16lListAdapter(Adapter):
    '''decode: take a list of Int16ul's, return a list of Float16l's
        encode: take a list of Float16l's, return a list of Int16ul's '''
    def _decode(self, obj, context, path):
        float16s = []
        for u16 in obj:
            if u16 > 65535:
                raise IntegerError("Expecting 16-bit unsigned value, given {}".format(u16))
            bits = "{:016b}".format(u16)
            sign, exponent, fraction = (int(b, 2) for b in (bits[0], bits[1:6], bits[6:]))

            if exponent == 0: #subnormal or zero
                float16 = (-1)**sign * 2**(-14) * fraction/1024
            elif exponent == 0b11111:
            #note: ARM has an alternate mode that encodes normal numbers 65536-131008 instead of inf/nan: https://en.wikipedia.org/wiki/Half-precision_floating-point_format#ARM_alternative_half-precision
                if fraction == 0: #infinity or NaN
                    float16 = (-1)**sign * float('inf')
                else:
                    #XXX does not differentiate between quiet and signalling NaNs
                    float16 = float('nan')
            else: #normal
                float16 = (-1)**sign * 2**(exponent-15) * (1024+fraction)/1024
            float16s.append(float16)
        return float16s

    def _encode(self, obj, context, path):
        return NotImplemented
        # u16s = []
        # for float16 in obj:
        #     u16 = 'value'
        #     u16s.append(u16)
        # return u16s

#XXX testing float16
def test16(hexstr, byteswap=True):
    if byteswap:
        u16 = int(hexstr[2:] + hexstr[:2], 16)
    else:
        u16 = int(hexstr, 16)
    if u16 > 65535:
        raise IntegerError("Expecting 16-bit unsigned value, given {}".format(u16))
    bits = "{:016b}".format(u16)
    sign, exponent, fraction = (int(b, 2) for b in (bits[0], bits[1:6], bits[6:]))

    if exponent == 0: #subnormal or zero
        float16 = (-1)**sign * 2**(-14) * fraction/1024
    elif exponent == 0b11111:
    #note: ARM has an alternate mode that encodes normal numbers 65536-131008 instead of inf/nan: https://en.wikipedia.org/wiki/Half-precision_floating-point_format#ARM_alternative_half-precision
        if fraction == 0: #infinity or NaN
            float16 = (-1)**sign * float('inf')
        else:
            #XXX does not differentiate between quiet and signalling NaNs
            float16 = float('nan')
    else: #normal
        float16 = (-1)**sign * 2**(exponent-15) * (1024+fraction)/1024
    return float16


def get_bone_ids_in_order(bones_parents_ids):
    '''return a list of bone ids, ordered such that a bone id never appears before its parent

    A utility function to get bone ids in an order suitable for positioning bones in the rest pose (where parent bones must always be positioned before their children) or animations (where child bones must be positioned before their parents).

    bones_parents_ids: a list of 2-tuples (bone id, parent bone id). The first value is the ID number of a bone from a CMB model or the equivalent bone in a Blender armature. The second value is the ID number of that bone's parent bone, or a negative number if it has no parent.

    return value: a list of bone ids, ordered such that a bone id never appears before its parent. The root bone (bone with no parent) is always first, and child bones of a parent bone can appear anywhere as long as it isn't before the parent bone.

    Example:
      bones_parents_ids: [(0,-1), (1,0), (2,1), (3,1), (4,1), (5,0), (6,5), (7,5), (8,5)]
        (equivalent to the following bone hierarchy)
                     0
                  /     \
                 1       5
                /|\     /|\
               2 3 4   6 7 8
      return value:
        [0, 1, 2, 3, 4, 5, 6, 7, 8]
        But if the items in bones_parents_ids were ordered differently (which wouldn't affect the bone hierarchy), other potential return values would include:
        [0, 5, 6, 7, 8, 1, 2, 3, 4]
        [0, 1, 5, 2, 3, 4, 6, 7, 8]
        In short, the return value's order doesn't matter as long as a parent bone never appears after any of its child bones.

    '''
    #There's probably a more proper way to do this, but this works well enough.

    bone_ids_in_order = []
    since_added = 0 #used to keep the Blender from hanging if the bone hierarchy is messed up

    #This for loop cycles until all bones are added to the list.
    for bone_id, parent_id in cycle(bones_parents_ids):

        #Add the root bone right away, or add a bone if its parent has already been already added
        if (parent_id < 0 or parent_id in bone_ids_in_order) and bone_id not in bone_ids_in_order:
            bone_ids_in_order.append(bone_id)
            since_added = 0
        else:
            since_added += 1

        #Stop when bone_ids_in_order contains all bone ids
        if len(bone_ids_in_order) == len(bones_parents_ids):
            break

        #Abort this script if it looks like it will loop forever without adding any new bones.
        if since_added > len(bones_parents_ids):
            raise ValueError("ERROR: Problem with the bone hierarchy. "
                "Stopping prematurely so this script won't loop forever. "
                "Bone hierarchy was: {0}".format(bones_parents_ids))

    return bone_ids_in_order
