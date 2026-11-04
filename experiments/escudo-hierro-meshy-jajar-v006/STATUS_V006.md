# Escudo de hierro V006 · verificación visual (04/11/2026)

**Ejecución real finalizada con éxito:** [GitHub Actions V006](https://github.com/gburdesedev/genesis-blender-render/actions/runs/41868278251). Blender 4.5.13 LTS, Cycles, 48 samples, HDRI Poly Haven 4K RGBE de 32 bits, 1100x1100, material V153 derivado de la copia V175 y roble seco PBR real del proyecto.

**Tres vistas JPG públicas de evaluación:**
- [Frente V006](previews/01_frente_hierro_v175_contorno_roble_v006.jpg)
- [Tres cuartos V006](previews/02_tres_cuartos_hierro_roble_v006.jpg)
- [Reverso V006](previews/03_reverso_roble_agarres_v006.jpg)

**Informe real del render privado:** 232.273 triángulos sin optimizar; 62.304 caras con hierro frontal, 98.859 caras con roble en aro, 51.532 caras con roble posterior y 19.578 caras conservando material Meshy en agarres. Los mapas de roble (color, normales, rugosidad) fueron verificados por SHA-256 desde `asset/tutorial-roble_seco`.

**Evaluación visual del candidato, NO aprobado:** el dorso ya tiene madera y se ven vetas; la madera sigue demasiado clara y hay fallas residuales en bordes/corners posteriores, por lo cual **no alcanza todavía 8/10**. Las muescas rectas del frente proceden de la malla Meshy original y pueden parecer tablones metálicos.

**Notas técnicas:** la primera ejecución V006 falló al descargar Blender con HTTP 403; se agregó fallback oficial `mirror.blender.org` y la nueva ejecución terminó con éxito. Todas las vistas anteriores permanecen en sus ramas.

**Pendiente:** validación del usuario sobre el contraste entre madera y hierro antes de producir V007, luego separar geometría/materiales y optimizar GLB para PlayCanvas. No integrar ni aprobar automáticamente. No hay cambios en `main`.
