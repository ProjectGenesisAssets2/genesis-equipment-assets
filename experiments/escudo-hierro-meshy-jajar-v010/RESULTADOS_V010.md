# Resultado de render V010 A/B — 4 de noviembre de 2026

**Estado:** seis vistas Cycles reales terminadas, JPEG públicas y verificadas, **escudo candidato NO aprobado**.

## Trazabilidad
- Render real: [GitHub Actions 41941401165](https://github.com/gburdesedev/genesis-blender-render/actions/runs/41941401165) (success).
- Fuente cuero: [GitHub Actions 41940961092](https://github.com/ProjectgenesisAssets/genesis-workshop-assets/actions/runs/41940961092) (success), recuperando `caprino_v020_roughness_web.glb` exacto, SHA256 `5aaeb196738d9b70cbce32102aad9ef4562b4da88550e08a2aea03ca061dca37`.
- Fuente aprobada: `asset/tanned-goatskin:evaluation/tanned-goatskin/V020_OWNER_APPROVED.json` (aprobación para material consumible de inventario; **no** aprobación del escudo).
- Blender 4.5.13 LTS + Cycles + HDRI real Poly Haven 4K HDR/RGBE de 32 bits; geometría V009 preservada; chapa frontal V175 con material derivado intacto; originales conservados en repositorio privado.
- Mapa PBR cuero: albedo `000a561fee2d2a48ea88988f01d956ec15f1e8006c03db13e187445eaedebb26`, normal `6618f354f0e8f918fe177993da133cad5a7a34cbd88c31140491e2f2506e3314`, roughness G `7c7fa3b77170f3cc8c19c4247620d5bb47cc9d51bf219a11571564159eb443ff`.

## Variantes
- **V010A:** acabado exactamente derivado del cuero V020 aprobado: albedo/normal/roughness sin retoques.
- **V010B:** mismo caprino V020, con color algo oscurecido y rugosidad multiplicada por 0,82 para un aspecto más satinado. **No fue aprobado** como material separado.
- Se mantiene el reverso de madera del escudo V009 en ambas.

## JPG públicos reales
- [V010A · frente](previews/V010A_01_frente_hierro_cuero.jpg)
- [V010A · tres cuartos](previews/V010A_02_tres_cuartos_hierro_cuero.jpg)
- [V010A · reverso](previews/V010A_03_reverso.jpg)
- [V010B · frente](previews/V010B_01_frente_hierro_cuero.jpg)
- [V010B · tres cuartos](previews/V010B_02_tres_cuartos_hierro_cuero.jpg)
- [V010B · reverso](previews/V010B_03_reverso.jpg)

## Evaluación visual inicial
El color y el grano de cuero contrastan notablemente mejor con el hierro que el roble claro de V009. La V010A es preferible provisionalmente: la V010B aporta poco y puede verse más artificial. **Dos problemas pendientes**: la sección geométrica del aro es demasiado grande y redondeada (efecto acolchado), y en el borde superior del modelo original sobresale una franja clara desde tres cuartos. El reverso de madera permanece demasiado pálido para el carácter rústico esperado. No afirmar mínimo 8/10 ni integrar.

**Siguiente decisión:** el usuario evalúa si conservar el concepto hierro + aro forrado en cuero antes de corregir la geometría en una nueva rama. Sin cambios en main ni publicación del GLB, ni GLB optimizado para WebGL.
