# Genesis iron sword — V02 experiment (maps derived from V175)

The original Fab sword geometry is retained. Only the **blade's PBR material** is switched to the 2K iron maps from the user's existing `Genesis_Demo_Kit_Materiales_UE5_2K.zip` kit. This is a **visual trial**, **not** a direct bake of the full procedural shader inside `PG_Iron_Ingot_V175_CHECKPOINT_APROBADO.blend`.

Inputs (local only):
- `Genesis_Sword_Iron_V01.glb` (two glTF primitives, blade 98 triangles).
- `Texturas/Basicos/T_Hierro_Color_2K.png`
- `Texturas/Basicos/T_Hierro_Normal_2K.png`
- `Texturas/Basicos/T_Hierro_ORM_2K.png`

```bash
python scripts/fab_sword/apply_v175_material_v02.py \
 --input /secure/Genesis_Sword_Iron_V01.glb \
 --textures /secure/Genesis_Demo_Materiales/Texturas/Basicos \
 --output /local-preview/Genesis_Sword_Iron_V02_V175_PBR.glb
```

Notes:
- **UV / mesh unchanged**, same 1,406 source vertices and 2,150 triangles.
- The guard and grip use the original sword material.
- The V175-derived texture set uses glTF PBR standard: ORM green = roughness, blue = metallic, red = occlusion (optional).
- The kit's `T_Hierro_DetailRGBA_2K.png` remains unused because it requires an extra shader or an explicit bake.
- Expected GLB test size approximately 18.8 MB: optimize **after** reviewing the look.
- Do not publish the source Fab GLB or source-texture files as standalone distributables into the public repository. Keep these files local.
- Review in PlayCanvas or Blender for normal-map contribution: the lightweight offline comparison renderer does not fully implement glTF normal-map lighting.
