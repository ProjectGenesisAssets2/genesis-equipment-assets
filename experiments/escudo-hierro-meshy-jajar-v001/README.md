# Escudo de hierro — experimento Meshy jajar V001 (NO APROBADO)

**Contexto:** Escudo sencillo para las primeras fabricaciones del Herrero en Project Genesis. Conservar la silueta original; apariencia de hierro rústico, sin decoración sofisticada ni estilo stylized.

**Origen:** https://www.meshy.ai/3d-models/v2-019871b7-fdc5-7cc4-9e12-5d8335ffa187

**Descargador de referencia:** https://github.com/Shuvam-Banerji-Seal/meshy-glb-downloader ; uso de modelos públicos con licencia válida y respeto de condiciones aplicables.

**Procesamiento seguro:** Los renders se ejecutan en el repo privado `gburdesedev/genesis-blender-render`, rama `experiment/escudo-meshy-jajar-v001`, porque allí se conserva una COPIA DE TRABAJO del material V175. Nunca exponer el master aprobado en este repositorio público.

**Revisión:** https://github.com/gburdesedev/genesis-blender-render/actions/runs/41837864574

**Condiciones técnicas:**
- Blender 4.5.13 LTS en GitHub Actions, Cycles
- HDRI 4K HDR/RGBE de alto rango dinámico (no JPG/PNG de entorno)
- Tres vistas para comparar fuente, hierro y reverso
- Material de hierro derivado de escena V175, verificar asignación real
- La fuente Meshy contiene una ranura de material; confirmar que las correas no reciban metal accidentalmente
- No integrar a `main`, ni publicación al juego, ni aprobación automática
- Revisión humana visual >=8/10

**Estado al abrir rama:** la primera ejecución produjo 3 renders, pero el push a la rama privada falló por conflicto no-fast-forward. Segunda ejecución creada para corregir ese conflicto. Las imágenes aún no se validaron visualmente.
