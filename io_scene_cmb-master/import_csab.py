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
    
    def __init__(self, csab_parsed, anim_name="anim"):
        self.csab_parsed = csab_parsed
        
        # self.blender = ValueHolder()
        # self.blender.anim_name = anim_name
        # self.blender.armature_object = None #TODO
        
        self.anim_name = anim_name
        self.bone_mismatch = False #TODO quick hacky way to show bone mismatch error after done importing
    
    def import_anims(self):
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
    
        for anim_id, csab_anim in enumerate(x.data for x in csab_parsed.animations):
            num_anims = len(csab_parsed.animations)
            if num_anims > 1:
                
                print("WARNING: This CSAB file contains {num_anims} animations. For now, only the first animation will be loaded.".format(num_anims=num_anims))
                
                #TODO use this when multiple anims are supported
                # digits = len(str(num_anims-1))
                # anim_full_name = "{anim_name}_{num:0{digits}}".format(anim_name=self.anim_name, num=anim_id, digits=digits)
                
                #temporary until multiple anim support
                anim_full_name = "{anim_name}_1-of-{num_anims}}".format(anim_name=self.anim_name, num_anims=num_anims)
            else:
                anim_full_name = self.anim_name
        
            #Check that the number of bones in the animation matches the number of bones in the armature
            armobj = armature_object
            anim_bones = csab_anim.num_bones
            arm_bones = len(armobj.pose.bones)
            if anim_bones != arm_bones:
                print("WARNING: Bone number mismatch. Animation contains {anim_bones} bones, but the selected armature contains {arm_bones} bones.".format(anim_bones=anim_bones, arm_bones=arm_bones))
                self.bone_mismatch = True
        
            #Prepare armature for animation, prepare animation & action
            armobj.animation_data_clear()
            armobj.animation_data_create()
            armobj.animation_data.action = bpy.data.actions.new(anim_full_name)
            action = armobj.animation_data.action
            
            
            #Get bone ids and parents, also map bone ids to Blender PoseBones. TODO someday use custom property for bone_ids
            bones_parents_ids = []
            boneid_posebone_map = dict()
            
            for posebone in armobj.pose.bones:
                bone_id = int(posebone.name)
                boneid_posebone_map[bone_id] = posebone
                
                parent_bone = posebone.parent
                parent_bone_id = -1 if parent_bone is None else int(parent_bone.name)
                bones_parents_ids.append((bone_id, parent_bone_id))
            
            #Process bones in reverse order from child to parent
            for bone_id in reversed(get_bone_ids_in_order(bones_parents_ids)):
                try:
                    anod_id = csab_anim.per_bone_indices[bone_id]
                except IndexError:
                    #raise BoneMismatchError("Attempted to animate nonexistent bone. Are you sure this is the right model for this animation?")
                    print("WARNING: Attempted to animate nonexistent bone {bone_id}. Are you sure this is the right model for this animation? Skipping this bone.".format(bone_id=bone_id))
                    continue
                if anod_id < 0:
                    continue #this bone is not animated
                anod = csab_anim.anod_chunks[anod_id].data
                blender_posebone = boneid_posebone_map[bone_id]
                
                parent_matrix = (blender_posebone.parent.matrix.copy() if blender_posebone.parent is not None else Matrix.Identity(4))
                local_matrix = parent_matrix.inverted() * blender_posebone.matrix
                local_position = local_matrix.to_translation()
                local_rotation = local_matrix.to_euler('XYZ')
            
                ### TRANSLATION: populate FCurves with local position pose values ###
                pos_all_keyframes = set() #position keyframes numbers for all axes
                #pos_all_keyframes = set(range(animation.last_frame + 1)) #TODO: Remember how a translation during a rotation should theoretically need a translation keyframe on every frame of rotation? This just makes every frame a keyframe. Test this with the Link's fairy revive animation, see if it makes any difference (i.e. smoother animation)
                pos_fcurves = []
                
                #For each axis:
                for axis_idx, axis in enumerate((anod.posx, anod.posy, anod.posz)):
                    
                    #create new fcurve
                    data_path = 'pose.bones["{0}"].location'.format(blender_posebone.name)
                    fcurve = action.fcurves.new(data_path=data_path, index=axis_idx)
                    pos_fcurves.append(fcurve)
                    
                    if axis is None:
                        #Animation is not defined for this axis, so make a flat fcurve from local bone translation
                        keyframe_value = local_position[axis_idx]
                        fcurve.keyframe_points.insert(0, keyframe_value)
                        pos_all_keyframes.add(0)
                    else:
                        #Animation is defined for this axis
                        #Populate the fcurve and add all frame #s to pos_all_keyframes
                        #Note: In theory, you should have a position keyframe for every frame the bone is simultaneously translating and rotating (we don't). In practice, though, it doesn't seem to make a visible difference. TODO: there's a test above we should do on Link's fairy revive animation
                        for frame in axis.data.frames:
                            keyframe_value = frame.value * GLOBAL_SCALE
                            fcurve.keyframe_points.insert(frame.num, keyframe_value) #XXX consider LINEAR interpolation
                            pos_all_keyframes.add(frame.num)
                
                ### ROTATION: populate FCurves with local rotation pose values ###
                rot_all_keyframes = set() #rotation keyframes numbers for all axes
                blender_posebone.rotation_mode = 'XYZ'
                rot_fcurves = []
                
                #For each axis:
                for axis_idx, axis in enumerate((anod.rotx, anod.roty, anod.rotz)):
                    
                    #create new fcurve
                    data_path = 'pose.bones["{0}"].rotation_euler'.format(blender_posebone.name)
                    fcurve = action.fcurves.new(data_path=data_path, index=axis_idx)
                    rot_fcurves.append(fcurve)
                    
                    if axis is None:
                        #Animation is not defined for this axis, so make a flat fcurve from local bone rotation
                        keyframe_value = local_rotation[axis_idx]
                        fcurve.keyframe_points.insert(0, keyframe_value)
                        rot_all_keyframes.add(0)
                    else:
                        #Animation is defined for this axis
                        #Populate the fcurve and add all frame #s to rot_all_keyframes
                        for frame in axis.data.frames:
                            keyframe_value = frame.value
                            fcurve.keyframe_points.insert(frame.num, keyframe_value) #XXX consider LINEAR interpolation
                            rot_all_keyframes.add(frame.num)
            
                ### TRANSLATION & ROTATION: get evaluated FCurve values of local animation poses ###
                pos_local_anims = [] #(x,y,z) local pose for each frame in pos_all_keyframes + rot_all_keyframes
                rot_local_anims = [] #(x,y,z) local pose for each frame in pos_all_keyframes + rot_all_keyframes
                for frame in sorted(pos_all_keyframes | rot_all_keyframes):
                    pos_keyframe_values = tuple(pos_fcurves[axis_idx].evaluate(frame) for axis_idx in range(3))
                    pos_local_anims.append(pos_keyframe_values)
                    rot_keyframe_values = tuple(rot_fcurves[axis_idx].evaluate(frame) for axis_idx in range(3))
                    rot_local_anims.append(rot_keyframe_values)
                    
                ### TRANSLATION & ROTATION: pose the Blender bone and create keyframes ###
                for frame, pos_local_pose, rot_local_pose in zip(sorted(pos_all_keyframes | rot_all_keyframes), pos_local_anims, rot_local_anims):
                    scene.frame_set(frame)

                    local_anim_pos = Matrix.Translation(pos_local_pose)
                    local_anim_rot = Euler(rot_local_pose, 'XYZ').to_matrix().to_4x4()
                    
                    local_anim_pose_matrix = local_anim_pos * local_anim_rot
                    anim_pose_matrix = parent_matrix * local_anim_pose_matrix
                    blender_posebone.matrix = anim_pose_matrix
                    scene.update()

                    if frame in rot_all_keyframes:
                        blender_posebone.keyframe_insert('rotation_euler')
                    if frame in pos_all_keyframes:
                        blender_posebone.keyframe_insert('location')
                
            #TODO does not account for multiple animations
            scene.frame_start = 0
            scene.frame_end = csab_anim.last_frame
            scene.frame_set(0)
            
            break #XXX temporary, ensures only first anim is imported
            
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
