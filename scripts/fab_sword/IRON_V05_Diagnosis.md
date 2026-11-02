# V05 · visible V175 iron, preserving PBR reflections

**Finding:** V04 imported correctly with a distinct blade material, but its `baseColor` atlas had been blended with Fab's lighter original. The prior V12 comparison renderer also incorrectly forced `SetRoughness(.21)` on every model, regardless of material.

**Fix:** V05 takes the darker graphite/oxide **V175-derived palette** from V03 and retains V04's metallic/roughness and normal maps. It does **not** change 1,406 source vertices, original UVs, the 98 blade triangles or 2,052 other triangles. The original grip/guard material is untouched.

Run only with appropriately obtained local assets:
```bash
python scripts/fab_sword/restore_v175_palette_v05.py \
 --v03 /local/Genesis_Sword_Iron_V03_V175_Colores.glb \
 --v04 /local/Genesis_Sword_Iron_V04_Reflejos_V175.glb \
 --output /local/Genesis_Sword_Iron_V05_V175_ColorRestored_HDR32.glb
```

In the VTK comparison test, use `property.SetRoughness(1.0)` and `property.SetMetallic(1.0)` **as glTF factors**, allowing the imported metallicRoughness map to supply actual per-texel G roughness and B metallic values. Avoid hardcoding an absolute .21 roughness across different materials.

**Status:** PBR GLB V05 built and side-by-side HDR float32 preview rendered. **Not approved**. This is a palette restoration using a material derived from the V175 approval, **not a true Blender bake of the original four procedural V175 shaders**. The production-quality workflow requires a re-bake/remapping of the actual V175 procedural material to sword UVs followed by PlayCanvas validation. No Fab source or derivative binary is stored in this public GitHub repository.
