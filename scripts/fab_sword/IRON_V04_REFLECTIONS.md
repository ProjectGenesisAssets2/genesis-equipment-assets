# Project Genesis sword: achieve reflective iron without changing its mesh

## What was actually measured on GLB texture samples

| Blade | Median/average roughness | Metalness |
| --- | ---: | ---: |
| Fab original | ~0.21 | ~1.00 |
| Genesis V03 V175 texture | ~0.69 | ~0.84 |
| Genesis V04 candidate | **0.344** | **0.973** |

V04 is an A/B **material candidate**, not an approved asset. The unchanged geometry contains **2,150 triangles**, with **98 blade** and 2,052 non-blade triangles. The original normals, tangents, UVs, vertex positions and original grip+guard material were retained.

The local export `Genesis_Sword_Iron_V04_Reflejos_V175.glb` was generated from the user's licensed Fab file and Genesis V03, using a mix of original blade PBR and V175 color+surface detail. Original GLB SHA-256 begins `493b3b9080b3b209`.

The model binaries are NOT included in this public repository. Keep the originals and derivatives in the authorized project environment rather than distributing standalone copies.

## Reflections: what Fab shows and why our previews looked flat

A real metal reflects its world. It will appear flat or black in an under-lit scene with no prefiltered environment map. A visually successful PBR inspection needs:

1. **HDRI environment** (interior / forge with bright windows or a suitable outdoor sky), prefiltered for Image-Based Lighting.
2. Correct linear/sRGB texture interpretation: baseColor sRGB; normal + metallicRoughness linear.
3. Metallic near 1 on exposed iron, and **roughness around 0.3–0.4** as a *test*, using the map's spatial variation. In glTF: roughness = G, metalness = B.
4. One broad highlight source, softer fill, controlled exposure/tonemapping. Rotate HDRI or sword to see if specular reflections move across the blade. Do not use emissive to fake shine.
5. Retain original bevels/normals and consider additional near-edge microdetail only after the HDR lighting test. Don't change equipment silhouettes by rarity.

PlayCanvas' StandardMaterial uses **Glossiness** rather than Roughness in some interfaces. If importing a hand-authored roughness map into an Editor material, invert it. A correctly loaded GLB handles the glTF mapping for you; do not invert it twice.

### Non-destructive runtime diagnostic

```js
// After loading sword entity and setting an HDR prefiltered scene envAtlas:
const audit = window.GenesisSwordV04.enhanceSword(app, swordEntity);
console.log('Sword PBR / HDR audit:', audit);
// The helper only adjusts the named blade material and clones it.
// It leaves the grip / guard and other world materials untouched.
```

File: `scripts/fab_sword/playcanvas_reflections_v04.js`.

PlayCanvas docs:
- https://developer.playcanvas.com/user-manual/graphics/physical-rendering/environment-lighting/
- https://developer.playcanvas.com/user-manual/graphics/physical-rendering/physical-materials/

## Approval criteria
- Side-by-side same-camera: original Fab GLB, V03, V04.
- Inspect in real PlayCanvas HDRI-lit world and workshop (different environments).
- Blade shows moving environment reflections while retaining V175 forging detail.
- No blown-out edges, flat gray blade, or lacquer-like clear coat.
- Track load size, texture memory, FPS. Optimize 2K textures AFTER lookdev signoff.
