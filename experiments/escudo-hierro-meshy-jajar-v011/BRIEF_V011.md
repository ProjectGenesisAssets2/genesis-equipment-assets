# Escudo hierro+cuero V011 · corrección controlada de exposición
**Estado:** candidato experimental NO aprobado. Fuente de trabajo V010A.

La valoración del usuario es que el hierro V175 y el cuero caprino V020 ya se sienten correctos, pero **el conjunto está sobreexpuesto** y el reverso está quemado. Por lo tanto no se cambian geometría, caras, texturas, normal maps, rugosidad ni HDRI.

## Únicas diferencias con V010A
- AgX exposure: **-0,85 EV → -1,15 EV**.
- Rear broad fill: **600 → 250**; misma posición, tamaño, color y cámara.
- Front metal sweep: **780 sin cambios**.
- HDRI **Poly Haven studio_small_08_4k.hdr** RGBE HDR/32-bit sin cambios, strength 1,15.
- No se modifica material de hierro V175 ni cuero caprino V020 de V010A.
- Tres renders reales: frontal, tres cuartos, reverso; JPG públicos y .blend/GLB privados.

**Rama de producción protegida:** `gburdesedev/genesis-blender-render:experiment/escudo-meshy-jajar-v011`. Control de originales por SHA256.
**Vistas públicas de evaluación:** `experiments/escudo-hierro-meshy-jajar-v011/previews/` una vez verificadas.
**Estado de aprobación:** ninguno. No publicar al juego ni modificar `main`.
