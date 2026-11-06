# Project Genesis — biblioteca VFX de fuego REAL (Unity Labs CC0)

Este directorio conserva de forma permanente los **tres paquetes originales** descargados de [Unity Labs Paris](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) (Thomas ICHÉ, Unity Technologies, 28 de noviembre de 2016). Unity confirma explícitamente licencia **CC0**, válida fuera de Unity. <https://creativecommons.org/publicdomain/zero/1.0/>

## Recursos pendientes de incorporación por GitHub Actions

| Efecto | ZIP original | Atlas RGBA sin modificar (origen) | Atlas PNG para PlayCanvas | Demostración animada |
|---|---|---|---|---|
| Flame02 | `source/Flame02-flipbooks.zip` | Dentro del ZIP | `atlases/Flame02_16x4.png` | `previews/Flame02_animado.gif` |
| Flame03 | `source/Flame03-flipbooks.zip` | Dentro del ZIP | `atlases/Flame03_16x4.png` | `previews/Flame03_animado.gif` |
| SmallFlame01 | `source/SmallFlame01-mini-flipbooks.zip` | Dentro del ZIP | `atlases/SmallFlame01-mini_16x4.png` | `previews/SmallFlame01_animado.gif` |

Cada hoja contiene **16 × 4 cuadros**. Los GIF muestran los **cuadros originales animados en secuencia**, no composiciones conceptuales ni render de la espada.

Los renders previos de V16 usaron el TGA de SmallFlame01 como **fotos estáticas por distintas tarjetas**, no como un flipbook animado completo. Por eso se veían chispitas aisladas. **V16 no está aprobada visualmente.**

## Reglas de integración

- No modificar geometría, textura ni preset aprobado del hierro V175–V12B.
- Mantener las texturas de fuego como capas VFX independientes, con atlas animado en el tiempo.
- Anclar los emisores al borde de la hoja y crear el fuego con continuidad espacial, no 20/32 tarjetas aisladas.
- Conservar el EXR HDRI de 32 bits por canal para iluminación Blender; las hojas PNG/TGA son **texturas VFX**, no reemplazos de iluminación.
- Comparar tamaño, color, movimiento y aspecto a intensidad 60 y 100; verificar render y PlayCanvas WebGL2 antes de integrar.
- Mantener assets originales y licencia CC0; ningún recurso experimental se considera aprobado.

[Fuente y licencia oficial de Unity](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) · [Hoja de auditoría](vfx_source_audit.json)

**Todo permanece en rama de experimentación. No se modificó `main`.**
