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
        GLOBAL_SCALE,
        axis_correction_matrix, #TODO use this someday
        ValueHolder, #TODO maybe not
        get_bone_ids_in_order,
)
from .interpolated_bone_transforms import InterpolatedBoneTransforms


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

    def __init__(self, csab_parsed, cmb, anim_name="anim"):
        self.csab_parsed = csab_parsed
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
        for anim_id, csab_anim in enumerate(x.data for x in csab_parsed.animations):
            num_anims = len(csab_parsed.animations)
            if num_anims > 1:
                # digits = len(str(num_anims-1))
                # anim_full_name = "{anim_name}_{num:0{digits}}".format(anim_name=self.anim_name, num=anim_id, digits=digits)

                #temporary until multiple anim support
                anim_full_name = "{anim_name}_1-of-{num_anims}}".format(anim_name=self.anim_name, num_anims=num_anims)
            else:
                anim_full_name = self.anim_name

            #Check that the number of bones in the animation matches the number of bones in the armature
            anim_bones = csab_anim.num_bones
            if anim_bones != arm_bones:
                print("WARNING: Bone number mismatch. Animation contains {anim_bones} bones, but the selected armature contains {arm_bones} bones.".format(anim_bones=anim_bones, arm_bones=arm_bones))
                self.bone_mismatch = True

            # Checks that the bones match up
            for bone_id in get_bone_ids_in_order(bones_parents_ids):
                try:
                    anod_id = csab_anim.per_bone_indices[bone_id]
                except IndexError:
                    #raise BoneMismatchError("Attempted to animate nonexistent bone. Are you sure this is the right model for this animation?")
                    print("WARNING: Attempted to animate nonexistent bone {bone_id}. Are you sure this is the right model for this animation? Skipping this bone.".format(bone_id=bone_id))
                    self.bone_mismatch = True

            # Creates new action (i.e. animation)
            armobj.animation_data.action = bpy.data.actions.new(anim_full_name)
            action = armobj.animation_data.action

            # Gathers up animations from each bone
            animationLength = csab_anim.last_frame + 1
            boneTransforms = InterpolatedBoneTransforms(anim_bones, animationLength)
            for bone_id in get_bone_ids_in_order(bones_parents_ids):
                anod_id = csab_anim.per_bone_indices[bone_id]
                if anod_id < 0:
                    continue #this bone is not animated
                anod = csab_anim.anod_chunks[anod_id].data

                blender_posebone = boneid_posebone_map[bone_id]

                parent_matrix = (blender_posebone.parent.matrix.copy() if blender_posebone.parent is not None else Matrix.Identity(4))
                local_matrix = parent_matrix.inverted() * blender_posebone.matrix
                local_position = local_matrix.to_translation()
                local_rotation = local_matrix.to_euler('XYZ')

                blender_posebone.rotation_mode = 'XYZ'

                #For each position axis:
                pos_fcurves = []
                for axis_idx, axis in enumerate((anod.posx, anod.posy, anod.posz)):
                    data_path = 'pose.bones["{0}"].local_position'.format(blender_posebone.name)
                    fcurve = action.fcurves.new(data_path=data_path, index=axis_idx)
                    pos_fcurves.append(fcurve)

                    if axis is None:
                        keyframeValue = local_position[axis_idx]
                        fcurve.keyframe_points.insert(0, keyframeValue)
                    else:
                        for frame in axis.data.frames:
                            keyframeValue = frame.value
                            fcurve.keyframe_points.insert(frame.num, keyframeValue)

                rot_fcurves = []
                for axis_idx, axis in enumerate((anod.rotx, anod.roty, anod.rotz)):
                    data_path = 'pose.bones["{0}"].rotation_euler'.format(blender_posebone.name)
                    fcurve = action.fcurves.new(data_path=data_path, index=axis_idx)
                    rot_fcurves.append(fcurve)

                    adj = False #axis_idx == 0
                    if axis is None:
                        #Animation is not defined for this axis, so make a flat fcurve from local bone rotation
                        keyframeValue = local_rotation[axis_idx]

                        if adj:
                            keyframeValue = -keyframeValue

                        print(keyframeValue)
                        fcurve.keyframe_points.insert(0, keyframeValue) #XXX consider LINEAR interpolation
                    else:
                        #Animation is defined for this axis
                        #Populate the fcurve and add all frame #s to rot_all_keyframes
                        for frame in axis.data.frames:
                            keyframeValue = frame.value

                            if adj:
                                keyframeValue = -keyframeValue

                            print(keyframeValue)
                            fcurve.keyframe_points.insert(frame.num, keyframeValue) #XXX consider LINEAR interpolation

                # TODO: Animations seem right, but it looks like we still need to manually pose?

                for frame_index in range(animationLength):
                    translation = tuple(pos_fcurves[axis_idx].evaluate(frame_index) for axis_idx in range(3))

                    # TODO: Get this from the bone?
                    scale = (1, 1, 1)

                    radians = tuple(rot_fcurves[axis_idx].evaluate(frame_index) for axis_idx in range(3))

                    for i in range(3):
                        assert translation[i] is not None, "Undefined translation!" + str(translation)
                        assert scale[i] is not None, "Undefined scale!" + str(scale)
                        assert radians[i] is not None, "Undefined radians!" + str(radians)

                    boneChannels = boneTransforms.getBoneChannels(bone_id)
                    boneChannels.translationChannel.setKeyframe(frame_index, translation)
                    boneChannels.scaleChannel.setKeyframe(frame_index, scale)
                    boneChannels.radiansChannel.setKeyframe(frame_index, radians)

            return

            # Poses model w/ calculated transforms and saves all keyframes
            # TODO: Only do these if keyframes are defined!
            for frame_index in range(animationLength):
                # Positions all bones as expected for each frame.
                for bone_id in get_bone_ids_in_order(bones_parents_ids):
                    anod_id = csab_anim.per_bone_indices[bone_id]
                    if anod_id < 0:
                        continue #this bone is not animated
                    #blender_posebone = boneid_posebone_map[bone_id]

                    #parent_matrix = (blender_posebone.parent.matrix.copy() if blender_posebone.parent is not None else Matrix.Identity(4))
                    #local_anim_pose_matrix = boneTransforms.getTransformKeyframe(bone_id, frame_index)

                    #anim_pose_matrix = local_anim_pose_matrix * parent_matrix
                    #blender_posebone.matrix = anim_pose_matrix

                    blender_posebone.matrix = getWorldTransformCsab(boneid_posebone_map, boneChannels, bone_id, frame_index).transposed()

                scene.update()

                # Saves all bones as a frame
                scene.frame_set(frame_index)
                for bone_id in get_bone_ids_in_order(bones_parents_ids):
                    blender_posebone = boneid_posebone_map[bone_id]

                    # TODO: Only do these if keyframes are defined!
                    blender_posebone.keyframe_insert('rotation_euler')
                    #blender_posebone.keyframe_insert('rotation_quaternion')
                    blender_posebone.keyframe_insert('location')

            #TODO does not account for multiple animations
            scene.frame_start = 0
            scene.frame_end = csab_anim.last_frame
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

def getWorldTransformCsab(boneid_posebone_map, bone_channels, bone_id, frame_index):
    M = bone_channels.getTransformKeyframe(bone_id, frame_index)

    posebone = boneid_posebone_map[bone_id]
    parent_posebone = posebone.parent
    parent_posebone_id = int(parent_posebone.name.replace("bone_", ""))

    if (parent_posebone_id != -1): P = getWorldTransformCsab(bones, parent_posebone_id)
    else: P = mathutils.Matrix.Translation((0, 0, 0)).to_4x4()

    return M * P

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
