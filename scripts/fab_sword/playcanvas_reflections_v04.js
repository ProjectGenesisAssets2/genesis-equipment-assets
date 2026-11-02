/*
 * Project Genesis — Fab sword reflective-iron V04 PlayCanvas lighting check.
 * Non-destructive helper: apply only to the selected V04 sword render.
 * Requires the application to already have a valid prefiltered HDR environment
 * set on app.scene.envAtlas (or provide one as third argument).
 *
 * If app.scene.envAtlas is null and no atlas is provided, the diagnostic warns.
 * This script does NOT fabricate reflections by using emissive or fake shine.
 */
(function (global) {
  'use strict';

  function enhanceSword(app, swordRoot, optionalEnvAtlas) {
    if (!app || !swordRoot) {
      throw new Error('GenesisSwordV04: app and swordRoot are required');
    }
    const pc = global.pc;
    if (!pc) throw new Error('PlayCanvas pc namespace not loaded');
    const atlas = optionalEnvAtlas || app.scene.envAtlas;
    if (!atlas) {
      console.warn('[Genesis Sword V04] HDR envAtlas missing. Metallic blade cannot show realistic environment reflections.');
    }
    const renderers = swordRoot.findComponents('render').concat(swordRoot.findComponents('model'));
    let blades = 0;
    for (const renderer of renderers) {
      for (const meshInstance of renderer.meshInstances || []) {
        const original = meshInstance.material;
        if (!original || !/Genesis_Hierro_V175_Reflections_V04/i.test(original.name)) continue;
        // Clone so that materials of other items remain unchanged.
        const material = original.clone();
        material.useMetalness = true;
        material.useSkybox = true;
        material.useLighting = true;
        material.metalness = 1;
        if (pc.FRESNEL_SCHLICK !== undefined) material.fresnelModel = pc.FRESNEL_SCHLICK;
        if (atlas) material.envAtlas = atlas;
        material.update();
        meshInstance.material = material;
        blades++;
      }
    }
    if (!blades) console.warn('[Genesis Sword V04] Blade material not found on render/model components');
    return {blades, hasEnvironment: Boolean(atlas)};
  }

  global.GenesisSwordV04 = Object.freeze({ enhanceSword });
})(typeof window === 'undefined' ? globalThis : window);
