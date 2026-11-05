# Project Genesis · V012, escudo de hierro con cuero caprino · Resultado

**Fecha de verificación:** 2026-11-04/05 UTC. **Estado:** candidato experimental, NO aprobado.

## Ejecución real
- [GitHub Actions 41947923314](https://github.com/gburdesedev/genesis-blender-render/actions/runs/41947923314): finalizó con **success**, incluidos render, 3 JPG y commit privado. Intento anterior 41946743413 renderizó bien pero falló al publicar por nombre incompleto de rama; fue corregido.
- Fuente Meshy jajar GLB idéntica SHA256 `ca4e63a25acf84985d1c66fcef77ffc92abb0212e59f50f84821facd171b28f2`.
- Escena de trabajo de hierro V175 verificada `8b67ec62da384fb31ad80dcc35feec7a2f1bff08e03ad80ab3205f53dd6588ba`.
- Cuero: caprino V020 aprobado como material de inventario, 3 mapas PBR idénticos por SHA. Geometría, mapeado, materiales y cámaras del escudo V011 conservados.

## Perfil recuperado EXACTAMENTE de evaluación/tanned-goatskin/V020_OWNER_APPROVED.json
- Luz principal **4600 K**, Blackbody; ubicación (3, -4, 5), potencia 12, tamaño 4.
- **HDRI 32 bits RGBE** Poly Haven `studio_small_09_2k.hdr`, intensidad de entorno 0,82.
- Color Standard / exposición 0, Cycles 64 samples, sin las luces auxiliares artificiales altas de las versiones previas.

## Renders JPG públicos del asset real
- [Frente V012](previews/V012_01_frente_hierro_cuero.jpg)
- [Tres cuartos V012](previews/V012_02_tres_cuartos_hierro_cuero.jpg)
- [Reverso V012](previews/V012_03_reverso_perfil_4600k.jpg)

## Evaluación visual
**A favor:** el aro de cuero recupera un marrón natural con grano, la madera posterior ya no se ve blanqueada ni quemada.
**En contra:** con el perfil caprino sin luces adicionales, el hierro V175 del frente queda **demasiado oscuro** y pierde reflejos. Persisten geometría del aro gruesa y franja clara lateral del original. El perfil aprobado para material consumible NO asegura equilibrio para el escudo de dos materiales y no equivale a aprobar el escudo.

**Decisión de QA:** no aprobar, no integrar en main ni PlayCanvas. Mantener V010A/V011 y V012 por separado; evaluar posteriormente una iluminación de hierro más focalizada, sin cambiar el cuero y sin quemarlo.
