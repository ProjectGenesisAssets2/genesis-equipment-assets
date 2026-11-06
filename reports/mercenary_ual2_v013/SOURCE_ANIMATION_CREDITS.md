# Animation Assets

This folder contains CC0 animation libraries by Quaternius.

## Universal Animation Library 1

- `universal_animation_library_1/UAL1_Standard.glb`: in-place animations.
- `universal_animation_library_1/UAL1_Standard_RM.glb`: root-motion animations.
- `universal_animation_library_1/LICENSE_Quaternius_CC0.txt`: source license.

## Universal Animation Library 2

- `universal_animation_library_2/UAL2_Standard.glb`: in-place animations.
- `universal_animation_library_2/UAL2_Standard_RM.glb`: root-motion animations.
- `universal_animation_library_2/Mannequin_F.glb`: female mannequin reference from the pack.
- `universal_animation_library_2/LICENSE_Quaternius_CC0.txt`: source license.

## Source Files

- `source/`: editable Blender source files extracted from the source packs in
  Downloads. This folder has a `.gdignore` file so Godot does not import it.
- `source/README.md`: explains which files were kept from the source archives
  and which redundant exports were skipped.

Use the non-`_RM` files by default for server-authoritative MMO movement. Root-motion variants are useful for animation previewing or future special-case ability work.

Current player usage:

- `UAL1_Standard.glb`: `Idle`, `Jog_Fwd`, and `Punch_Jab`.
- `UAL2_Standard.glb`: `Shield_OneShot` for the first hand-gathering wood
  prototype.

## Ability Clips

- `abilities/one_handed_sword/sword_and_shield_slash.glb` is the user-provided
  Mixamo `Sword And Shield Slash` motion retargeted onto Elderforge's Quaternius
  humanoid skeleton. Horizontal root travel is removed so gameplay movement
  remains authoritative; vertical motion, the airborne turn, and landing pose
  are preserved for `Whirling Slash` on W.
- `abilities/one_handed_sword/sword_and_shield_attack.glb` is the user-provided
  Mixamo `Sword And Shield Attack` motion used by `Leaping Strike` on E. Its
  3.65-meter forward travel is removed from the clip and applied through the
  collision-aware movement motor, while the overhead jump and landing recovery
  remain on the skeleton. The sword reaches its landing contact at 53%.
- Regenerate it with `tools/animation/retarget_mixamo_to_elderforge.py`. The
  script accepts a Mixamo FBX, target Elderforge rig scene, output path, and
  animation name through Blender's arguments after `--`.
