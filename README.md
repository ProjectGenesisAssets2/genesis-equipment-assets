# Project Genesis — Equipment and Materials (PlayCanvas/WebGL)

Temporary **public** Blender-on-GitHub-Actions workspace for equipment, ingots, ores and material previews. Canonical approved master meshes and proprietary files remain in the **private** project.

## Current production jobs

| Asset | Source generator | Workflow | Status |
| --- | --- | --- | --- |
| Modular neutral sword V008 | `scripts/build_sword_base_hd_v008.py` | `build-sword-base-hd-v008.yml` | **Infrastructure diagnostic only; not an approved replacement** |
| Sword V023 with pommel correction | Not copied (depends on protected V023 Blender master) | Not launched here yet | Original approved baseline preserved privately; evaluate secure input handoff |
| Iron ingot V175 | Not copied (approved private master) | Not launched here yet | Approved source preserved privately |
| Ore 55k triangles, PBR 1536 | Not copied | Not launched here yet | Approved source preserved privately |

## Operational rules

- Use official Blender **4.5.13 LTS** via Actions; no local Blender execution.
- User-approved models never get superseded by older diagnostic results.
- Keep PBR artifacts small, retain workflow artifacts **2 days**, inspect hashes/GLB topology/previews before promotion to private repository.
- No credentials, private masters, or unapproved confidential input in public Git history. Deleting this public repository later cannot erase prior clones or downloads.
