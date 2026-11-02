# Genesis sword — V03 · V175 approved color palette

This version addresses an important distinction: **V02 already used the experimental V175 2K base-color texture**, but its light gray/cool look did not reproduce the darker, warm-oxidized **approved V175** render.

V03 bakes a visual palette adaptation into the sword's **blade-only baseColor** using:
- The user-approved V175 iron appearance (graphite gray and muted brown/oxide).
- Existing 2K Genesis iron base color map.
- Existing `T_Hierro_DetailRGBA_2K.png` masks: R wear, G oxidation, B pitting, A microscratches.

Roughness, metallic, normals, mesh (1,406 source vertices, 2,150 triangles), original UVs and original hilt material are **unchanged from V02**. Blade has 98 triangles.

This is **not** an exact transplantation of the four procedural Blender materials in the approved `PG_Iron_Ingot_V175_CHECKPOINT_APROBADO.blend`. A complete shader bake would require Blender 4.5 with correct UV mapping and comparison under the production lighting.

## Reproduce locally

```bash
python -m pip install numpy pillow opencv-python
python scripts/fab_sword/v175_palette_v03.py \
  --source /secure/Genesis_Sword_Iron_V02_V175_PBR.glb \
  --color /secure/T_Hierro_Color_2K.png \
  --detail /secure/T_Hierro_DetailRGBA_2K.png \
  --preview-texture /local-preview/T_Hoja_V175_Color_V03.png \
  --output /local-preview/Genesis_Sword_Iron_V03_V175_Colores.glb
```

No licensed Fab sword mesh/texture or its derived GLB is committed to this public repository. Review the render before approving this palette. PlayCanvas and Blender shader-parity checks are outstanding.
