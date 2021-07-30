import sys, io, os, os.path, array, bpy, bmesh, operator, math, mathutils

from .common import CLIP_START, CLIP_END, GLOBAL_SCALE
from .csab import csab_file
from .import_cmb import LoadModelFromStream
from .import_csab import CsabImporter
from .zar import Zar

#TODO: Clean up
def load_zar( operator, context ):
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
        filePath = operator.directory + f[1].name

        zar = Zar(filePath)

        # Parse model
        cmbList = zar.getFiles("cmb")

        cmbBytesList = []
        if cmbList and len(cmbList) > 0:
            for cmb in cmbList:
                cmbBytesList.append(cmb.bytes)
        else:
            # TODO: Is this robust enough?
            # If no models exist, this might be a scene? Scene models are in a
            # separate file, try to look for that.
            realFilePath = filePath.replace(".zar", "_0_info.zsi")
            if os.path.isfile(realFilePath):
                with open(realFilePath, "rb") as f:
                    cmbBytesList.append(f.read())

        for cmbBytes in cmbBytesList:
            cmbStream = io.BytesIO(cmbBytes)
            LoadModelFromStream(cmbStream)

        # Parse animations
        csabList = zar.getFiles("csab")

        if csabList:
            for i, csab in enumerate(csabList):
                parsedCsab = csab_file.parse(csab.bytes)
                CsabImporter(
                    parsedCsab,
                    csab.filename
                ).import_anims(
                    i == 0 # Clear armatures
                )

        return {"FINISHED"}
