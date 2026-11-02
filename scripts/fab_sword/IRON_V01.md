# Fab sword — local iron-material experiment

Source: [Joan Lahoz / Fab listing](https://www.fab.com/listings/3ac3603a-f91b-413b-82b3-341d91cfaba3).

This public repository hosts **scripts and metadata only**. The source GLB and derivative binary are not committed to a public repository. Use a local copy of the model you legitimately obtained; keep it outside Git.

```sh
python -m pip install numpy pillow
python scripts/fab_sword/build_iron_v01.py \
  --input "/secure/free_medieval_sword.glb" \
  --output "/local-preview/Genesis_Sword_Iron_V01.glb" \
  --report "/local-preview/Genesis_Sword_Iron_V01.audit.json"
```

The script verifies the exact original file SHA-256; classifies the disconnected blade shells rather than relying on a crude Y threshold; splits two index groups into original hilt and iron blade, with **0 geometry edits**. The hilt retains its original material. Blade retains its diffuse and normal textures, adding roughness minimum ~0.674 and a lightly cooled/darkened tint. In original source there are **1,406 vertices, 2,150 triangles**; blade 98 triangles, other 2,052.

Review under real PlayCanvas lights before approval. Not yet a final approved material. Iron and steel both reflect as metals; the relevant look is darker/rougher iron, not metalness=0.

Build locally, not in public Actions, until an approved non-public binary handoff exists. The output GLB is a derivative; do not publish it as standalone source in this repository.