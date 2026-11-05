# Project Genesis · Escudo de hierro V014 · Chapa castigada

**Estado:** EXPERIMENTO NO APROBADO. Trabajo sobre GLB Meshy jajar y escena V013B reales, no un concepto ilustrado.

## Alcance estrictamente acotado
- Malla frontal de chapa: se aumenta el detalle de malla radial de 14 a 48 anillos (SEG 120) y se aplican **43 abolladuras asimétricas deterministas** (seed 140514). Relieve con profundidad máxima acotada y atenuación a cero en el borde.
- El material PBR exacto V175 sigue como base: sobre una **copia derivada solo de la chapa** se añaden microporos de martillo tipo Voronoi, grano fino Noise y fluctuaciones de rugosidad. No se cambian albedo, oxidación original ni Metallic de V175; se conserva la normal procedimental anterior como entrada de los bump nuevos.
- Se mantiene **cuero caprino V020 aprobado como material** (sin cambios en mapas), su perfil HDRI studio_small_09 32-bit 0,82/4600 K, y la luz vinculada exclusivamente al metal a **260 W** de la V013B.
- No se modifican la corona de cuero, los remaches, el reverso, las correas, la geometría Meshy original ni la versión del juego.
- Blender 4.5.13 LTS / GitHub Actions / Cycles 64 samples. Cuatro renders reales: frente, tres cuartos, acercamiento real a chapa y reverso de control.

**Revisión visual:** confirmar que los abollados son reales y desiguales, sin efecto craterizado, sin artefactos radiales ni estrellas, sin parecer metal quemado. Meta >=8/10, **sin aprobación automática**. Optimización WebGL pendiente. El arte conceptual generado anteriormente no equivale a un render de este GLB.

**GitHub Actions:** https://github.com/gburdesedev/genesis-blender-render/actions/runs/41987613577

**JPG públicos, solo después de render verificado:** `experiments/escudo-hierro-meshy-jajar-v014/previews/`. Originales privados, sin tocar `main`.
