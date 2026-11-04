# PROJECT GENESIS · ESCUDO DE HIERRO V005
## Brief de producción — Herrero principiante

**Estado:** CANDIDATO EXPERIMENTAL. No aprobado ni integrado.

### Identidad y silueta
Reutilizar sin remodelar desde cero el escudo circular sencillo de **jajar** (Meshy, modelo `019871b7-fdc5-7cc4-9e12-5d8335ffa187`). Su apariencia debe ser de una **primera fabricación medieval funcional, humilde, sin ornamentos ni estética stylized**. Conservar el original y toda la historia V001–V004.

### Materiales obligatorios
- **Frente principal:** hierro forjado derivado de nuestra copia de trabajo del lingote **V175**, empleando su red de material oxidado V153. Prohibido simular hierro con un color gris plano.
- **Aro y canto visible:** **roble seco del proyecto** (rama pública `ProjectgenesisAssets/genesis-workshop-assets:asset/tutorial-roble_seco`, carpeta `production/tutorial_materials/generated/roble_seco/source/`). Reutilizar sus mapas CC0 `wood_albedo.jpg`, `wood_normal.png`, `wood_roughness.png`. No reemplazar por textura genérica.
- **Reverso:** roble como estructura portante, conservar agarres de material no metálico siempre que la segmentación del Meshy permita identificarlo.
- **Remaches:** metal trabajado, sin brillo ornamental.
- Si el roble no resulta convincente, evaluar el **fresno del proyecto** en una versión separada; no sustituir silenciosamente.

### Correcciones aprendidas
- V001: metal oscuro y plano; todo el escudo metalizado.
- V002: metal demasiado plateado (+1.1 EV), mejor oxidación, pero agarres mal segmentados.
- V003: exposición +0.15 y -0.25 EV, todavía plateado.
- V004: exposición -1.30 EV, **aspecto carbonizado**; descartado artísticamente, valoración anterior 7,5/10 retirada.
- V005: una corrección conjunta acordada: hierro frontal bien expuesto y aro/reverso de roble auténtico. Separar por superficies sin reconstruir la silueta; priorizar su lectura visual.

### Técnica
Blender **4.5.13 LTS** ejecutado con GitHub Actions, **Cycles**, sombreado PBR, HDRI real **4K HDR/RGBE 32-bit** de Poly Haven. Render de **frente, tres cuartos y reverso** de 1100×1100; producir JPG de revisión pública directamente accesible. Proteger el material maestro V175 (revisión privada de materiales; solamente imágenes públicas). Mantener parámetros HDRI constantes durante comparaciones.

### Criterios de salida
- Validar source GLB contra hash `ca4e63a25acf84985d1c66fcef77ffc92abb0212e59f50f84821facd171b28f2`; comprobar imágenes e informe.
- Comprobar material roble concreto y mapas PBR cargados sin faltantes. Identificar material del hierro por nombre y origen V175. Documentar la segmentación y la cantidad de triángulos.
- **No usar ni modificar main**, ni integración a PlayCanvas, ni aprobación automática.
- Meta visual >=8/10 tras revisión del usuario. Separación correcta de hierro/roble/reverso antes de optimizar GLB para WebGL.

### Repositorios
- Seguimiento y JPG público: `ProjectGenesisAssets2/genesis-equipment-assets`, rama `experiment/escudo-meshy-jajar-v005`.
- Excepción para renderizar con **copia privada V175**: `gburdesedev/genesis-blender-render`, rama `experiment/escudo-meshy-jajar-v005`. Una vez exista material autorizado para distribución, trasladar ejecución completa a runner público de la organización.

**Nota de licencia:** el descargador MIT no convierte la licencia del modelo Meshy en MIT/CC0. Verificar los términos del modelo antes de integrar y redistribuir el GLB.
