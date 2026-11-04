# Escudo de hierro V009 — corrección real de malla 3D

Candidato experimental **sin aprobación**. No se modifica main ni la versión pública del juego.

Se conserva el GLB Meshy original de jajar por SHA256, el material de hierro V175 de la escena de trabajo, los mapas PBR de roble seco reales del proyecto, y el HDRI de 32 bits. Se mantiene la silueta original como núcleo.

V008 construyó físicamente una lámina independiente de hierro, un aro macizo de roble UV con su textura correcta, y doce remaches de hierro. El primer render real V008 **no superó el control visual**: pliegue en forma de estrella y costura radial en la chapa, procedentes de la unión de vértices en el polo central y del doble cierre del círculo.

**V009:** corrige las caras de la chapa en el centro; elimina vértices angulares duplicados en el cierre; modula el relieve conforme aumenta el radio para que desaparezca suavemente hacia el centro. No altera la geometría de la corona ni los parámetros HDRI o de materiales.

Workflow: https://github.com/gburdesedev/genesis-blender-render/actions/runs/41924685650

**Entregables previstos y pendientes de verificación:** frente, tres cuartos y reverso reales de Blender 4.5.13 LTS/Cycles; tres JPG en previews/ de este experimento público. Mantener .blend y V175 en rama privada. No afirmar que están listos antes de verificar.
