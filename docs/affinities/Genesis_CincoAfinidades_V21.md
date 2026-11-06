# Project Genesis — V21: Cinco afinidades nuevas para la espada V03

**Estado: prototipos reales de PlayCanvas/WebGL2, NO aprobados, NO integrados al juego.**
Trabajo incremental en `ProjectGenesisAssets2/genesis-equipment-assets`. Se conserva el GLB V03 original, el material V175 y el shader aprobado de Fuego V20C.1 y Rayo V07.

## Módulos nuevos

| Afinidad | Módulo V21 | Manifestación | Zona experimental de espada |
| --- | --- | --- | --- |
| Hielo | `Genesis_Hielo_V21_Cristalizacion.mjs` | Escarcha/cristales de facetas azuladas | hoja superior (76–93%) |
| Luz | `Genesis_Luz_V21_Destellos.mjs` | puntos radiantes blancos y dorados | junto a la guarda (2–11%) |
| Sombra | `Genesis_Sombra_V21_Brumas.mjs` | corrientes umbrales violetas difusas | nervio superior-intermedio (54–69%) |
| Naturaleza | `Genesis_Naturaleza_V21_Filamentos.mjs` | ramificaciones, hojas y savia energética | hoja media-inferior (32–48%) |
| Tierra | `Genesis_Tierra_V21_Mineral.mjs` | fisuras minerales angulares pulsantes | hoja inferior (15–27%) |

Las cinco animaciones tienen shaders **distintos**, no son recolores de un mismo movimiento. Cada una admite intensidad 0–100 y dispone de geometría propia de prueba que no modifica la espada.

## Separación y límites de esta primera versión

- Cada una ocupa una banda longitudinal distinta: la separación entre las **cinco bandas** está validada estructuralmente y se examinará con capturas WebGL2 reales.
- El shader de Fuego V20C.1 sigue cubriendo sectores de la hoja: **todavía NO** se ha probado ni corregido su posible interacción con estas cinco zonas.
- Rayo V07 permanece en órbita helicoidal exterior y no se ejecuta en esta prueba.
- Los perfiles de escudos, armaduras y joyas están **solo especificados**: falta desarrollar adaptadores de malla reales y validar sus máscaras.
- Ninguno de estos cinco nuevos candidatos está aprobado. No publicar en main, ni modificar V07/V20C.1, ni reutilizar la vista experimental como arte maestro.

## Siguiente puerta de validación

Probar cada shader aislado a intensidades 0, 60 y 100 sobre el GLB V03 real; revisar visibilidad, calidad visual >=8/10, costos WebGL y transparencia; después adaptar por familia y comprobar las siete afinidades combinadas sin interferencias.
