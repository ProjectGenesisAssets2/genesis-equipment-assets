# Escudo hierro + cuero V011 — resultado real (NO APROBADO)
**Blender/Cycles HDRI 32 bits:** [GitHub Actions 41944626390](https://github.com/gburdesedev/genesis-blender-render/actions/runs/41944626390) finalizó exitosamente. Primer intento 41944526616 falló por ruta de descarga del cuero, corregida antes de renderizar. 

## Comparación controlada con V010A
- Geometría, vista, materiales originales y shaders de hierro V175 y cuero caprino V020, remaches y HDRI idénticos. No cambiar piezas maestras.
- Exposición AgX de **−0,85** a **−1,15 EV**, luz frontal **780** intacta, luz posterior de **600** a **250**.
- Revisión a posteriori: el dorso deja de parecer blanqueado; se distinguen tablas y agarres. El frente mantiene hierro y cuero con menor brillo. Persisten la franja clara visible desde tres cuartos y aro físicamente demasiado grueso, problemas de geometría/segmentación pendientes de autorización.
- Estado del informe Blender: `rendered_pending_human_review`. El usuario todavía no evaluó V011. **No aprobar ni exportar juego.**

## JPG públicos verificados
- [Frente V011](previews/V011_01_frente_hierro_cuero.jpg)
- [Tres cuartos V011](previews/V011_02_tres_cuartos_hierro_cuero.jpg)
- [Reverso V011](previews/V011_03_reverso_reduccion_de_luz.jpg)

**Hashes SHA256 de las fuentes preservadas:** GLB jajar `ca4e63a25acf84985d1c66fcef77ffc92abb0212e59f50f84821facd171b28f2`, hierro V175 `8b67ec62da384fb31ad80dcc35feec7a2f1bff08e03ad80ab3205f53dd6588ba`, HDRI 4K RGBE `762731ef23f7584707881a47711dca613e11cf515966685b538dfedfd694784e`.

Sin cambios en main. Los PNG, el .blend y el master V175 se guardan en rama privada de trabajo; JPG únicamente en la organización pública.
