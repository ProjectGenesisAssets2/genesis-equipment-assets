# Project Genesis — V030 read-only anatomy audit

**Status: BLOCKED FOR VISUAL APPROVAL.** This is a diagnostic of the existing real Meshy mercenary V029. No character, animation, socket or weapon GLB was modified. No change to `main`.

## Sources verified
- Character: `candidates/mercenary/explorer_v029/mercenary_explorer_v029.glb`, SHA256 `694c5d9de518de6a702e5d0ee2d801e203daffa04807f394437663cae4ef94aa`.
- Right weapon: genuine protected V12B sword with iron V175, used ephemerally by Blender Actions.
- Left shield: original V015 Blender-compatible GLB.
- Render: Blender 4.5.13 LTS, Cycles, Poly Haven EXR 32-bit.
- Analysis workflow: https://github.com/ProjectGenesisAssets2/genesis-equipment-assets/actions/runs/42377958142 (render output successful, overall workflow red only because QA script wrote report as V029, while final assertion expected V030).
- Artifact containing 3 real full-size closeups and `ANATOMY_QA_V030.json`: https://github.com/ProjectGenesisAssets2/genesis-equipment-assets/actions/runs/42377958142/artifacts/13576158471

## Hard handedness mapping: checked, never swap
- `RightHand` node 8, world rest (-0.61895, 1.47877, 0.04203) m; bone is character's anatomical right, world X negative. `GENESIS_SOCKET_WEAPON_R` node 26 is CHILD of node 8.
- `LeftHand` node 4, world rest (+0.60665, 1.48287, 0.04136) m; bone is character's anatomical left, world X positive. `GENESIS_SOCKET_SHIELD_L` node 27 is CHILD of node 4.
- Skin-weighted glove centers: Right (-0.7242,1.46582,0.05980) m, Left (+0.72188,1.46630,0.05858) m. Both proper sides; 519 weighted right-hand vertices, 516 weighted left.
- Existing native socket to glove centroid offsets: right **49.9 mm**, left **59.5 mm** (geometric offsets, not yet certified anatomical grip centers).
- The rig has 24 joints, **zero individually animated finger/thumb joints**.

## Actual render observations
1. Right-hand fingers lie/extend alongside the sword's leather hilt instead of wrapping tightly around it.
2. The front and reverse camera angles show the sword-hilt position/wrist alignment is not an anatomically convincing grip. Simply rotating the socket cannot make the fingers close.
3. Left shield is attached by the correct LEFT socket, but a frontal shield closeup does not prove contact with the inside grip/strap. Require a rear view of the shield and hand contact separately.
4. No attack/block animations are required. Keep the five explorer actions unchanged until hand geometry/attachment is fixed.

## Required V031 repair order
1. Use the actual V029 Meshy hand/glove geometry and real V12B grip as reference, do **not** change RightHand/LeftHand mapping.
2. Fit an anatomical right closed-fist grip: if fingers cannot deform (current rig), a non-destructive, source-preserving hand mesh correction or added finger rig is necessary. Choose based on 3D contact test, not guessed Euler angles.
3. Align sword grip anchor with closed palm and correct thumb/knuckle side; check front, back, and underneath closeups and finger/sword intersection.
4. Verify LEFT shield handle/strap contact from behind; avoid substituting the shield face or mirroring the hand.
5. Only then derive natural shoulder/elbow/wrist inspection and walk-with-equipment movement, preserving original approved assets. Aim >=8/10 after actual Cycles and WebGL QA.
6. Never merge `main` or label approved without user review.

QA scripts in this branch are diagnostic only. PlayCanvas integration still not tested.
