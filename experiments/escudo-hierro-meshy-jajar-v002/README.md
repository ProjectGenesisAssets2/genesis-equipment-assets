# Project Genesis — Escudo de hierro V002, prueba artística (NO APROBADO)

**Fuente inalterada:** Meshy jajar, escudo circular básico, 232.273 triángulos / 134.588 vértices en la V001. Descargador canónico `Shuvam-Banerji-Seal/meshy-glb-downloader`; comprobar condiciones de licencia de fuente antes de distribución.

**V001 verificada:** workflow https://github.com/gburdesedev/genesis-blender-render/actions/runs/41837864574, éxito. Renders reales inspeccionados: V078_HammeredIron_TOP resultó demasiado uniforme/oscuro y metalizó las correas traseras; se mantienen imágenes sin aprobación en rama privada.

**V002:** workflow https://github.com/gburdesedev/genesis-blender-render/actions/runs/41840148154. Corrige uso de escala importada (la geometría Meshy estaba muy escalada en espacio local; el material V175 utiliza coordenadas de objeto). Prueba el verdadero material frontal oxidado `V153_FrontOxidation_Only_MatchedBack` de la copia de trabajo aprobada del lingote V175, con shader derivado (`Metallic=0.72`, sin tocar fuente). Conserva partes más elevadas de correas de Meshy por máscara geométrica provisional, con revisión posterior necesaria. Añade softboxes físicamente coherentes manteniendo HDRI Poly Haven 4K HDR/RGBE de 32 bits, Cycles 48 muestras, 1100px.

**Entorno de trabajo:** Los assets privados originales y la escena V175 se abren desde el repositorio privado `gburdesedev/genesis-blender-render`. En esta rama de organización se documenta el experimento sin publicar masters privados.

**Restricciones:** No integrar a `main`, PlayCanvas ni la demo. No considerar aprobadas las vistas hasta que sean inspeccionadas. Investigar reducción de 232k triángulos posteriormente sin pérdida de silueta.

**Nota:** La V002 es un render de evaluación, no un GLB optimizado ni una aprobación automática.