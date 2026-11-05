# Project Genesis — Escudo V015: resultado real, sin aprobación

## Verificación
**GitHub Actions #42000989370** finalizó exitosamente: https://github.com/gburdesedev/genesis-blender-render/actions/runs/42000989370

Blender 4.5.13 LTS, Cycles, 64 samples, 3 vistas reales 1100×1100, JPG públicos verificados byte a byte, .blend y PNG en rama de revisión privada. El resultado sigue **rendered_pending_human_review**.

**Fuentes protegidas:**
- GLB Meshy original jajar: SHA256 `ca4e63a25acf84985d1c66fcef77ffc92abb0212e59f50f84821facd171b28f2`; no se alteró.
- Copia de trabajo fuente hierro V175: `8b67ec62da384fb31ad80dcc35feec7a2f1bff08e03ad80ab3205f53dd6588ba`; shader V153 derivado, original intacto.
- Cuero V020 original aprobado como consumible, sin modificar. Mismo perfil de estudio 4600K / `studio_small_09_2k.hdr` RGBE 32 bits / strength 0.82, softbox ligado solo a hierro 260 W.
- Reverso, aro de cuero, remaches y geometría base conservados de V014.

## Cambio controlado en la chapa
Conservaron los 43 golpes de V014. Se agregaron **3 golpes fuertes junto al perímetro** de la lámina (159°, 292°, 23°) con intensidades y radios no simétricos. Profundidades relativas al radio total: 3.4%, 3.0% y 1.9%. La deformación se atenúa exactamente a cero en la unión con el cuero. Se redujo el bump Voronoi 0.27→0.075, ruido fino 0.16→0.045, y rugosidad multiplicada 0.91–1.10 en lugar de 0.79–1.24.

## JPG públicos auténticos
- [Frente](previews/V015_01_frente_golpes_fuertes.jpg)
- [Tres cuartos](previews/V015_02_tres_cuartos.jpg)
- [Detalle ampliado del borde golpeado](previews/V015_03_detalle_golpes_borde.jpg)

## Evaluación visual preliminar
**Mejora:** desaparece gran parte de los remolinos artificiales de V014 y se ven tres golpes marcados en la chapa, con variaciones grandes de reflexión y volumen. **Pendiente:** los golpes tienen bordes demasiado suaves y redondeados, como hundimientos amplios; para mayor credibilidad podrían requerir zonas de plegado/tensión más abruptas, sin subir otra vez el ruido fino. Continúa la franja lateral clara del modelo original y el aro de cuero demasiado grueso; no se tocaron en V015. No se supera automáticamente el mínimo de 8/10.

**Estado:** V015 NO APROBADA; solicitar evaluación del usuario. No tocar `main`, game demo, ni masters. No exportar GLB para integración hasta revisión.
