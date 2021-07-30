import sys, os, array, bpy, bmesh, operator, math, mathutils

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
                area.spaces.active.clip_start = 10.0
                area.spaces.active.clip_end = 100000.0

    bpy.context.scene.render.engine = 'CYCLES'# Idc if you don't like cycles

    for f in enumerate(operator.files):
        filePath = operator.directory + f[1].name
        return {"FINISHED"}
