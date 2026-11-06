# Project Genesis — Contrato universal de manifestación V01 (experimental)

## Estado real
- **Rayo V07:** animación helicoidal aprobada para la espada; adaptador universal NO implementado aún.
- **Fuego V20:** shader de prueba aislado en PlayCanvas; pendiente de evaluación humana y adaptación a otros objetos.
- **Hielo, Luz, Sombra, Naturaleza, Tierra:** solo especificación de comportamiento y zonas; no hay siete shaders listos.
- **Canal Base:** no se cuenta entre las siete afinidades elementales. Los canales conservan intensidad independiente 0–100.

## Regla de diseño
El objeto no almacena siete animaciones duplicadas. Provee **máscaras de superficie, curvas y anclajes semánticos**
para que los shaders reutilizables puedan manifestarse en zonas distintas de cada familia.

| Afinidad | Manifestación propuesta | Exclusividad prevista |
|---|---|---|
| Rayo | pulsos helicoidales sobre curva 3D exterior | volumen orbital |
| Fuego | llamas estrechas que fluyen hacia arriba | bandas de borde |
| Hielo | cristalización y escarcha | facetas reservadas |
| Luz | destellos localizados | puntos ornamentales |
| Sombra | corrientes oscuras en huecos | ranuras |
| Naturaleza | filamentos vegetales/energía orgánica | ramificaciones superficiales |
| Tierra | pulsos y microfracturas minerales | juntas/relieves |

Los cuatro perfiles semánticos (espada, escudo, armadura y joya) están en
`vfx/experimental/Genesis_AffinitySlots_V01.mjs`. Su validador impide duplicar
**nombres de zonas** en una familia; **NO** prueba que dos máscaras de geometría se
superpongan de verdad o que los halos se anulen en pantalla.

### Pendiente para V21/V22
1. Registrar máscaras sobre la malla real de cada objeto, con superficie y volumen exterior definidos por coordenadas locales.
2. Calcular intersecciones espaciales entre máscaras y límites de expansión de partículas.
3. Renderizar simultáneamente 7 canales, incluyendo reflejos y bloom, y examinar la legibilidad del material PBR.
4. Reducir LOD, coste de draw calls y fill-rate para PlayCanvas/WebGL móvil sin distorsionar los efectos aprobados.
5. Grabar animaciones finales únicamente tras aprobación visual (>=8/10) y verificación de juego real.

**Los perfiles son contrato experimental, no siete animaciones terminadas ni integración al juego.**
