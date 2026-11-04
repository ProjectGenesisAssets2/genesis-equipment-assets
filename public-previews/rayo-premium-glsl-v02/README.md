# Project Genesis · Rayo premium V02 · PlayCanvas/WebGL2

**Previsualización experimental para PC. No aprobada ni integrada.**

La espada usada es exactamente la V03 original, 2.150 triángulos y mapas PBR V175. Se implementó **Rayo** como un shader GLSL de descargas fractales con emisión y Bloom HDR real (CameraFrame) sobre la hoja, sin primitivas geométricas ni mapas de máscaras.

**[▶ Ver video Rayo V02 (MP4)](https://raw.githubusercontent.com/ProjectGenesisAssets2/genesis-equipment-assets/experiment/v03-rayo-premium-glsl-v02-brightcorona-20261104/public-previews/rayo-premium-glsl-v02/Genesis_Rayo_Premium_PlayCanvas_V002.mp4)**

**[Ver animación Rayo V02 (GIF)](https://raw.githubusercontent.com/ProjectGenesisAssets2/genesis-equipment-assets/experiment/v03-rayo-premium-glsl-v02-brightcorona-20261104/public-previews/rayo-premium-glsl-v02/Genesis_Rayo_Premium_PlayCanvas_V002.gif)**

Duración 2,67 segundos. Resolución 1280×720, 32 fotogramas, intensidad 85/100 (demostración).
Fuente SHA-256: `e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b`.

## Evidencia
- [GitHub Actions: render real PlayCanvas y auditoría](https://github.com/ProjectGenesisAssets2/genesis-equipment-assets/actions/runs/41898363440).
- `audit.json` demuestra WebGL2, 2.150 triángulos, 2 mallas, shader compilado sin errores, Bloom HDR activado.
- Sin geometría alterada ni GLB de origen distribuido.
- Estado: **experimental pendiente de evaluación visual**, sin cambios en main.
