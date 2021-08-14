# OoT3D Importer

A Blender 2.79 plugin for importing models from Ocarina of Time 3D.

## Credits

- @xdanieldzd, for reverse-engineering and documenting the CMB and CSAB formats.
- Twili, for reverse-engineering and documenting the ZAR archive format and various additional research.
- @M-1-RLG, AKA M-1, as his [CMB plugin](https://github.com/M-1-RLG/io_scene_cmb) was used as the base of this importer.
- @magcius, AKA Jasper, as their [animated model viewer](https://github.com/magcius/noclip.website/tree/master/src/oot3d) was ported to add CSAB support.

## Features

- [ ] CMB support
  - [x] Multiple meshes
  - [x] Rigs
  - [x] Materials
  - [x] Textures
  - [ ] Alpha blend modes
- [x] ZAR support
- [ ] CSAB support
  - [x] parsing files
  - [x] rotation keyframes
  - [x] Link's animations
  - [ ] translation keyframes
  - [ ] keyframe tangents
- [ ] Improve latency
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
