# Mercenario explorador — control V037 (7 noviembre 2026)

**No aprobado.** Rama experimental solamente. No tocar `main`, la versión pública, el rig ni los masters V12B/V175 o escudo V015.

## Objetivo canónico
El mercenario solo requiere caminar, reposo, inspeccionar espada, inspeccionar escudo, caminar equipado y equipar/desequipar ambos objetos del inventario. **No existen combates visibles**, ataques ni bloqueos de pelea.

## Evidencia real
- Blender Foundation 4.5.13 LTS, Cycles, 32-bit EXR Poly Haven, espada original V12B con hierro V175 recuperada temporalmente, escudo original V015.
- Acción verificada: https://github.com/ProjectGenesisAssets2/genesis-equipment-assets/actions/runs/42386773133 (success).
- Artefacto con 6 renders reales y 2 GLB experimentales: https://github.com/ProjectGenesisAssets2/genesis-equipment-assets/actions/runs/42386773133/artifacts/13580051556 .
- Render de revisión `candidates/mercenary/arc_fingers_v037/V037_REAL_ARC_FINGER_COMPARISON.jpg`.
- Dos mallas reales A/B parten del GLB V029, evitando heredar V031/V035 donde detectamos 56–67 triángulos con normales/orientación invertidas en la zona de la mano.
- `V037_ARC_FINGERS_{A,B}`: deformación de dedos de mano anatómica derecha por arco continuo, no proyectar con seno aislado. **0 triángulos invertidos**, 0 colapsados y 0 expandidos más de 5x según QA.
- Se mantienen 24 bones; `RightHand` + `GENESIS_SOCKET_WEAPON_R` espada, `LeftHand` + `GENESIS_SOCKET_SHIELD_L` escudo. No invertir nombres ni espejar. Los dedos carecen de rig propio.

## Evaluación visual
Mejora geométrica auténtica y evita las superficies volteadas, pero el guante todavía no envuelve la empuñadura. Los cinco clips siguen siendo los originales V029; esta prueba **no demuestra una animación natural aprobada ni funciona aún en PlayCanvas**.

**Candidato A y B: NO APROBADOS. Nota visual del conjunto permanece por debajo de 8/10.**

## Siguiente corrección (V038 o posterior)
1. No insistir con traslaciones de mango X/Z: la V034/V035 ya aisló una posición cercana.
2. Diseñar o reconstruir **un puño cerrado anatómico con pulgar oponible** sobre la propia mano derecha del mercenario, conservando la identidad, PBR y estilo medieval realista. Si es necesario, sumar huesos de dedos de forma experimental sin cambiar el resto de los 24 huesos ni los sockets.
3. Verificar en render Cycles 32bit desde **palma, nudillos, dorso, parte inferior** y durante la inspección y caminata equipada; evaluar penetración de dedos en empuñadura.
4. Mantener mano izquierda/escudo intactos. Validar exportación GLB/WebGL y montaje dinámico desde inventario; el juego no muestra lucha.
5. Nunca fusionar con `main` sin evaluación del usuario y mínimo visual 8/10.

Este archivo es una revisión visual y técnica, no evidencia de aprobación final.
