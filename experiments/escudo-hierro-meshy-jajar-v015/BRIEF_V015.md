# Project Genesis — Escudo hierro V015 · Golpes fuertes junto al perímetro

**Base:** V014 real; selección de iluminación **V013B**. Experimento reversible en rama separada. **NO APROBADO**.

## Cambio exclusivamente en la chapa frontal de hierro V175 derivada
- Se preservan los **43 impactos** anteriores en la chapa, sin modificar la fuente del Meshy jajar, el hierro V175 original, el cuero caprino V020, sus mapas PBR ni el reverso.
- Se añaden **tres golpes físicos específicos** cerca del borde interior de la chapa: superior izquierdo (159°, radio 82% de la chapa, profundidad máxima 3,4% del radio total), inferior derecho (292°, 78%, 3,0%) y superior derecho moderado (23°, 86,5%, 1,9%). Los golpes son elípticos, de dimensiones diferentes y con pequeños labios de material desplazado; decrecen suavemente a cero en el borde para conservar la unión con el cuero.
- El microrelieve circular artificial V014 se reduce: intensidad Voronoi **0,27 → 0,075**, ruido fino **0,16 → 0,045**, menor profundidad y rugosidad menos variable (multiplicadores de **0,91 a 1,10** sobre el shader original V175). No se sustituye el hierro por una textura sintética.
- Se conservan **HDRI `studio_small_09_2k.hdr` RGBE 32 bits**, intensidad 0,82, luz principal de 4600 K y refuerzo exclusivo de chapa a 260 W, como V013B. Blender **4.5.13 LTS** y Cycles, 64 muestras.
- Salidas a revisar: frente V015, tres cuartos V015, acercamiento V015 al borde. El reverso no cambia y puede compararse directamente con V014.
- No integrar al juego, no modificar `main`, no aprobar sin valoración del usuario (mínimo 8/10). Al principio únicamente se generan las imágenes reales y la escena privada, sin exportación optimizada WebGL.

**Ejecución real:** [GitHub Actions V015 #42000989370](https://github.com/gburdesedev/genesis-blender-render/actions/runs/42000989370).

**JPG públicos solo después de verificar:** `experiments/escudo-hierro-meshy-jajar-v015/previews/`.
