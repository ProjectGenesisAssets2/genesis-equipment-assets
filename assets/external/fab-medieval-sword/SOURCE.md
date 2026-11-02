# Project Genesis — Fab medieval sword (iron sword candidate)

- **Original author:** Joan Lahoz
- **Fab listing:** https://www.fab.com/listings/3ac3603a-f91b-413b-82b3-341d91cfaba3
- **Source filename:** `free_medieval_sword.glb`
- **SHA-256:** `493b3b9080b3b209de66186e0265c3b68d2fcfdbfe7c8b214425e197b3086b32`
- **Original file size:** 6,679,212 bytes
- **Original format:** GLB 2.0, `fab-model-conversion`.

## Licensing / distribution

This public repository intentionally **does not contain the source GLB, embedded textures, or a repackaged derivative**. The listing's precise grant has not yet been verified; Fab's Standard License prohibits standalone redistribution of asset source files. Retain the original only in an appropriately access-controlled location until rights for public source distribution are explicitly established. No public Actions artifact should contain the source mesh or textures.

## Initial inspection

- One glTF mesh, one material, four scene nodes.
- 1,406 exported vertices; 2,150 triangles; 24 disconnected components.
- Three packed PBR textures: base color (JPEG), metallic/roughness (PNG), normal (PNG), all 2048x2048.
- Bounding-box extents (original units): `X 0.688974`, `Y 2.0`, `Z 0.122774`.
- Blade extends towards positive Y; pommel is near Y = -1; guard near Y = -0.45.
- The blade must preserve its mesh silhouette. All Genesis rarities share one fixed sword model: no rarity-specific embellishments.

## Next production stage

Use `scripts/fab_sword/blender_inspect.py` to identify blade faces/components in Blender 4.5.13 and produce a JSON report. Do not modify the original GLB in-place. The future iron-material pass will alter only the blade's PBR shading (color, metallic/roughness, and possibly normal map), while preserving geometry and hilt appearance unless specifically approved.

Local analysis command (requires your own licensed source):

```bash
blender -b --factory-startup --python scripts/fab_sword/blender_inspect.py -- --input /path/to/free_medieval_sword.glb --report /path/to/sword_audit.json
```
