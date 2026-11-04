# Project Genesis — Escudo de hierro Meshy, V003, comparación de exposición (NO APROBADO)

Fuente: https://www.meshy.ai/3d-models/v2-019871b7-fdc5-7cc4-9e12-5d8335ffa187 (autor jajar; verificar licencia y términos antes de integración). Descargador canónico Shuvam-Banerji-Seal/meshy-glb-downloader.

V001: forma sencilla adecuada, material demasiado oscuro y uniformizado.
V002: coordenadas procedurales corregidas aplicando escala original 0.000122265 -> 1.0. Material oxidado V153 de la copia aprobada V175; HDRI real 4K RGBE de Poly Haven. Muestra mejores detalles pero iluminación excesiva (parece metal plateado), resultado provisional 6,5/10. Reverso preservó parte de los agarres mediante máscara provisional. Render original (privado): https://github.com/gburdesedev/genesis-blender-render/actions/runs/41840148154

V003: PRUEBA ACOTADA: únicamente exposición de escena (+0,15 EV vs -0,25 EV). Mantener geometría, material, metallic 0,72, iluminación HDRI y softboxes, tamaño y Cycles 48 muestras iguales a V002. Comprobar en ambas vistas frontales, sin alterar masters. Ejecutado en repo privado por dependencia con copia V175; seguimiento aquí en organización. Run: https://github.com/gburdesedev/genesis-blender-render/actions/runs/41841955958

**Aprobación:** ninguna todavía. El criterio es >=8/10 tras inspección visual. Queda pendiente optimización de 232.273 triángulos, limpieza de agarres y GLB PlayCanvas. No integrar a main.
