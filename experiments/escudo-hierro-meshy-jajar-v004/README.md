# Project Genesis — Escudo jajar V004 · ensayo de hierro oscuro (NO APROBADO)

Base conservada: Meshy jajar `019871b7-fdc5-7cc4-9e12-5d8335ffa187`, source SHA-256 `ca4e63a25acf84985d1c66fcef77ffc92abb0212e59f50f84821facd171b28f2`.

Copia de trabajo protegida del lingote V175, SHA-256 `8b67ec62da384fb31ad80dcc35feec7a2f1bff08e03ad80ab3205f53dd6588ba`.

V003 confirmó que +0,15 y −0,25 EV todavía producen demasiado metal plateado, con poca oscuridad de hierro forjado. Experimento V004: **una sola variable**, exposición `−1,30 EV`. Mismo material V153 de oxidación frontal del V175, `Metallic 0,72` derivado, escala aplicada, misma cámara, Cycles y mismo HDRI de Poly Haven 4K HDR/RGBE 32 bits más dos softboxes constantes.

Run: https://github.com/gburdesedev/genesis-blender-render/actions/runs/41843397773

Este repositorio público de la organización documenta las versiones; la prueba exacta V175 se ejecuta en el repo privado para no exponer el material fuente. Sin cambios en `main` ni en juego, y ninguna aprobación automática. La geometría original tiene **232.273 triángulos**, todavía sin optimización para WebGL.

## Resultado verificado V004 — 2026-11-04

GitHub Actions run 41843397773 **success**: Blender 4.5.13 LTS, Cycles 48 samples, HDRI Poly Haven 4K HDR/RGBE 32-bit, imagen 1100×1100. Fuente Meshy, HDRI y copia V175 coinciden con sus SHA-256. El render V004 quedó guardado en la rama privada experimental:

https://github.com/gburdesedev/genesis-blender-render/blob/experiment/escudo-meshy-jajar-v004/review/escudo_hierro_meshy_v004/01_escudo_v004_frente_exposure_neg130.png

Evaluación visual preliminar: **7,5/10** (mejor que V003). El hierro es más oscuro y creíble, con matices de oxidación; todavía se notan las separaciones de tablones de la geometría Meshy original. **NO APROBADO**. Falta render posterior V004, depurar agarres, retopología/LOD y GLB PlayCanvas, sin tocar la geometría maestra.

GLB original conservado y comprobado: https://github.com/gburdesedev/genesis-blender-render/blob/experiment/escudo-meshy-jajar-v004/source_assets/meshy/jajar_019871b7/escudo_original.glb

**Distribución/licencia:** verificar condición de licencia específica del modelo y términos de Meshy antes de publicar el original en el repositorio público.
