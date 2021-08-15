# OoT3D Importer

A Blender 2.79 plugin for importing models from Ocarina of Time 3D.

## Credits

- @xdanieldzd, for reverse-engineering and documenting the CMB and CSAB formats.
- Twili, for reverse-engineering and documenting the ZAR archive format and various additional research.
- @M-1-RLG, AKA M-1, as his [CMB plugin](https://github.com/M-1-RLG/io_scene_cmb) was used as the base of this importer. He also provided [thorough documentation](https://github.com/M-1-RLG/010-Editor-Templates/tree/master/Grezzo) on each of Grezzo's formats.
- @magcius, AKA Jasper, as their [animated model viewer](https://github.com/magcius/noclip.website/tree/master/src/oot3d) was ported to add CSAB support.

## To-do

- [ ] CMB support
  - [x] Multiple meshes
  - [x] Rigs
  - [x] Materials
  - [x] Textures
  - [ ] Alpha blend modes
- [x] ZAR support
- [ ] CSAB support
  - [x] Parsing files
  - [x] Rotation keyframes
  - [x] Link's animations
  - [ ] Translation keyframes
  - [ ] Keyframe tangents
  - [ ] Visibility animations
- [ ] FACEB support (Link's face animations)
- [ ] Improve latency (especially for Link, his models take ~1 minute to load)
- [ ] CMAB support (animated textures)
- [ ] Bugfixes
  - [ ] Custom split normals cause weird shadows on meshes
  - [ ] Bone orientation is off by 90 degrees
- [ ] Support for other Grezzo games
  - [ ] Majora's Mask
  - [ ] Luigi's Mansion

## Usage guide

- This is meant to be used with Blender 2.79.
- The io_scene_cmb-master directory should be copied into [blender install directory]/2.79/scripts/addons, i.e. [blender install directory]/2.79/scripts/addons/io_scene_cmb-master.
- Two new import options should appear: File > Import > OoT3D (.zar) and File > Import > CtrModelBinary (.cmb).
