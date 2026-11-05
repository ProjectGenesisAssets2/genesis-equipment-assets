# Project Genesis — V09 · 7 shaders universales (prueba técnica)

**Estado: EXPERIMENTAL, no integrado.** Rayo V07 conserva su shader y geometría aprobados; Fuego V01 y los otros cinco canales siguen en evaluación.

## Siete canales elementales

| Canal | Espada V03 real + escudo de prueba, intensidad fija 60 |
|---|---|
| Luz | ![Luz 60](Luz_060.png) |
| Sombra | ![Sombra 60](Sombra_060.png) |
| Fuego | ![Fuego 60](Fuego_060.png) |
| Hielo | ![Hielo 60](Hielo_060.png) |
| Naturaleza | ![Naturaleza 60](Naturaleza_060.png) |
| Tierra | ![Tierra 60](Tierra_060.png) |
| Rayo | ![Rayo 60](Rayo_060.png) |

## Combinación

![Fuego 60 + Rayo 70 sobre ambas geometrías](Fuego060_Rayo070_BothTargets.png)

**Importante:** La espada sí es la V03 original con V175, pero el escudo es una malla irregular **de control**: todavía no es el GLB real aprobado. Esta prueba comprueba que se obtiene su contorno desde sus propios vértices (no un círculo fijo ni una textura). Falta probar sobre el escudo definitivo y revisar el reverso en cámara.

Los siete canales son **Luz, Sombra, Fuego, Hielo, Naturaleza, Tierra y Rayo**. Base no es elemental; Veneno sigue siendo una técnica de Naturaleza, no una manifestación automática.

Material PBR y sombreado de efectos independientes. Este test es de comportamiento WebGL2, sin HDRI final; NO representa calidad final del hierro. Consultar [auditoría](audit.json) para cobertura real, compilación y fallos.
