# Módulos de efectos elementales — Project Genesis

## Rayo — V07 aprobado visualmente
- Módulo: `vfx/approved/Genesis_Rayo_Helicoidal_V07.mjs`
- Aprobación: efecto visual Rayo helicoidal V07, otorgada por el usuario en esta conversación
- Intensity: **0–100**, separado de rareza, estadísticas y modelo base
- Efecto: descarga que recorre la hélice invisible en 3D alrededor de la hoja
- Fuente artística inmutable: `tests/rayo-premium-v01/rayo-premium.js` en la rama experimental V07
- Identidad del GLB original V03: SHA-256 `e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b`
- Comparación técnica: `tests/fire-rayo-v08/check_rayo_approved.py` exige GLSL vertex y fragment sin modificaciones.
- La aprobación visual **no autoriza integrarlo automáticamente a main**.

## Fuego — V01 en pruebas
- Módulo independiente: `vfx/experimental/Genesis_Fuego_Filo_V01.mjs`
- Emissive cálido y vetas móviles sobre ambos filos
- Intensity 0–100, sin alterar la geometría ni material PBR V175
- Candidato todavía **sin aprobación**.

## API compartida (PlayCanvas)
Los dos módulos reciben `(pc, app, bladeAabb)`, devuelven `{material,entity,stats,set}` y cada `set(time, intensity)` opera por separado. Con `set(time, 0)` el efecto desaparece. Son capas VFX adicionales; no sustituyen PBR ni son máscaras horneadas en el GLB.

Las pruebas V08 cargan ambos sobre la misma espada sin copiar el arte original. Las piezas nuevas se mantienen fuera de la demo principal hasta revisión de calidad.
