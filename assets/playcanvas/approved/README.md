# Assets aprobados — Project Genesis / PlayCanvas

Esta carpeta es el **punto de entrada canónico** para los assets aceptados del vertical slice web. El catálogo `catalog.json` identifica la versión aprobada y su ubicación real, incluso cuando algún recurso ya existe en una ruta histórica del proyecto.

## Reglas de publicación

1. **Solo PlayCanvas/WebGL.** No incorporar archivos del pipeline de Unreal Engine.
2. **Aprobación explícita.** Un candidato, una prueba visual o una versión con correcciones pendientes no se convierte automáticamente en asset aprobado.
3. **Una sola copia de cada entregable.** Reutilizar rutas del catálogo y evitar ZIPs, escenas .blend, checkpoints intermedios y duplicados dentro de la aplicación.
4. **Fuente original intacta.** Los másteres aprobados permanecen en sus respaldos de producción; aquí van únicamente sus derivados ligeros que hayan sido revisados.
5. **Optimización y transparencia reales.** Para la web se prefieren GLB optimizados y miniaturas PNG/WebP con canal alfa auténtico; los renders de fondo opaco no cuentan como miniaturas listas.
6. **Trazabilidad.** Registrar profesión, versión, aprobación, origen, formato, peso y rutas de cada variante.
7. **Sin rupturas de referencias.** No mover las 39 capas V002 ni otros archivos ya usados por el menú sin actualizar y verificar primero todas las rutas.

## Organización prevista

Las subcarpetas se crean **solo cuando haya assets realmente aprobados para colocarlos**, sin llenar Git de directorios vacíos:

- `materials/<material>/<version>/`: modelos 3D y miniaturas de minerales, lingotes y materiales.
- `props/<objeto>/<version>/`: herramientas, puertas, fragua, fuelle, armas, etc.
- `animations/<objeto>/<version>/`: animaciones optimizadas que requiera el juego.
- `ui/<pantalla>/<version>/`: paquetes de interfaz aprobados.

Un asset podrá tener `model.glb`, `thumbnail.webp` y/o `poster.png`, según lo requiera. Los nombres y variantes reales se registrarán en `catalog.json`.

## Estado inicial (24-10-2026)

- **Preparación V002 — 39 capas:** composición visual aprobada; ya están en `assets/ui/preparacion/01_Capas/` y se referencian sin duplicarlas.
- **Lingote de hierro V175:** máster visual aprobado. Su render PNG existente incluye fondo gris opaco; faltan GLB optimizado y miniatura transparente para considerarlo listo para web.
- **Minerales V008:** candidatos a evaluación; **no** se admiten en el conjunto aprobado todavía.
- **Otros assets:** se incorporarán uno a uno tras revisar su versión, estado de aprobación y paquete de salida real.

Para los slots 3D de Preparación, el comportamiento acordado es oscilar suavemente entre −45° y +45° durante hover y regresar a 0° al perderlo; el marco y contador quedan inmóviles.

Este catálogo no certifica por sí solo el rendimiento o el aspecto en PlayCanvas: la admisión y las pruebas se hacen por asset.
