# Escudo de hierro V007 — render y evaluación (2026-11-04)

**GitHub Actions V007:** https://github.com/gburdesedev/genesis-blender-render/actions/runs/41894863022

**Ejecución:** `success`. Blender 4.5.13 LTS, Cycles, 48 samples, 4K HDR/RGBE Poly Haven de 32 bits; 3 renders PNG 1100×1100 y 3 JPG para revisión. El hash del GLB Meshy original (`ca4e63a25acf84985d1c66fcef77ffc92abb0212e59f50f84821facd171b28f2`), de la escena copia V175 (`8b67ec62da384fb31ad80dcc35feec7a2f1bff08e03ad80ab3205f53dd6588ba`) y del HDRI (`762731ef23f7584707881a47711dca613e11cf515966685b538dfedfd694784e`) coinciden con V006. La malla original sigue con 232.273 triángulos sin optimizar.

**Solo parámetros alterados respecto de V006:** exposición -0,45 -> **-0,85 EV**; softbox frontal 950 -> **780**; softbox trasero 720 -> **600**. Geometría, mapeado, hierros y roble PBR son idénticos.

### Vistas de revisión públicas
- [Frente](previews/01_frente_hierro_v175_contorno_roble_v007.jpg)
- [Tres cuartos](previews/02_tres_cuartos_hierro_roble_v007.jpg)
- [Reverso](previews/03_reverso_roble_agarres_v007.jpg)

**Evaluación provisional:** el escudo se ve algo más oscuro, pero el borde y el dorso todavía quedan muy claros; la reducción de luz no alcanza para producir roble envejecido. Quedan detalles grises inadecuados sobre el borde posterior; esta prueba no arregló segmentación ni materiales. **NO APROBADO**. Esperar la evaluación del usuario antes de otra corrección artística. No modificar `main`, juego ni masters.
