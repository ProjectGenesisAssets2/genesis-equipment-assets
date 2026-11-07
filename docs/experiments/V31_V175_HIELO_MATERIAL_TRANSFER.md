# V31 — Transferencia del material HIELO V175 al filo (experimento)

Fuente maestra identificada en la Biblioteca de Project Genesis:
`/Project Genesis/Art/01_Assets_Work/Iron_Ingot/Genesis_V175_MaterialMaster_4_Afinidades_EXPERIMENTAL.blend` (2,779,174 bytes).
Referencia visual: `Lingote_Afinidad_HIELO_Blender_FINAL.png`.

## Contrato de prueba
- Espada V03 y preset hierro V175/V12B intactos.
- Material existente `M_Ingot_Universal_Affinity_HIELO`, sin recrear shader a partir de una imagen.
- Zona inicial: 35–40 % de una sección de la hoja, sin cubrir el nervio central.
- Intensidad animable de 0 a 100 mediante máscara de mezcla; no crear cristales geométricos de V28–V30.
- Blender 4.5.13 LTS, Cycles, HDRI EXR 32-bit, render frontal y detalle.
- No modificar main ni integrar sin revisión visual >= 8/10.

## Bloqueo verificable
El archivo fuente binario está recuperado en el entorno de trabajo, pero no está en este repositorio. La conexión GitHub disponible permite crear archivos UTF-8, no subir el .blend binario. Git por terminal no resuelve github.com. **No afirmar que se ejecutó un render hasta que GitHub Actions registre una ejecución y produzca imágenes.**

## Próximo paso
Transferir el archivo .blend original a esta rama experimental y ejecutar un workflow que abra el archivo maestro y enlace el grupo de material HIELO a la hoja V03. Rechazar cualquier resultado que no use el material original.
