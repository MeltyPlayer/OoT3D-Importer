#!/usr/bin/env python3
'''Blender import addon for CMB model format (from Legend of Zelda: Ocarina of Time 3D & Majora's Mask 3D)
'''

import math
from itertools import groupby, cycle
from operator import itemgetter
from collections import defaultdict

#Allow modules used by this addon to be reloaded by pressing F8 in Blender
if "bpy" in locals():
    import importlib
    if "cmb" in locals():
        importlib.reload(cmb)
    if "common" in locals():
        importlib.reload(common)

import bpy
from mathutils import Matrix, Vector, Euler, Quaternion

from . import cmb
from .common import (
        GLOBAL_SCALE,
        axis_correction_matrix, #TODO use this someday
        ValueHolder,
        get_bone_ids_in_order,
)


BONE_SIZE = 0.75 #determines the size of each bone in the armature

LOG_MODEL = False #XXX There's no logging code for CMB at the moment
LOG_MODEL_PATH = "/home/whatagotchi/Projects/N64/OoT_N64_3DS/blender_addon/bpy_logfile_cmb.txt"

#[ ] TODO: UNUSED STUFF: pop up a message if it detects unused meshes, textures, materials, etc
#[ ] TODO: NO ARMATURE OPTION: consider always importing armature instead of making it an option (many models look messed up without an armature to pretransform faces and stuff, and you can always go back to rest position anyway)
#[x] TODO: IMPORT NORMALS: will eventually need to import normals to make it look not-blocky
#[X] TODO: ARMATURE/EMPTY NAME: consider always giving mesh names a suffix so the parent can have the original CMB name
#[~] TODO: EZ MESH COMBINING: consider leaving mesh combining to the user (Ctrl-J) if it plays nice with imported custom normals. It saves having to make a mesh chooser for import (just delete unwanted meshes and combine) (While at it, see if removing loose geometry plays nice with custom normals.)
#[ ] TODO: axis_idx is fine bone idx (or other idx I guess) is NOT! rename rename.


class CmbImporter:
    '''Imports a parsed cmb file into Blender

    Specifying the file:
        One of the following must be specified. (If both are specified, cmb_parsed is used for the CMB file and filepath is used only in warning messages.)
        - filepath: path to a CMB model file.
        - cmb_parsed: a parsed cmb model object,i.e. the object returned from cmb.parse().
    
    Options:
        opt_import_armature: if True, import the armature (default True). Otherwise, all imported meshes are parented to an Empty
    '''
    def __init__(self, filepath=None, cmb_parsed=None, opt_import_armature=True):
        
        if filepath is None and cmb_parsed is None:
            raise ValueError("filepath or cmb_parsed must be specified")
        self.filepath = filepath
        self.cmb_parsed = cmb_parsed

        # user-defined importer options
        self.options = ValueHolder()
        self.options.import_armature = opt_import_armature #TODO do away with this, always do armature
        
        # helper variables for dealing with bones/armature stuff
        self.bonehelpers = ValueHolder()
        self.bonehelpers.idx_cmbbone_map = None    #{bone id: CMB bone (from parsed CMB model)}
        self.bonehelpers.idx_bonename_map = None   #{bone id: bone name in Blender}
        self.bonehelpers.idx_bleditbone_map = None #{bone id: Blender editbone}
        self.bonehelpers.idxs_in_order = None #list of bone ids in order from parent to child
                                            #TODO CSAB: self.bonehelpers.idxs_in_order is only used for anim import

        #vertex data ready to be imported into Blender
        self.by_mesh = ValueHolder()
        self.by_mesh.ids = []
        self.by_mesh.indices = []
        self.by_mesh.pretrans_indices = []
        self.by_mesh.vtxgroups = []
        self.by_mesh.positions = []
        self.by_mesh.normals = []
        self.by_mesh.colors = [] #TODO
        self.by_mesh.texcoords = [] #TODO
        
        # already-imported Blender data and objects
        self.blender = ValueHolder()
        self.blender.mesh_objects = None
        self.blender.armature_object = None
        self.blender.empty_object = None
        
    def import_model(self):
        '''import the CMB model into Blender'''
        
        self.parse_cmb()
        
        self.get_vertex_data()

        #import armature
        if self.options.import_armature:
            self.import_armature()
            self.pretransform_vertices()
        else:
            self.create_empty()

        #import meshes
        self.import_meshes()

        #More armature-related stuff: Import vertex groups and parent mesh.
        if self.options.import_armature:
            self.import_vertexgroups()
            self.parent_meshes_to_armature()
            self.correct_axes_armature()
        else:
            self.parent_meshes_to_empty()
            self.correct_axes_empty()

        bpy.context.scene.update()
        print("Done importing.\n")

    def parse_cmb(self):
        filepath = self.filepath
        
        if self.cmb_parsed is not None:
            print("CMB file has already been read and parsed.")
        elif filepath is not None:
            print("Reading and parsing CMB file '{0}' [{1}] ...".format(bpy.path.basename(filepath), filepath))
            self.cmb_parsed = cmb.parse(filepath)
            print("...done reading CMB file.")
        else:
            raise ValueError("")
        
        self.name = self.cmb_parsed.name

    def get_vertex_data(self): #XXX may become get_mesh_data when it includes the material
        '''Get vertex data
        
        Get the vertex data:
            - vertex indices that form each triangle
            - vertex indices that need to be pretransformed by an armature bone
            - vertex groups for skinning
            - vertex positions, normals, [TODO colors, and texture coordinates]
        '''
        print("Getting vertex data...")

        #Meshes in MSHS chunk
        for mesh_id, cmb_mesh in enumerate(self.cmb_parsed.sklm_chunk.mshs_chunk.meshes):
            ### Part 1: get vertex data from the SEPD chunk and connected chunks ### 
            sepd_chunk = self.cmb_parsed.sklm_chunk.shp_chunk.sepd_chunks[cmb_mesh.sepd_id]
            # #Testing certain sepd chunks XXX
            if cmb_mesh.sepd_id != 0:
                #continue
                pass
            
            #XXX
            if mesh_id != 0:
                #continue
                pass
            #Testing for a special case I'm unsure about in MM3D
            if not (sepd_chunk.bones_per_vertex == 1 and
                    any(p.skinning_mode in ('skinning', 'skinning_no_pretransform') for p in sepd_chunk.prms_chunks) and
                    any(len(p.bone_indices) > 1 for p in sepd_chunk.prms_chunks)
                ):
                #continue
                pass
            
            print("Mesh: {0}, SEPD: {1}".format(mesh_id, cmb_mesh.sepd_id))
            #print(" bones_per_vertex: {}".format(sepd_chunk.bones_per_vertex))
            #print(" autogen flags: {}".format(sepd_chunk.autogen_flags))
            # if sepd_chunk.autogen_flags.bone_index_lookup or sepd_chunk.autogen_flags.bone_weights:
            #     raise ValueError("bones per vertex is 1 yet autogen_flags has bone_index_lookup {0} and bone_weights {1}".format(sepd_chunk.autogen_flags.bone_index_lookup, sepd_chunk.autogen_flags.bone_weights))
            # 
            # bl = list(set(sepd_chunk.vertex_arrays.bone_index_lookup.data))
            # bl.sort()
            # bl = bl[:20]
            # bw = list(set(sepd_chunk.vertex_arrays.bone_weights.data))
            # bw.sort()
            # bw = bw[:10]
            # print(" 20 bone index lookups: {}".format(bl))
            # print(" 10 bone weights: {}".format(bw))
            
            self.by_mesh.ids.append(mesh_id)
            indices_this_mesh = [] #vertex indices for triangles [(idx1, idx2, idx3), ...]
            pretrans_indices_this_mesh = defaultdict(set) #dict {bone_idx: set(vertex indices)}
            vtxgroups_this_mesh = defaultdict(set) #dict {(bone_idx, weight) : set(vertex indices)}
            positions_this_mesh = [] #vertex positions [(x,y,z), ...]
            normals_this_mesh = [] #vertex normals [(x,y,z), ...]
            #TODO colors, texcoords
            colors_this_mesh = [] #vertex colors [(r,g,b), ...]
            texcoords_this_mesh = [] #vertex texture coordinates [(u,v), ...]

            #each item in the chunkified lists below applies to a single vertex
            bone_lookups = chunkify(sepd_chunk.vertex_arrays.bone_index_lookup.data, sepd_chunk.bones_per_vertex)
            bone_weights = chunkify(sepd_chunk.vertex_arrays.bone_weights.data, sepd_chunk.bones_per_vertex)

            #PRMS chunks
            for prms_id, prms_chunk in enumerate(sepd_chunk.prms_chunks): #XXX prms_id is for debugging
                if prms_id != 0: #debugging, only do this PRMS chunk
                    #continue
                    pass
                print(" PRMS: {}".format(prms_id))
                
                #XXX
                #print("  bone indices: {}".format(list(prms_chunk.bone_indices)))

                ## Get PRMS chunk's vertex indices ##
                cmb_indices_flat_this_prms = prms_chunk.prm_chunk.indices
                #Offset the vertices so Blender can use them
                blender_vertindex_offset = len(positions_this_mesh) # number of vertices so far in this mesh
                blender_indices_flat_this_prms = [x + blender_vertindex_offset for x in cmb_indices_flat_this_prms]
                indices_this_mesh.extend(chunkify(blender_indices_flat_this_prms, 3))

                ## Get PRMS chunk's vertex groups and vertices needing pretransformation ##
                if self.options.import_armature:

                    #skinning mode: single bone as parent:
                    if prms_chunk.skinning_mode == 'single_bone':
                        bone_idx = prms_chunk.bone_indices[0]
                        key = (bone_idx, 1.0)
                        vtxgroups_this_mesh[key].update(blender_indices_flat_this_prms)

                        #Keep track of the vertices so they can be pretransformed later
                        pretrans_indices_this_mesh[bone_idx].update(blender_indices_flat_this_prms)

                    #skinning mode: skinning with bone lookup and weights:
                    elif prms_chunk.skinning_mode in ('skinning', 'skinning_no_pretransform'):

                        #print(cmb_indices_flat_this_prms) #XXX
                        # print("Highest CMB index:   {}".format(max(cmb_indices_flat_this_prms)))
                        # print("Highest Blender idx: {}".format(max(blender_indices_flat_this_prms)))

                        for cmb_idx, blender_idx in zip(cmb_indices_flat_this_prms, blender_indices_flat_this_prms):

                            if sepd_chunk.bones_per_vertex == 1:
                                
                                if self.cmb_parsed.game == "Ocarina3D":
                                #if False:
                                #if True:
                                    #When bones_per_vertex == 1, it actually uses 2 bones per vertex, but the other bone is determined automatically based on the first bone. Bone weights are also determined automatically.
                                    #TODO or maybe I'm wrong and it's only weighed to the first bone somehow, since bone weight is always 1,0. Check back when I don't have a headache
                                    
                                    #TODO this needs testing
                                    bone_lookup = sepd_chunk.vertex_arrays.bone_index_lookup.data[cmb_idx]
                                    bone_lookups_this_vertex = (bone_lookup,) #if this works instead, TODO update the wiki
                                    bone_weights_this_vertex = (1.0,)
                                    
                                    # bone_lookup2 = (bone_lookup + 1) % prms_chunk.num_bone_indices
                                    # bone_lookups_this_vertex = (bone_lookup, bone_lookup2)
                                    # bone_weights_this_vertex = (1.0, 0.0)
                                    
                                else: #Majora's Mask 3D
                                    
                                    #TODO this needs testing
                                    bone_lookups_this_vertex = (0,)
                                    bone_weights_this_vertex = (1.0,) #If this works, TODO update the wiki
                                
                            else:
                                if sepd_chunk.autogen_flags.bone_index_lookup:
                                    #generate bone lookups instead of reading from file
                                    bone_lookups_this_vertex = range(sepd_chunk.bones_per_vertex)
                                else:
                                    bone_lookups_this_vertex = bone_lookups[cmb_idx]

                                if sepd_chunk.autogen_flags.bone_weights:
                                    #generate bone weights instead of reading from file
                                    #TODO this needs testing. It may not be the right weights. I'm making the assumption that bone weights are split evenly between the bones. Unfortunately, there aren't many models I can test this on
                                    bone_weights_this_vertex = [1/sepd_chunk.bones_per_vertex] * (sepd_chunk.bones_per_vertex)
                                else:
                                    bone_weights_this_vertex = bone_weights[cmb_idx]
                            
                            #Add to the dict vtxgroups_this_mesh:
                            # - key is tuple of (bone index, weight)
                            # - value for each key is a list of indicies using that bone index and weight
                            
                            for bone_lookup, bone_weight in zip(bone_lookups_this_vertex, bone_weights_this_vertex):
                                try: #XXX
                                    bone_idx = prms_chunk.bone_indices[bone_lookup]
                                except IndexError:
                                    raise IndexError("Tried to get index {0} of bone indices {1}".format(bone_lookup, list(prms_chunk.bone_indices)))
                                except TypeError:
                                    raise TypeError("Tried to use {} as an index".format(bone_lookup))
                                #test: only add vertex group for the specified bone:
                                if bone_idx != 10:
                                    #continue
                                    pass
                                #print("bone_lookup: {0}, bone_idx: {1}, vertidx: {2}, bl_vertidx: {3}".format(bone_lookup, bone_idx, cmb_idx, blender_idx))
                                bone_weight *= sepd_chunk.vertex_arrays.bone_weights.scale
                                key = (bone_idx, bone_weight)
                                vtxgroups_this_mesh[key].add(blender_idx)
                            
                            #Keep track of the vertices so they can be pretransformed later
                            if prms_chunk.skinning_mode == 'skinning':
                                bone_lookup = bone_lookups_this_vertex[0]
                                bone_idx = prms_chunk.bone_indices[bone_lookup]
                                pretrans_indices_this_mesh[bone_idx].add(blender_idx)
                
                ## Get PRMS chunk's vertex positions ##
                max_index = max(item for sublist in indices_this_mesh for item in sublist) #take max after flattening indices list
                scale = sepd_chunk.vertex_arrays.positions.scale
                positions_flat = [x * scale * GLOBAL_SCALE for x in sepd_chunk.vertex_arrays.positions.data]
                positions_this_prms = chunkify(positions_flat, 3)[:max_index+1] #truncate to highest used vertex index
                positions_this_mesh.extend(positions_this_prms)
                
                ## Get PRMS chunk's normals ##
                if not sepd_chunk.autogen_flags.normals:
                    scale = sepd_chunk.vertex_arrays.normals.scale
                    normals_flat = [x * scale for x in sepd_chunk.vertex_arrays.normals.data]
                    normals_this_prms = chunkify(normals_flat, 3)[:max_index+1] #truncate to highest used vertex index
                    
                    #if there are fewer normals than positions, pad with (0,0,0) normals to match the number of positions. Blender turns those (0,0,0) into autogenerated normals.
                    num_positions = len(positions_this_prms)
                    num_normals = len(normals_this_prms)
                    if num_normals < num_positions:
                        normals_this_prms.extend([(0,0,0)] * (num_positions - num_normals))
                        print("~~ Mesh {0}, PRMS {1}: added {2} zero normals".format(mesh_id, prms_id, num_positions - num_normals))
                    #if there are too many normals, truncate to match the number of positions
                    elif num_normals > num_positions:
                        extra_normals = normals_this_prms[num_positions:]
                        normals_this_prms = normals_this_prms[:num_positions]
                        print("~~ Mesh {0}, PRMS {1}: removed {2} extra normals:".format(mesh_id, prms_id, num_normals - num_positions))
                        for n in extra_normals:
                            print("     {}".format(n))
                        print("     Last used normal: {}".format([round(x, 2) for x in normals_this_prms[-1]]))
                    normals_this_mesh.extend(normals_this_prms)
            #End of this PRMS chunk
            
            self.by_mesh.indices.append(indices_this_mesh)
            self.by_mesh.vtxgroups.append(vtxgroups_this_mesh)
            self.by_mesh.pretrans_indices.append(pretrans_indices_this_mesh)
            self.by_mesh.positions.append(positions_this_mesh)
            self.by_mesh.normals.append(normals_this_mesh)
            ### End of Part 1 ###
            
            ### Part 2: get material/texture data from the MATS chunk's material and connected chunks ###
            cmb_material = self.cmb_parsed.mats_chunk.materials[cmb_mesh.material_id]
            if cmb_material.texture_id_0 == -1:
                cmb_texture_0 = None
            else:
                cmb_texture_0 = self.cmb_parsed.tex_chunk.textures[cmb_material.texture_id_0]
            
            # print(cmb_texture_0.format)
            # if cmb_texture_0.pixels is not None:
            #     print(len(cmb_texture_0.pixels))
            
            ### End of Part 2 ###
        #End of this cmb_mesh
        
        print("...done getting vertices.")

    def import_armature(self):
        '''Create the armature, then parent and position the bones.'''
        print("Importing armature...")

        cmb_parsed = self.cmb_parsed

        #Create the bone names to be used for vertex groups and bones.
        bone_ids = [cmb_bone.bone_id for cmb_bone in cmb_parsed.skl_chunk.bones]
        bone_name_max_len = max(len(str(bone_id)) for bone_id in bone_ids)
        self.bonehelpers.idx_bonename_map = {bone_id: ("{0:0" + str(bone_name_max_len) + "}").format(bone_id) for bone_id in bone_ids}

        #Add armature.
        arm_name = self.name
        armdata = bpy.data.armatures.new(arm_name)
        armobj = bpy.data.objects.new(armdata.name, armdata)
        bpy.context.scene.objects.link(armobj)
        self.blender.name = armdata.name

        #Get ready to add bones to armature.
        for x in bpy.context.scene.objects:
            x.select = False #deselect all objects
        armobj.select = True
        bpy.context.scene.objects.active = armobj
        bpy.ops.object.mode_set(mode='EDIT')
        boneidx_bleditbone_map = dict() #{cmb bone id: blender EditBone}
        self.bonehelpers.idx_bleditbone_map = boneidx_bleditbone_map

        #Add bones to armature.
        for cmb_bone in cmb_parsed.skl_chunk.bones:
            bone_name = self.bonehelpers.idx_bonename_map[cmb_bone.bone_id]
            blbone = armobj.data.edit_bones.new(name=bone_name)
            boneidx_bleditbone_map[cmb_bone.bone_id] = blbone
            #bone.select = True
        
        #Parent the bones.
        for cmb_bone in cmb_parsed.skl_chunk.bones:
            bone_id = cmb_bone.bone_id
            parent_id = cmb_bone.parent_bone_id
            if parent_id != -1: #if not the root bone
                boneidx_bleditbone_map[bone_id].parent = boneidx_bleditbone_map[parent_id]

        #Get a list of bones in order from highest in the hierarchy to lowest.
        #This list is used to process bones in that order.
        bones_parents_ids = [(cmb_bone.bone_id, cmb_bone.parent_bone_id) for cmb_bone in cmb_parsed.skl_chunk.bones]
        bone_ids_in_order = get_bone_ids_in_order(bones_parents_ids)
        self.bonehelpers.idxs_in_order = bone_ids_in_order #TODO CSAB: self.bonehelpers.idxs_in_order is only used for anim import
            
        #Position the bones using the ordered bone list obtained in the previous step.
        boneidx_cmbbone_map = {cmb_bone.bone_id: cmb_bone for cmb_bone in cmb_parsed.skl_chunk.bones}
        self.bonehelpers.idx_cmbbone_map = boneidx_cmbbone_map
        for bone_id in bone_ids_in_order:
            print(" Bone: {}".format(bone_id))
            cmb_bone = boneidx_cmbbone_map[bone_id]
            blbone = boneidx_bleditbone_map[bone_id]
            if cmb_bone.parent_bone_id == -1:
                parent_matrix = Matrix.Identity(4)
            else:
                blbone_parent = boneidx_bleditbone_map[cmb_bone.parent_bone_id]
                parent_matrix = blbone_parent.matrix

            #position, rotation
            position = [x * GLOBAL_SCALE for x in cmb_bone.position]
            mat_pos = Matrix.Translation(position)
            rotation = Euler(cmb_bone.rotation, 'XYZ')
            mat_rot = rotation.to_matrix().to_4x4()
            bone_matrix = mat_pos * mat_rot
            blbone.tail = Vector((0, BONE_SIZE, 0))
            blbone.matrix = parent_matrix * bone_matrix
        #Done positioning the bones.
        

        #Finish up
        bpy.ops.object.mode_set(mode='OBJECT')
        armobj.select = False
        self.blender.armature_object = armobj
        print("...done importing armature.")

    def pretransform_vertices(self):
        '''pre-transform vertices for things like characters' faces and held objects'''
        for pretrans_indices_this_mesh, positions_this_mesh, normals_this_mesh in zip( self.by_mesh.pretrans_indices, self.by_mesh.positions, self.by_mesh.normals):
            for bone_id, pretransform_indices in pretrans_indices_this_mesh.items():
                bleditbone = self.bonehelpers.idx_bleditbone_map[bone_id]
                for ptidx in pretransform_indices:
                    #pretransform affected vertex positions
                    oldvtx = Vector(positions_this_mesh[ptidx])
                    oldvtx.resize_4d()
                    newvtx = bleditbone.matrix * oldvtx
                    newvtx.resize_3d()
                    positions_this_mesh[ptidx] = newvtx

                    #pretransform affected normals (unless there are 0 normals, i.e. normals are autogenerated)
                    if normals_this_mesh:
                        oldnml = Vector(normals_this_mesh[ptidx])
                        bone_rotation = bleditbone.matrix.to_quaternion().to_matrix()
                        newnml = bone_rotation * oldnml
                        normals_this_mesh[ptidx] = newnml

    def import_meshes(self):
        '''Create mesh from vertices obtained in get_vertex_data().'''
        print("Importing meshes...")
        
        meshes_name = self.blender.name
        digits = len(str(len(self.by_mesh.positions) - 1))
        blender_meshobjs = []

        for mesh_id, vertices_this_mesh, indices_this_mesh, normals_this_mesh in zip(self.by_mesh.ids, self.by_mesh.positions, self.by_mesh.indices, self.by_mesh.normals):
        
            ## Create blank Blender mesh ##
            
            
            mesh_name = "{meshes_name}.{mesh_id:0{digits}}".format(meshes_name=meshes_name, mesh_id=mesh_id, digits=digits)
            #mesh_name = meshes_name
            
            meshdata = bpy.data.meshes.new(mesh_name)
            meshobj = bpy.data.objects.new(meshdata.name, meshdata)
            bpy.context.scene.objects.link(meshobj)
            blender_meshobjs.append(meshobj)
            
            print(" Mesh {}".format(meshobj.name))
            
            ## Populate Blender mesh with vertices and faces ##
            meshdata.from_pydata(vertices_this_mesh, [], indices_this_mesh)
            
            ## Add normals ##
            if normals_this_mesh:
                meshdata.use_auto_smooth = True
                meshdata.normals_split_custom_set_from_vertices(normals_this_mesh)
                
                # num_normals = len(normals_this_mesh)
                # 
                # if num_normals >= len(meshdata.vertices):
                #     meshdata.normals_split_custom_set_from_vertices(normals_this_mesh[:len(meshdata.vertices)]) #truncate normals to num vertices for now
                # 
                #     #XXX debug print
                #     if num_normals > len(meshdata.vertices):
                #         extra_normals = normals_this_mesh[len(meshdata.vertices):]
                #         print("~~ Mesh '{0}' has extra normals: {1}".format(meshobj.name, extra_normals))
                #         last_valid_normal = normals_this_mesh[len(meshdata.vertices) - 1:len(meshdata.vertices)]
                #         print("   last non-extra normal: {}".format(last_valid_normal))
                # 
                # else:
                #     #If there aren't enough normals, fill in missing normals with (0,0,0). This instructs Blender to use automatically generated normals instead.
                #     #It may be that extra normals like this are always for unused vertices, and that more zealous removal of unused vertices will prevent this from occurring.
                # 
                #     normals_plus_zeroes = normals_this_mesh + [(0,0,0)] * (len(meshdata.vertices) - num_normals)
                #     meshdata.normals_split_custom_set_from_vertices(normals_plus_zeroes)
                # 
                # 
                #     #XXX debug print
                #     print("== Not enough custom normals for mesh {}".format(meshobj.name))
                #     print("  Only {0} normals (for {1} verts)".format(num_normals, len(meshdata.vertices)))
                #     print("Filling in the rest with zero vectors (i.e. keep auto normals, yay!)")
                # 
                #     #XXX debug: select the vertices that were given (0,0,0) normals this way
                #     for i, v in enumerate(meshdata.vertices):
                #         if i <= num_normals - 1:
                #             v.select = False
                #         else:
                #             v.select = True
                #             print(i, end=", ")
                #     print()
                #     for e in meshdata.edges:
                #         e.select = False
                #     for p in meshdata.polygons:
                #         p.select = False
                    
                    
                
            else: #XXX
                pass
                #print("== No custom normals for mesh {}".format(meshobj.name))
                
                #TODO consider enabling auto smooth (0 degrees) even if the mesh doesn't use custom normals, so that joining meshes doesn't disable auto smooth (which toggles off custom normals)
                #meshdata.use_auto_smooth = True
                #meshdata.auto_smooth_angle = 0
            
            
            corrected = meshdata.validate()
            if corrected:
                print("Corrected invalid geometry in mesh {}".format(meshdata.name))
                #TODO show a pop-up warning of probably-messed-up meshes

        self.blender.mesh_objects = blender_meshobjs
        print("...done importing mesh.")

    def import_vertexgroups(self):
        '''Create vertex groups from vertex group data obtained in get_vertex_data().'''
        print("Importing vertex groups...")

        boneidx_bonename_map = self.bonehelpers.idx_bonename_map
        
        #add the vertex groups to Blender
        for mesh_vtxgroups, meshobj in zip(self.by_mesh.vtxgroups, self.blender.mesh_objects):
            for (bone_id, bone_weight), vertex_idxs in mesh_vtxgroups.items():
                if boneidx_bonename_map[bone_id] not in meshobj.vertex_groups:
                    meshobj.vertex_groups.new(boneidx_bonename_map[bone_id])
                meshobj.vertex_groups[boneidx_bonename_map[bone_id]].add(tuple(vertex_idxs), bone_weight, 'ADD')
        print("...done importing vertex groups.")

    def parent_meshes_to_armature(self):
        '''parent meshes to the armature and set the armature modifier for each'''
        armobj = self.blender.armature_object
        for meshobj in self.blender.mesh_objects:
                armmod = meshobj.modifiers.new(armobj.name, 'ARMATURE')
                armmod.object = armobj
                meshobj.parent = armobj

    def create_empty(self):
        '''create an empty (meshes will later be parented to this)'''
        empty_name = self.name
        empty_obj = bpy.data.objects.new(empty_name, None) #TODO *data vs *_data, *_obj, and such
        bpy.context.scene.objects.link(empty_obj)
        self.blender.empty_object = empty_obj
        self.blender.name = empty_obj.name
        

    def parent_meshes_to_empty(self):
        '''parent meshes to the empty created earlier'''
        empty_obj = self.blender.empty_object
        for meshobj in self.blender.mesh_objects:
            meshobj.parent = empty_obj
        self.blender.empty_object = empty_obj

    def correct_axes_armature(self):
        '''rotate the armature 90 degrees on the X axis (since Y is up in CMB and Z is up in Blender)'''
        self.blender.armature_object.rotation_euler = (math.radians(90), 0, 0)

    def correct_axes_empty(self):
        '''rotate the empty 90 degrees on the X axis (since Y is up in CMB and Z is up in Blender)'''
        self.blender.empty_object.rotation_euler = (math.radians(90), 0, 0)


def chunkify(l, n, indexable=False):
    '''split list/tuple/etc l into chunks of length n, omitting the final chunk if there are fewer than n elements left at the end

    e.g. chunkify([1,2,3,4,5,6,7,8], 3) = [[1,2,3], [4,5,6]]
    '''
    #TODO: instead of using indexable=, try turning chunkify into a generator? (you can always convert the result in to a list in cases where you need a list) And make it accept a generator, i.e. don't depend on len()
    
    return [l[x:x+n] for x in range(0, len(l) - n + 1, n)]

    #indexable=True returns a list (like what it does by default now), indexable=False returns a generator expression.
    #Why? Because an indexable list is needed for when you need to take a slice or replace elements (like when you pre-transform vertex positions and normals). The rest of the time, you can save memory by returning a generator expression.
    # if indexable:
    #     return [l[x:x+n] for x in range(0, len(l) - n + 1, n)]
    # else:
    #     return (l[x:x+n] for x in range(0, len(l) - n + 1, n))


def read(filepath, **options):
    
    #TODO: logging (from within CmbImporter, passed as an option argument?). Armature vs Empty option.
    
    cmb_importer = CmbImporter(filepath, **options)
    #cmb_importer = CmbImporter(filepath, opt_import_armature=False) #XXX
    cmb_importer.import_model()
    