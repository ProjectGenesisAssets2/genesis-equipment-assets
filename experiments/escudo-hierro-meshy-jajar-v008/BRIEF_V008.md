# Escudo de hierro V008 — experimento 3D (NO APROBADO)

**Objetivo:** corregir la estructura 3D real del escudo Meshy jajar, sin sustituir la prueba con arte conceptual ni reconstruir el modelo aprobado desde cero.

**Origen conservado:** GLB jajar, SHA-256 `ca4e63a25acf84985d1c66fcef77ffc92abb0212e59f50f84821facd171b28f2`. Mismo modelo y dimensiones aproximadas 2 m de diámetro, sin mover el juego ni `main`.

**Cambios respecto de V007:**
- El original queda como núcleo de madera y soporte posterior, con agarres conservados.
- Sobre la cara frontal se modela una lámina independiente de hierro forjado, algo convexa y ligeramente irregular, con material PBR procedente de la copia del lingote V175.
- Se crea un aro físico de roble en torno al borde, con UV propio y las texturas PBR reales de `ProjectgenesisAssets/genesis-workshop-assets:asset/tutorial-roble_seco` (color, normales, rugosidad).
- Se incorporan pequeños remaches de hierro, funcionales y sin adornos.
- El roble pasa a tono envejecido conservando las vetas fotográficas. No se cambia el HDRI RGBE 4K de 32 bits, se usa Blender 4.5.13 LTS con Cycles.
- Se producen vistas frente, tres cuartos y reverso, PNG y JPG. Los JPG de revisión se publicarán en `previews/` de esta rama; el master privado V175 no se publica.

**Ejecución:** https://github.com/gburdesedev/genesis-blender-render/actions/runs/41923240905

**Control de calidad:** revisar renders reales y estado de GitHub Actions. Si hay errores, corregir en la rama; ningún candidato se aprueba ni se integra automáticamente. El GLB optimizado WebGL/PlayCanvas queda pendiente de revisión, especialmente los 232.273 triángulos originales.
