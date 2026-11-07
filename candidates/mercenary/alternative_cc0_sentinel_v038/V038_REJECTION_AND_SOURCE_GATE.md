# Project Genesis — V038 alternate mercenary verification (REJECTED)

Source published as **T1 Sentinel**, under CC0 on https://www.autosprite.io/free-3d-models/t1-sentinel .

Actual file downloaded and examined in GitHub Actions run https://github.com/ProjectGenesisAssets2/genesis-equipment-assets/actions/runs/42387218995 . This is **not** an approved asset.

## Actual verified facts
- GLB file size: 24,319,564 bytes (publisher described 23.2 MiB).
- 1 skin, **22 bones**, **zero individually rigged finger bones**.
- 1 source glTF mesh, one texture, seven animations: death, hit_chest, idle, sword_attack, sword_block, sword_idle, walk_loop.
- No named sword or shield meshes, no separately detachable weapon/shield nodes. The source does **not** meet the Project Genesis requirement that the mercenary equip the actual V12B sword and V015 shield from inventory.
- Real Blender 4.5.13 LTS Cycles renders with the same Poly Haven 4K EXR HDRI (96-bit RGB / 32 bits per channel) show a fantasy-styled character with empty, open hands; no visible held sword/shield.
- Publisher claim of a heavy sword-and-shield sentinel was **not supported by the exported source GLB**.
- The realistic medieval style, properly closed right fist, dynamic equipment, and full five explorer actions were **not demonstrated**.

## Decision
REJECT V038. Do not spend further time patching or retargeting this GLB. Do not integrate into main. Keep the earlier mercenary V029-V035 files and the original game untouched.

## Next source selection gate
Reject replacement assets on metadata **before** investing in Blender if:
1. No separately replaceable sword and shield (inventory equipment is mandatory)
2. Cannot verify anatomical right weapon and left shield sockets
3. Hands do not reliably grasp objects in actual native idle/walk animation
4. No usable animation for walking, or no legal use rights
5. Does not visually fit the realistic medieval Project Genesis direction

An external non-free candidate to verify if explicitly acquired by the user is Emerald Warden, published at https://literock-studios.itch.io/emerald-warden . The publisher claims sockets `weapon_R` and `shield_L`, separate meshes, Mixamo rig, 15k triangles and 46 clips. **These are publisher claims, not independently verified files.** Do not purchase or retrieve restricted files without the user's authorization and account access.
