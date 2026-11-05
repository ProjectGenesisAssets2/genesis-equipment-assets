# Escudo de hierro V010 — cuero V020 aprobado sobre el aro (candidato, NO aprobado)

- **Modelo base:** Project Genesis escudo jajar V009; conserva la geometría original, la lámina frontal corregida de hierro V175 y los remaches.
- **Material recuperado de verdad:** cuero caprino V020 aprobado para consumible de inventario, SHA-256 GLB fuente `5aaeb196738d9b70cbce32102aad9ef4562b4da88550e08a2aea03ca061dca37`, registrado en `asset/tanned-goatskin:evaluation/tanned-goatskin/V020_OWNER_APPROVED.json`.
- **PBR extraído directamente del GLB V020:** mapa baseColor 1536×1536; textura de rugosidad extraída del canal G; mapa normal original. Trabajo público de origen: `ProjectgenesisAssets/genesis-workshop-assets`, rama `experiment/escudo-cuero-v010-source-v020`, carpeta `production/shield_v010/approved_goatskin_v020/`. Workflow de recuperación verificado como exitoso: [41940961092](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/41940961092).
- **V010A:** PBR caprino V020 original sobre el aro, sin alteraciones de acabado.
- **V010B:** mismo PBR V020 con leve oscurecimiento y multiplicador de rugosidad 0,82; no aprobado, test de acabado más satinado.
- **Mismo resto:** hierro frontal V175, geometría V009, contracara de madera y agarres, HDRI 32 bits, Blender 4.5.13 LTS, Cycles.
- **Render:** frente, tres cuartos y dorso A/B, 6 JPG para revisar en esta rama pública. Los originales privados (V175, .blend, GLB Meshy) no se distribuyen.
- **Criterio:** >=8/10 tras evaluación humana. No modificar `main`, no integrar al juego, no atribuir a B la aprobación de caprino V020.
- **Workflow de render:** [V010 A/B](https://github.com/gburdesedev/genesis-blender-render/actions/workflows/escudo-cuero-v010.yml), rama experimental privada, solo por dependencia con copia V175.
