# Escudo V014 — revisión de renders reales (no aprobado)

**Resultado técnico:** [GitHub Actions #41987613577](https://github.com/gburdesedev/genesis-blender-render/actions/runs/41987613577) finalizó **success** en Blender 4.5.13 LTS / Cycles / HDRI 32 bit. El reporte V014 guardó cuatro PNG 1100×1100, JPG públicos y el proyecto .blend experimental.

## Evidencia del trabajo geométrico y de materiales
- Malla Meshy origen **sin cambios**: SHA256 `ca4e63a25acf84985d1c66fcef77ffc92abb0212e59f50f84821facd171b28f2`, 232.273 tris.
- Copia trabajo del hierro V175 **sin cambios**: SHA256 `8b67ec62da384fb31ad80dcc35feec7a2f1bff08e03ad80ab3205f53dd6588ba`.
- Chapa física derivada V014: 48 anillos, 120 segmentos, 5.760 caras y **43 impactos elípticos** reproducibles con semilla 140514, atenuación hacia el borde. Relieve de normal Voronoi y ruido fino y variación de rugosidad de la red PBR V175, **solo sobre la cara frontal**, no sobre remaches.
- Cuero caprino V020 aprobado como consumible de inventario, reves, agarres, corona, otras texturas y luces idénticos al experimento V013B. Iluminación base HDRI `studio_small_09_2k.hdr` / 0,82, 4600 K; softbox solo para hierro 260W.
- **Nota de trazabilidad:** algunos campos heredados del informe V013 declaran `geometry_unchanged`, pero se refieren al seguimiento de versiones previas: **en V014 la geometría de la chapa sí se modifica**. Fuente Meshy y corona no.

## Cuatro JPG públicos, verificados por SHA
- [Frente martillado](previews/V014_01_frente_chapa_martillada.jpg)
- [Tres cuartos](previews/V014_02_tres_cuartos.jpg)
- [Acercamiento real](previews/V014_03_detalle_frontal.jpg)
- [Reverso de control](previews/V014_04_reverso_control.jpg)

## Control de calidad visual
**Logro:** ya no parece un disco liso; la luz recorre la chapa y la geometría presenta abolladuras auténticas. **Problema:** las micro-normal maps son exageradas y forman círculos y líneas repetidas, parecidas a huellas dactilares, en vez de impactos de martillo convincentes. La piel del cuero sigue relativamente gruesa y se conserva la franja lateral clara de la fuente Meshy; no fue objeto de la V014. El reverso queda igual a V013B.

**Decisión:** V014 **no aprobada**, no cumple todavía 8/10. El usuario debe evaluar la fuerza del relieve. La próxima prueba, si se autoriza, debería reducir bump repetitivo manteniendo las abolladuras físicas y el V175. No modificar main, masters ni demo. No se generó ningún concepto 2D; todas las imágenes son renders del modelo 3D real.
