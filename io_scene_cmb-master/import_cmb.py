import sys, os, array, bpy, bmesh, operator, math, mathutils

from .cmb import readCmb
from .ctrTexture import DecodeBuffer
from .cmbEnums import SkinningMode, DataTypes
from .utils import (getWorldTransformCmb, transformPosition, transformNormal)
from .io_utils import (readArray, readDataType, readUInt32, readString, getFlag, getDataTypeSize)
from .common import CLIP_START, CLIP_END, GLOBAL_SCALE

#TODO: Clean up
def load_cmb( operator, context ):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.viewport_shade = 'MATERIAL'

    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.clip_start = CLIP_START
                area.spaces.active.clip_end = CLIP_END

    bpy.context.scene.render.engine = 'CYCLES'# Idc if you don't like cycles

    for f in enumerate(operator.files):
        fpath = operator.directory + f[1].name
        LoadModel(fpath)
        return {"FINISHED"}

def LoadModel(filepath):
    with open(filepath, "rb") as f:
        return LoadModelFromStream(f)

def LoadModelFromStream(f):
    startOff = 0
    if readString(f, 4) == "ZSI\x01":
        f.seek(16)
        while True:

            cmd0 = readUInt32(f)
            cmd1 = readUInt32(f)

            cmdType = cmd0 & 0xFF
            print(cmdType)

            if(cmdType == 0x14): break
            if(cmdType == 0x0A):
                f.seek(cmd1 + 20)
                entryOfs = readUInt32(f)
                f.seek(entryOfs + 24)
                cmbOfs = readUInt32(f)
                f.seek(cmbOfs + 16)

                startOff = f.tell()
                break

    f.seek(startOff)
    assert readString(f, 3) == "cmb", "Expected magic text to be cmb!"
    f.seek(startOff)

    cmb = readCmb(f, startOff)
    vb = cmb.vatr#VertexBufferInfo
    boneTransforms = {}

    # ################################################################
    # Build skeleton
    # ################################################################

    skeleton = bpy.data.armatures.new(cmb.name)# Create new armature
    skl_obj = cmb.editSkeleton = bpy.data.objects.new(skeleton.name, skeleton)# Create new armature object
    skl_obj.show_x_ray = True
    bpy.context.scene.objects.link(skl_obj)# Link armature to the scene
    bpy.context.scene.objects.active = skl_obj# Select the skeleton for editing
    bpy.ops.object.mode_set(mode='EDIT')# Set to edit mode

    for bone in cmb.skeleton:
        # Save the matrices so we don't have to recalculate them for single-binded meshes later
        boneTransforms[bone.id] = getWorldTransformCmb(cmb.skeleton, bone.id)

        eb = skeleton.edit_bones.new('bone_{}'.format(bone.id))

        eb.use_local_location = eb.use_inherit_scale = eb.use_inherit_rotation = eb.use_deform = True# Inherit rotation/scale and use deform

        eb.head = bone.translation# Set head position
        eb.matrix = boneTransforms[bone.id].transposed()# Apply matrix

        # This rotation screws up the bone rotations in the rig, but makes the
        # animations work as expected.
        # TODO: Is there a way to have working animations *and* a working rig?
        eb.tail = transformPosition([0.0, 1.0, 0.0], boneTransforms[bone.id])

        # This rotation makes the bone rotations in the rig look as expected,
        # but screws up the animations.
        #eb.tail = transformPosition([1.0, 0.0, 0.0], boneTransforms[bone.id])
        #eb.roll = -math.pi / 2

        # Assign parent bone
        if bone.parentId != -1:
            eb.parent = skeleton.edit_bones[bone.parentId]

            parent = cmb.skeleton[bone.parentId]
            # TODO: Cap parent bone length in a robust way.

        #eb.tail[1] += 0.001# Blender will delete all zero-length bones

        translation = eb.head.copy()

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    # ################################################################
    # Add Textures
    # ################################################################
    textureNames = []# Used as a lookup

    for t in cmb.textures:
        f.seek(cmb.texDataOfs + t.dataOffset + startOff)

        image = bpy.data.images.new('{}.png'.format(t.name), t.width, t.height, alpha=True)
        textureNames.append(image.name)
        # Note: Pixels are in floating-point values
        if(cmb.texDataOfs != 0):
            image.pixels = DecodeBuffer(readArray(f, t.dataLength, DataTypes.UByte), t.width, t.height, t.imageFormat, t.isETC1)
        image.update()# Updates the display image
        image.pack(True)# Pack the image into the .blend file. True = pack as .png

    # ################################################################
    # Add Materials
    # ################################################################
    materialNames = []# Used as a lookup

    #TODO: Mimic materials best as possible
    for m in cmb.materials:
        mat = bpy.data.materials.new('{}_mat'.format(cmb.name))# Create new material
        mat.use_nodes = True# Use nodes
        materialNames.append(mat.name)

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        mat.node_tree.nodes.remove(nodes.get('Diffuse BSDF'))# Remove the default material blender creates

        out = nodes.get("Material Output")# Output node
        sdr = nodes.new("ShaderNodeBsdfPrincipled")# Create new shader node to use
        texture = nodes.new("ShaderNodeTexImage")# Create new texture node
        if len(textureNames) > 0:
            texture.image = bpy.data.images.get(textureNames[m.TextureMappers[0].textureID])# Set the texture's image
        links.new(sdr.inputs[0], texture.outputs[0])# Link Image "Color" to shaders "Base Color"
        links.new(sdr.outputs[0], out.inputs[0])# Link shader output "BSDF" to material output "Surface"

    # ################################################################
    # Build Meshes
    # ################################################################
    MIndex = 0

    for mesh in cmb.meshes:
        shape = cmb.shapes[mesh.shapeIndex]
        indices = [faces for pset in shape.primitiveSets for faces in pset.primitive.indices]
        vertexCount = max(indices)+1
        vertices = []
        bindices = {}

        # Python doesn't have increment operator (afaik) so this must be ugly...
        inc = 0 #increment
        hasNrm = getFlag(shape.vertFlags, 1, inc)
        if cmb.version > 6: inc+=1 #Skip "HasTangents" for now
        hasClr = getFlag(shape.vertFlags, 2, inc)
        hasUv0 = getFlag(shape.vertFlags, 3, inc)
        hasUv1 = getFlag(shape.vertFlags, 4, inc)
        hasUv2 = getFlag(shape.vertFlags, 5, inc)
        hasBi  = getFlag(shape.vertFlags, 6, inc)
        hasBw  = getFlag(shape.vertFlags, 7, inc)

        # Create new mesh
        nmesh = bpy.data.meshes.new('Order:{}_VisID:{}'.format(MIndex,mesh.ID))# ID is used for visibility animations
        MIndex +=1
        nmesh.use_auto_smooth = True# Needed for custom split normals
        nmesh.materials.append(bpy.data.materials.get(materialNames[mesh.materialIndex]))# Add material to mesh

        obj = bpy.data.objects.new(nmesh.name, nmesh)# Create new mesh object
        obj.parent = skl_obj# Set parent skeleton

        ArmMod = obj.modifiers.new(skl_obj.name,"ARMATURE")
        ArmMod.object = skl_obj# Set the modifiers armature

        for bone in bpy.data.armatures[skeleton.name].bones.values():
            obj.vertex_groups.new(name=bone.name)

        # Get bone indices. We need to get these first because-
        # each primitive has it's own bone table
        for s in shape.primitiveSets:
            for i in s.primitive.indices:
                if(hasBi and s.skinningMode != SkinningMode.Single):
                    f.seek(cmb.vatrOfs + vb.bIndices.startOfs + shape.bIndices.start + i * shape.boneDimensions + startOff)
                    for bi in range(shape.boneDimensions):
                        bindices[i * shape.boneDimensions + bi] = s.boneTable[int(readDataType(f, shape.bIndices.dataType) * shape.bIndices.scale)]
                else: bindices[i] = shape.primitiveSets[0].boneTable[0]# For single-bind meshes

        # Create new bmesh
        bm = bmesh.new()
        bm.from_mesh(nmesh)
        weight_layer = bm.verts.layers.deform.new()# Add new deform layer

        # TODO: Support constants
        # Get vertices
        for i in range(vertexCount):
            v = Vertex()# Ugly because I don't care :)

            # Position
            f.seek(cmb.vatrOfs + vb.position.startOfs + shape.position.start + 3 * getDataTypeSize(shape.position.dataType) * i + startOff)
            bmv = bm.verts.new([e * shape.position.scale * GLOBAL_SCALE for e in readArray(f, 3, shape.position.dataType)])

            if(shape.primitiveSets[0].skinningMode != SkinningMode.Smooth):
                bmv.co = transformPosition(bmv.co, boneTransforms[bindices[i]])

            # Normal
            if hasNrm:
                f.seek(cmb.vatrOfs + vb.normal.startOfs + shape.normal.start + 3 * getDataTypeSize(shape.normal.dataType) * i + startOff)
                v.nrm = [e * shape.normal.scale for e in readArray(f, 3, shape.normal.dataType)]

                if(shape.primitiveSets[0].skinningMode != SkinningMode.Smooth):
                    v.nrm = transformNormal(v.nrm, boneTransforms[bindices[i]])

            # Color
            if hasClr:
                f.seek(cmb.vatrOfs + vb.color.startOfs + shape.color.start + 4 * getDataTypeSize(shape.color.dataType) * i + startOff)
                v.clr = [e * shape.color.scale for e in readArray(f, 4, shape.color.dataType)]

            # UV0
            if hasUv0:
                f.seek(cmb.vatrOfs + vb.uv0.startOfs + shape.uv0.start + 2 * getDataTypeSize(shape.uv0.dataType) * i + startOff)
                v.uv0 = [e * shape.uv0.scale for e in readArray(f, 2, shape.uv0.dataType)]

            # UV1
            if hasUv1:
                f.seek(cmb.vatrOfs + vb.uv1.startOfs + shape.uv1.start + 2 * getDataTypeSize(shape.uv1.dataType) * i + startOff)
                v.uv1 = [e * shape.uv1.scale for e in readArray(f, 2, shape.uv1.dataType)]

            # UV2
            if hasUv2:
                f.seek(cmb.vatrOfs + vb.uv2.startOfs + shape.uv2.start + 2 * getDataTypeSize(shape.uv2.dataType) * i + startOff)
                v.uv2 = [e * shape.uv2.scale for e in readArray(f, 2, shape.uv2.dataType)]

            # Bone Weights
            if hasBw:
                # For smooth meshes
                f.seek(cmb.vatrOfs + vb.bWeights.startOfs + shape.bWeights.start + i * shape.boneDimensions + startOff)
                for j in range(shape.boneDimensions):
                    weight = round(readDataType(f, shape.bWeights.dataType) * shape.bWeights.scale, 2)
                    if(weight > 0): bmv[weight_layer][bindices[i * shape.boneDimensions + j]] = weight
            else:
                # For single-bind meshes
                bmv[weight_layer][bindices[i]] = 1.0

            vertices.append(v)

        bm.verts.ensure_lookup_table()# Must always be called after adding/removing vertices or accessing them by index
        bm.verts.index_update()# Assign an index value to each vertex

        for i in range(0, len(indices), 3):
            try:
                face = bm.faces.new(bm.verts[j] for j in indices[i:i + 3])
                face.material_index = mesh.materialIndex
                face.smooth = True
            except:# face already exists
                continue

        uv_layer0 = bm.loops.layers.uv.new() if (hasUv0) else None
        uv_layer1 = bm.loops.layers.uv.new() if (hasUv1) else None
        uv_layer2 = bm.loops.layers.uv.new() if (hasUv2) else None
        col_layer = bm.loops.layers.color.new() if (hasClr) else None

        for face in bm.faces:
            for loop in face.loops:
                if hasUv0:
                    uv0 = vertices[loop.vert.index].uv0
                    loop[uv_layer0].uv = (uv0[0], uv0[1]) # Flip Y
                if hasUv1:
                    uv1 = vertices[loop.vert.index].uv1
                    loop[uv_layer1].uv = (uv1[0], 1 - uv1[1]) # Flip Y
                if hasUv2:
                    uv2 = vertices[loop.vert.index].uv2
                    loop[uv_layer2].uv = (uv2[0], 1 - uv2[1]) # Flip Y
                if hasClr:
                    loop[col_layer] = vertices[loop.vert.index].clr

        # Assign bmesh to newly created mesh
        nmesh.update()
        bm.to_mesh(nmesh)
        bm.free()# Remove all the mesh data immediately and disable further access

        # Blender has no idea what normals are
        #TODO: Add an option
        # TODO: Custom split normals always look broken, are the values wrong?
        UseCustomNormals = True
        if(UseCustomNormals and hasNrm):
            nmesh.normals_split_custom_set_from_vertices([vertices[i].nrm for i in range(len(vertices))])
        else:
            clnors = array.array('f', [0.0] * (len(nmesh.loops) * 3))
            nmesh.loops.foreach_get("normal", clnors)
            nmesh.normals_split_custom_set(tuple(zip(*(iter(clnors),) * 3)))

        # Link object in scene
        bpy.context.scene.objects.link(obj)

    f.close()

    #TODO: Add an option
    Rotate = True
    if Rotate:
        bpy.ops.object.select_all(action='DESELECT')

        bpy.data.objects[skeleton.name].select = True

        bpy.ops.transform.rotate(value=math.radians(90), constraint_axis=(True, False, False))
        bpy.ops.object.select_all(action='DESELECT')

    return cmb

class Vertex(object):
    def __init__(self):
        self.pos = []
        self.nrm = []
        self.clr = []
        self.uv0 = []
        self.uv1 = []
        self.uv2 = []
