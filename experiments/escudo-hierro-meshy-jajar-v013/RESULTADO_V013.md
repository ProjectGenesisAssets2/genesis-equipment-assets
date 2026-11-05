# Project Genesis · Escudo V013 · Resultado de render REAL

**Estado:** ejecución técnica verificada, **NO aprobado visualmente**. Ninguna modificación a `main` ni al juego.

## Validación
GitHub Actions privado [run 41983986235](https://github.com/gburdesedev/genesis-blender-render/actions/runs/41983986235): completó Blender 4.5.13 LTS, Cycles 64 samples, 5 PNG 1100×1100, 5 JPG públicos, informe, copia .blend en rama experimental.

- GLB Meshy jajar original: `ca4e63a25acf84985d1c66fcef77ffc92abb0212e59f50f84821facd171b28f2`.
- Escena trabajo V175: `8b67ec62da384fb31ad80dcc35feec7a2f1bff08e03ad80ab3205f53dd6588ba`.
- Cuero aprobado V020: mapa PBR y procedencia intactos.
- HDRI real 32-bit: `studio_small_09_2k.hdr`, intensidad 0.82. Key 4600K con energía 12 conservada.
- Enlazado Cycles extra: solo chapa frontal de hierro y 12 remaches mediante una colección de receptores. Cuero y base de madera **excluidos de la luz extra**.

## Pruebas y fotografías verificadas
- V013A = softbox únicamente para hierro, 110 W: [frente](previews/V013A_01_frente_metal_y_cuero.jpg), [tres cuartos](previews/V013A_02_tres_cuartos.jpg)
- V013B = mismo softbox 260 W: [frente](previews/V013B_01_frente_metal_y_cuero.jpg), [tres cuartos](previews/V013B_02_tres_cuartos.jpg)
- Reverso, sin cambios en geometría o material: [JPG](previews/V013_03_reverso_perfil_4600k.jpg)

## Evaluación de las imágenes reales
La B ofrece una chapa más legible y con luz más clara, sin sobreexponer el cuero. La A ilumina menos y mantiene una lectura más opaca. **Ninguna resuelve el problema visual principal**: el hierro sigue siendo una superficie geométricamente muy lisa, con casi nulo relieve de martillazos o variación de micro-rugosidad comparado con la referencia ilustrativa. La corona de cuero es visualmente muy gruesa y plana, y una franja lateral clara de la estructura Meshy sobresale en tres cuartos. El reverso sigue con tablones claros y agarres poco creíbles.

**Importante:** la imagen generada por IA en una conversación anterior no es prueba de este asset. No reutilizar como evidencia de calidad. Para aproximarse a esa referencia habrá que trabajar incrementalmente sobre el modelo real en una nueva versión: relieve/normal y rugosidad de chapa (sin exceso estilizado), borde de cuero y remaches/agarres, luego optimizar GLB WebGL. El light linking solo pertenece al estudio de Cycles y no resuelve por sí mismo la iluminación del juego.

**Conclusión:** candidato de revisión V013B para el contraste metálico, pero NO alcanza umbral de 8/10; aguardar evaluación del usuario antes de más cambios o integración.
