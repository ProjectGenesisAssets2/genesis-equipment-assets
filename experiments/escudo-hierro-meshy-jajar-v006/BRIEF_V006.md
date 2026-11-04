# Project Genesis — Escudo de hierro V006 (NO APROBADO)

**Partir de V005**, conservar malla original Meshy jajar, material procedimental de hierro derivado de V175, HDRI 4K HDR/RGBE 32 bits y la iluminación de estudio. No modificar main ni la obra maestra.

## Hallazgos verificados de V005
- GitHub Actions finalizó la V005 y generó frente, tres cuartos y reverso. Renders públicos disponibles en `experiments/escudo-hierro-meshy-jajar-v005/previews/`.
- El aro salió casi blanco y sin lectura de veta; causa: la madera del roble V004 es clara por naturaleza y el mapeado original UV del modelo Meshy es insuficiente para esta adaptación.
- La superficie posterior quedó mayormente de hierro porque el criterio de profundidad Y no separaba sus caras.
- La V005 **NO ESTÁ APROBADA**; sus vistas son referencia comparativa.

## Cambios deliberadamente acotados para V006
1. Misma **madera real del roble del proyecto**: mismos `wood_albedo.jpg`, `wood_normal.png` y `wood_roughness.png` verificados por SHA-256. Cambiar proyección sobre X/Z del escudo para hacer visible la veta, sin sustituir el mapa por color liso.
2. Aplicar una tonalización de roble envejecido por multiplicación de albedo; conservar detalles fotográficos, normales y rugosidad.
3. Reconocer el reverso por normales de superficie positivas en Y, manteniendo agarres separados y el interior frontal en hierro auténtico V175.

## Ejecución y evaluación
Workflow privado para acceso a la copia V175:
https://github.com/gburdesedev/genesis-blender-render/actions/runs/41867662473

Los próximos tres JPGs reales deben publicarse aquí, **solo** si hay render y evidencia de revisión:
`experiments/escudo-hierro-meshy-jajar-v006/previews/`.

**No aprobar automáticamente**. Umbral >=8/10, inspección humana. Queda pendiente bajar los 232.273 triángulos para PlayCanvas solo después de resolver estética.
