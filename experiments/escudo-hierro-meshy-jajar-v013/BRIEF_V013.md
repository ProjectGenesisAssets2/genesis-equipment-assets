# PROJECT GENESIS — Escudo V013 (rama experimental, no aprobado)

## Origen y objetivo
V013 usa exactamente la escena 3D de V012: Meshy jajar SHA256 `ca4e63a25acf84985d1c66fcef77ffc92abb0212e59f50f84821facd171b28f2`, chapa de hierro V175 derivado, cuero caprino V020 aprobado como material de inventario, reverso y geometría originales. El usuario considera que el hierro y el cuero se sienten creíbles pero la V012 apagó excesivamente el hierro, haciendo plano el frente.

**Atención:** una imagen generada con detalle avanzado de martillazos y cuero cosido mostró una posible meta artística; es **concepto, no render del GLB**. No atribuirle detalles inexistentes al asset. El objetivo inmediato V013 es recuperar lectura metálica y especular reales en Blender, sin falsear geometría.

## Único cambio técnico, verificable
Se añade un área light **vinculada exclusivamente a los objetos hierro** (chapa frontal y 12 remaches) por el sistema Cycles Light Linking de Blender 4.5.13 LTS. La colección de receptoras no contiene ni cuero del aro ni núcleo de madera.
- **A**: luz suave específica de hierro a 110 W.
- **B**: misma luz a 260 W.
- **Restante**: mismo Blackbody 4600 K, HDRI Poly Haven `studio_small_09_2k.hdr` RGBE de 32 bits, fuerza 0,82, color Standard, cámara, muestras y materiales del caprino V020.
- Cinco renderizaciones: frente A/B, tres cuartos A/B y reverso (sin cambio por estar desligado el hierro frontal).

La luz de revisión no se transfiere literalmente a PlayCanvas: se evalúan la chapa y sus PBR en entorno iluminado. Si el hierro sigue plano, será necesaria una versión aparte de normales/roughness/altura, sin meter esos cambios en esta prueba.

### Evidencia
[GitHub Actions — V013 real](https://github.com/gburdesedev/genesis-blender-render/actions/runs/41983986235)

Los JPG reales, una vez renderizados y verificados, se publican a `experiments/escudo-hierro-meshy-jajar-v013/previews/` en esta misma rama pública. El material maestro V175 y el .blend de producción permanecen privados.

**Regla:** sin aprobación explícita del usuario (meta >=8/10), sin cambios a main ni integración a la demo. Mantener intactas las versiones V009–V012.
