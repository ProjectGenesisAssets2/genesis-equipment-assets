# Project Genesis — Visor universal 3D (ChatGPT / WebGL)

## Contrato de uso aprobado para el proyecto

**GitHub almacena la implementación; GitHub NO es el lugar donde el usuario debe abrir o utilizar el visor.** En las sesiones de revisión, el asistente debe reconstruir e incorporar el visor interactivo **dentro de la respuesta de ChatGPT** y precargar el GLB específico de la evaluación. No se debe pedir al usuario visitar una web, ejecutar HTML, descargar un programa ni seleccionar manualmente un GLB.

## Archivos versionados

- `hdr32-pbr-inspector.html`: visor WebGL2 de estudio con selector de GLB para pruebas técnicas locales. Es una base de desarrollo, **no sustituye el visor incrustado en ChatGPT**.
- `inline-selfcontained.html`: versión independiente sin red de la prueba inicial de espada provisional, con geometría incrustada.
- `inline-widget-template.html`, `sword-payload-gzip.b64`, `sword-payload-meta.json`: demostración de empaquetado de geometría en la respuesta.
- `pack_inline_lod.py`: herramienta para crear datos simplificados desde un GLB original verificado.
- `test-inline.cjs`: prueba de integración en navegador Chromium.
- `test-hdr32.cjs`: ensayo de carga de GLB real. **No afirmar que pasó** si no existe ejecución exitosa.

## Procedimiento por revisión de asset

1. Identificar **versión exacta aprobada** y localizar el archivo GLB auténtico y sus texturas. No reemplazar por renders de otras versiones ni inventar modelos.
2. Inspeccionar GLB real: triángulos, materiales, imágenes, tamaño y hash.
3. Preparar un paquete autocontenido de geometría y materiales para la respuesta; si se requiere reducción LOD, indicar inequívocamente que es vista previa.
4. Crear una instancia **en la conversación** del visor (no un `CodeBlock` ni un enlace) con ese paquete embebido. El usuario no debe hacer cargas ni pasos manuales.
5. Controles: rotación táctil, zoom, frente, perfil y restablecimiento. Reportar **HDR32 activo** solamente si WebGL acepta RGBA32F; diferenciar luces float32 de un HDRI EXR fotográfico auténtico.
6. Pedir aprobación visual, y solo entonces integrar a `main` o marcar el asset aprobado, según la autorización del usuario.

## Limitación de plataforma

El visor HTML guardado en GitHub no se inyecta por sí solo en un chat. Cada respuesta necesita incorporar el componente interactivo y sus datos. No son suficientes links, imágenes o código mostrado. URLs `sandbox:` no funcionan como URLs públicas dentro de `fetch()` del visor. Los blobs GLB/texturas tienen que ser embebidos o alimentados por un canal soportado en la conversación.

## Assets solicitados

- Tronco de Fresno V02: GLB original recuperado, 163 272 triángulos, 2 materiales, 5 imágenes y 14 178 280 bytes. Fuente de producción: artefacto Actions `genesis-fresno-v02-troncos-tablas-blender`, run 41503321995 en `ProjectgenesisAssets/genesis-workshop-assets`.
- Tablas de Fresno V05: **recuperación todavía pendiente de verificar**. No sustituir por las tablas V02/V03.
- Espada V03 con hoja del lingote hierro V175: pendiente de implementación visual real, no confundir con espada provisional V001.

## Garantías

- No editar `main` en una operación de preparación o prueba.
- No afirmar que un visor funcionó en ChatGPT basándose solo en una prueba de Chromium.
- Evitar `atob` sobre cadenas corruptas / usar firmas y validación.
- Evitar llamadas externas al renderizar dentro de ChatGPT; base autocontenida.
