bl_info = {
    "name": "Import CMB/CSAB format (The Legend of Zelda: Ocarina of Time/Majora's Mask 3D",
    "author": "BoringPerson (aka boringhexi)",
    "version": (0, 0, 3),
    "blender": (2, 79, 0),
    "location": "File > Import",
    "description": "Import CMB models, CSAB animations",
    #"wiki_url": "https://wiki.cloudmodding.com/oot/3D:Programs", #TODO
    #"tracker_url": "https://github.com/boringhexi/hello-world/issues", #TODO
    "category": "Import-Export",
}


import os.path, traceback

#Allow these addons to be reloaded by pressing F8 in Blender
if "bpy" in locals():
    import importlib
    if "import_cmb" in locals():
        importlib.reload(import_cmb)
    if "import_csab" in locals():
        importlib.reload(import_csab)

import bpy
from bpy.props import (
        StringProperty,
        CollectionProperty
        )
from bpy_extras.io_utils import ImportHelper


class ImportCMB(bpy.types.Operator, ImportHelper):
    """Load CMB model (from Legend of Zelda: Ocarina of Time 3D/Majora's Mask 3D)"""
    bl_idname = "import_scene.cmb"
    bl_label = "Import CMB"
    bl_options = {'UNDO'}

    filter_glob = StringProperty(
            default="*.cmb",
            options={'HIDDEN'}
    )

    def execute(self, context):
        from . import import_cmb
        
        try:
            for file in range(1): #in self.files TODO. see CSAB for how
                import_cmb.read(self.filepath)
        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            self.report({'ERROR'}, str(e))
            self.report({'ERROR'}, "[Details of the error]\n" + tb)
        
        #self.report({'ERROR'}, "Test message.") #XXX pops up a message in the header. If it's an error, it also pops up where the mouse cursor is.
        return {'FINISHED'}
        
        #TODO return {'CANCELLED'} and roll back to before import if there was a show-stopping error
        
        #TODO Want do know what to do next regarding warnings? well...
        #- For stuff like multiple anims per CSAB that aren't supported yet, use self.report()
        #But for unused data (like meshes or textures):
        # All I really need to do is pop up a message saying "[One of these CMB files|This CMB file] contains unused stuff! Check out Blender's console (or info window) for more details."
        #Therefore...
        # For making a custom pop-up message without report(), see https://blender.stackexchange.com/questions/109711/how-to-popup-simple-message-box-from-python-console

class ImportCSAB(bpy.types.Operator, ImportHelper):
    """Load CSAB anim into selected armature (from Legend of Zelda: Ocarina of Time 3D)""" #/Majora's Mask 3D
    bl_idname = "import_anim.csab"
    bl_label = "Import CSAB"
    bl_options = {'UNDO'}
    
    #multiple selected files in the file picker (basenames only)
    files = CollectionProperty(type=bpy.types.PropertyGroup)

    filter_glob = StringProperty(
            default="*.csab",
            options={'HIDDEN'}
    )
    
    def execute(self, context):
        from . import import_csab
        
        ## TODO Multiple anim import not supported yet, since it imports straight to the timeline
        # directory = (os.path.dirname(self.filepath))
        # for file in self.files:
        #     csab_path = (os.path.join(directory, file.name))
        #     import_csab.read(csab_path)
        
        try:
            for file in range(1): #TODO in self.files
                import_csab.read(self.filepath) #TODO eventually it'll be possible to import multiple animation files at once, see the comments above for how
        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            self.report({'ERROR'}, str(e))
            self.report({'ERROR'}, "[Details of the error]\n" + tb)
        
        return {'FINISHED'}

def menu_func_import_cmb(self, context):
    self.layout.operator(ImportCMB.bl_idname, text="Zelda OoT3D/MM3D model (.cmb)")


def menu_func_import_csab(self, context):
    self.layout.operator(ImportCSAB.bl_idname, text="Zelda OoT3D anim (.csab)") #/MM3D


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func_import_cmb)
    bpy.types.INFO_MT_file_import.append(menu_func_import_csab)


def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func_import_cmb)
    bpy.types.INFO_MT_file_import.remove(menu_func_import_csab)
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
