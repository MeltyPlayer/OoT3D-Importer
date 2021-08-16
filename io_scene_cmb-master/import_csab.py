#!/usr/bin/env python3
'''Blender import addon for CSAB animation format (from Legend of Zelda: Ocarina of Time 3D & Majora's Mask 3D)
'''

#Allow modules used by this addon to be reloaded by pressing F8 in Blender
if "bpy" in locals():
    import importlib
    if "csab" in locals():
        importlib.reload(csab)
    if "common" in locals():
        importlib.reload(common)

import bpy
from mathutils import Matrix, Vector, Euler, Quaternion

from . import csab
from .common import (
        axis_correction_matrix, #TODO use this someday
        ValueHolder, #TODO maybe not
        get_bone_ids_in_order,
)


LOG_ANIMATION = False
LOG_ANIMATION_PATH = "/home/whatagotchi/Projects/N64/OoT_N64_3DS/blender_addon/bpy_logfile_csab.txt"


class NoActiveArmatureError(ValueError):
    pass

class BoneMismatchError(IndexError):
    pass

class CsabImporter:
    '''Imports a parsed csab file into Blender

    csab_parsed: a parsed csab animation object (i.e. the object returned from csab.parse())
    '''

    def __init__(self, csab_parsed, csabAnimationHelper, cmb, anim_name="anim"):
        self.csab_parsed = csab_parsed
        self.csabAnimationHelper = csabAnimationHelper
        self.cmb = cmb

        # self.blender = ValueHolder()
        # self.blender.anim_name = anim_name
        # self.blender.armature_object = None #TODO

        self.anim_name = anim_name
        self.bone_mismatch = False #TODO quick hacky way to show bone mismatch error after done importing

    def import_anims(self, clear_armature = True):
        '''import all animations in the CSAB file. (Generally there is only one anim per file.)'''
        csab_parsed = self.csab_parsed
        scene = bpy.context.scene

        #Get the active/selected armature or raise an error if there isn't one
        armature_object = bpy.context.active_object
        if armature_object is None or armature_object.type != 'ARMATURE':
            for obj in bpy.context.selected_objects:
                if obj.type == 'ARMATURE':
                    armature_object = obj
                    break
            else:
                raise NoActiveArmatureError("You must first select the armature to be animated.")

        armobj = armature_object
        arm_bones = len(armobj.pose.bones)

        #Prepare armature for animation, prepare animation & action
        # TODO: This should not occur if animation_data is defined
        if clear_armature:
            armobj.animation_data_clear()
            armobj.animation_data_create()

        #Get bone ids and parents, also map bone ids to Blender PoseBones. TODO someday use custom property for bone_ids
        bones_parents_ids = []
        boneid_posebone_map = dict()
        for posebone in armobj.pose.bones:
            bone_id = int(posebone.name.replace("bone_", ""))
            boneid_posebone_map[bone_id] = posebone

            parent_bone = posebone.parent
            parent_bone_id = -1 if parent_bone is None else int(parent_bone.name.replace("bone_", ""))
            bones_parents_ids.append((bone_id, parent_bone_id))

        # Backs up pose.
        backupTransforms = []
        for bone_id in get_bone_ids_in_order(bones_parents_ids):
            blender_posebone = boneid_posebone_map[bone_id]
            backupTransforms.append(blender_posebone.matrix.copy())

        # Processes animations
        csab_anim = self.csab_parsed
        anim_full_name = self.anim_name

        #Check that the number of bones in the animation matches the number of bones in the armature
        #anim_bones = csab_anim.num_bones
        #if anim_bones != arm_bones:
        #    print("WARNING: Bone number mismatch. Animation contains {anim_bones} bones, but the selected armature contains {arm_bones} bones.".format(anim_bones=anim_bones, arm_bones=arm_bones))
        #    self.bone_mismatch = True

        # Creates new action (i.e. animation)
        armobj.animation_data.action = bpy.data.actions.new(anim_full_name)
        action = armobj.animation_data.action

        # Gathers up animations from each bone
        animationLength = csab_anim.duration + 1
        for bone_id in get_bone_ids_in_order(bones_parents_ids):
            blender_posebone = boneid_posebone_map[bone_id]
            cmb_bone = self.cmb.skeleton[bone_id]

            blender_posebone.rotation_mode = 'QUATERNION'

            pos_fcurves = []
            rot_fcurves = []
            for i in range(3):
                # TODO: This is broken, this needs to be "location" instead.
                pos_data_path = 'pose.bones["{0}"].location'.format(blender_posebone.name)
                pos_fcurves.append(action.fcurves.new(data_path=pos_data_path, index=i))
            for i in range(4):
                rot_data_path = 'pose.bones["{0}"].rotation_quaternion'.format(blender_posebone.name)
                rot_fcurves.append(action.fcurves.new(data_path=rot_data_path, index=i))

            previousQuaternion = None
            for i in range(animationLength):
                translation = self.csabAnimationHelper.getBoneTranslation(csab_anim, cmb_bone, i)
                quaternion = self.csabAnimationHelper.getBoneQuaternion(csab_anim, cmb_bone, i)

                # Keeps quaternion signs the same to prevent gimbal lock.
                if previousQuaternion is not None and previousQuaternion.dot(quaternion) < 0:
                    quaternion *= -1

                # TODO: Only write frames where they're needed (if possible?)
                # TODO: Include tangents in animation (if possible?)
                for a in range(3):
                    pos_fcurves[a].keyframe_points.insert(i, translation[a])
                for a in range(4):
                    rot_fcurves[a].keyframe_points.insert(i, quaternion[a])

                previousQuaternion = quaternion

        #TODO does not account for multiple animations
        scene.frame_start = 0
        scene.frame_end = csab_anim.duration
        scene.frame_set(0)
        scene.update()

        # Done w/ animations here!

        # Reapplies original poses
#        for bone_id in get_bone_ids_in_order(bones_parents_ids):
#            blender_posebone = boneid_posebone_map[bone_id]
#            blender_posebone.matrix = backupTransforms[bone_id]

#        scene.update()

        if self.bone_mismatch:
            raise BoneMismatchError("There is a mismatch between the number of bones in the animation and the armature. Are you sure this is the right model for this animation? (See the Blender console for more details.)")

def read(filepath):
    print("Reading CSAB file '{0}' [{1}] ...".format(bpy.path.basename(filepath), filepath))
    csab_parsed = csab.parse(filepath)
    print("...done reading CSAB file.")


    if LOG_ANIMATION:
        with open(LOG_ANIMATION_PATH, 'wt') as logfile:
            print(csab_parsed, file=logfile)

    anim_name = bpy.path.display_name_from_filepath(filepath)
    csab_importer = CsabImporter(csab_parsed, anim_name=anim_name)
    csab_importer.import_anims()
