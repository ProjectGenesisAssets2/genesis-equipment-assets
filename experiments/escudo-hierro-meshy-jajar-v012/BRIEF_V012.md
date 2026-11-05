# Project Genesis | Shield V012 | Calibración aprobada del caprino V020

**Estado:** candidato de render, sin aprobación del escudo. Conserva geometría y materiales de V011 / V010A; se cambió únicamente la configuración de iluminación y la gestión de color.

## Referencia exacta
`ProjectgenesisAssets/genesis-workshop-assets`, `asset/tanned-goatskin:evaluation/tanned-goatskin/V020_OWNER_APPROVED.json`.
- Luz principal: **4600 K** con nodo **Blackbody**, misma posición `[3,-4,5]`, potencia 12 y tamaño 4 que el estudio aprobado V020.
- HDRI real **studio_small_09_2k.hdr** (RGBE / 32-bit), intensidad **0.82**.
- Vista de color Blender **Standard**, exposición **0** como el estudio de referencia V020.
- Se desactivan las dos luces auxiliares de alta potencia que quemaban el caprino en V010/V011.
- Cycles, Blender **4.5.13 LTS**, imagen PNG y JPG revisable.
- Materiales V175 (hierro) y V020 (cuero), geometría jajar y cámaras: **sin modificaciones**.

La calibración de caprino aprobada corresponde a ese material como **consumible de inventario**, no implica aprobación del escudo. Imágenes del escudo para revisión y validación humana >=8/10.

Workflow experimental privado por depender del material V175:
https://github.com/gburdesedev/genesis-blender-render/actions/runs/41946743413

**Publicar solo los JPG** dentro de `experiments/escudo-hierro-meshy-jajar-v012/previews/` tras verificar el workflow y los renders reales. No integrar ni modificar `main`.
