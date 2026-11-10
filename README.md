# 3D creations

3D character models made with Tripo Studio and refined in Blender, plus a small web viewer.

**Doll Garden:** https://wolfxxx.github.io/3dcreations/ shows the doll in a dusk garden. You can orbit the camera and switch between its four animations.

## Contents

- `docs/`: the Doll Garden page (three.js) and `doll.glb`, served by GitHub Pages.
- `final/boy1`, `final/boy2`: finished models (`model.glb`), preview renders, and review notes.
- `demon_rigged/`: the fantasy demon with fixed head weights, so the face no longer deforms when walking or running.
  - `fix_head_weights.py`: the Blender script that fixes the weights.
  - `patch_weights_into_tripo_glb.py`: copies the fixed weights into a Tripo export.
- `tools/`: Blender and Python scripts used to build, refine, and review the boy models.
- `fantasy demon 3d model.glb`: the original demon model.

Model files (`*.glb`) are stored with Git LFS, except `docs/doll.glb`, which Pages has to serve directly. Run `git lfs install` before cloning.

The `.blend` sources, the intermediate attempts, and the reference photos are not in this repository.
