bl_info = {
    "name":         "OoT3D Import",
    "author":       "M-1 (Discord: M-1#1972)",
    "blender":      (2, 79, 0),
    "version":      (1,0,0),
    "location":     "File > Import",
    "warning":      "This add-on is an early release and bugs may occur",
    "description":  "Import Grezzo's \"ZAR\", \"Ctr Model Binary\" file(s)",
    "category":     "Import-Export",
    "wiki_url":     "",
    "tracker_url":  "",
}

import os, bpy
from bpy.props import *
from bpy_extras.io_utils import ImportHelper

# ################################################################
# Import/Export
# ################################################################
class ImportCmb(bpy.types.Operator, ImportHelper):
    bl_idname = "import.cmb"
    bl_label = "Import CMB"

    filename_ext = ".cmb"
    filter_glob = StringProperty(default="*.cmb", options={'HIDDEN'})
    files = bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory = bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})


    def execute( self, context ):
        from .import_cmb import load_cmb
        return load_cmb(self, context)


class ImportZar(bpy.types.Operator, ImportHelper):
    bl_idname = "import.zar"
    bl_label = "Import ZAR"

    filename_ext = ".zar"
    filter_glob = StringProperty(default="*.zar", options={'HIDDEN'})
    files = bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory = bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})


    def execute( self, context ):
        from .import_zar import load_zar
        return load_zar(self, context)


# ################################################################
# Common
# ################################################################

def menu_func_import( self, context ):
    self.layout.operator( ImportZar.bl_idname, text="OoT3D (.zar)")
    self.layout.operator( ImportCmb.bl_idname, text="CtrModelBinary (.cmb)")

def register():
    print("Registering ZAR\n")
    bpy.utils.register_class(ImportZar)

    print("Registering CMB\n")
    bpy.utils.register_class(ImportCmb)
    bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
    print("Unregistering ZAR\n")
    bpy.utils.unregister_class(ImportZar)

    print("Unregistering CMB\n")
    bpy.utils.unregister_class(ImportCmb)

    bpy.types.INFO_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
