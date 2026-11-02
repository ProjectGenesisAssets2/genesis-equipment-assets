# Exact V03 input for Cycles rendering

The Actions workflow `.github/workflows/render-fab-sword-cycles-v03.yml` accepts:
- A user-provided exact GLB at `render-input/Genesis_Sword_Iron_V03_V175_Colores.glb`; or
- An access-controlled URL via the repository secret `GENESIS_SWORD_V03_SOURCE_URL`.

**Source SHA-256:** `e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b`.

Pushing the exact GLB on the feature branch triggers Blender 4.5.13 Cycles automatically and uploads only the rendered PNG and JSON audit as artifacts.

**License warning:** This Fab-derived GLB is not cleared for public standalone redistribution. A public Git commit exposes the file permanently in Git history, even if deleted later. Prefer the protected source URL secret route if complying with Fab Standard License.
