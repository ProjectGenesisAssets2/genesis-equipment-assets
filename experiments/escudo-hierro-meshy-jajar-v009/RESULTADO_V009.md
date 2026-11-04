# Resultado V009 — prueba 3D real (NO APROBADO)

El workflow [GitHub Actions 41924685650](https://github.com/gburdesedev/genesis-blender-render/actions/runs/41924685650) terminó con `success`. Se utilizó Blender 4.5.13 LTS, Cycles, HDRI 4K HDR/RGBE de 32 bits y los mapas PBR del roble del proyecto. La copia privada V175 conserva su SHA-256 esperado. No se modificó el GLB original ni `main`.

**Cambios 3D validados en reporte:** fuente Meshy 232.273 tris preservada; nueva chapa frontal físicamente independiente de 1.680 caras, aro de roble UV independiente de 480 caras y 12 remaches de hierro. Se eliminó la costura radial y la distorsión de estrella en el polo central de V008.

**JPG auténticos del render, públicos y verificados por SHA:**
- [Frente](previews/01_frente_hierro_v175_contorno_roble_v009.jpg)
- [Tres cuartos](previews/02_tres_cuartos_hierro_roble_v009.jpg)
- [Reverso](previews/03_reverso_roble_agarres_v009.jpg)

**Revisión visual:** el defecto geométrico de la chapa frontal desapareció. Aún hay un borde demasiado liso y claro para ser madera de roble envejecida y una pequeña franja superior del modelo original visible desde tres cuartos; no cumple todavía 8/10. La geometría original sigue sin optimizar. Esta versión NO está aprobada para el juego.

**Continuidad:** corregir vetas, rugosidad y borde original sobresaliente como V010 solamente después de evaluación. Nunca presentar conceptos 2D en lugar de los renders del asset 3D.
