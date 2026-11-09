/* Project Genesis / PlayCanvas · Preparación de hierro.
   Las intervenciones regulan el calor; el avance de 0 a 100 ocurre
   CONTINUAMENTE mientras la temperatura permanece en rangos válidos.
   No hay tiempo límite ni resultados de fabricación ligados a este avance.
   Temperaturas normalizadas y equivalencia 1:1: DEMO provisional. */
(() => {
  'use strict';

  const safePreviews = !!window.GenesisDevice?.safePreviews;
  let layoutFrame = 0, layoutObserver;
  function syncOriginalLayout(){
    layoutFrame = 0;
    const wrapper = document.querySelector('.prepSkinModal .prepSkinScroll');
    const layer = document.getElementById('modalLayer');
    if (!wrapper || !layer || !layer.clientWidth || !layer.clientHeight) return;
    const style = getComputedStyle(layer);
    const width = layer.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
    const height = layer.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
    // El lienzo original (1536x1024) conserva su geometría; el marco exterior
    // se amplía a 16:9 sin estirar texto, casillas ni controles del minijuego.
    const PANORAMA_WIDTH = 1820.4444444444443;
    const scale = Math.max(.01, Math.min(1, width / PANORAMA_WIDTH, height / 1024));
    wrapper.style.setProperty('--prep-layout-width', `${PANORAMA_WIDTH * scale}px`);
    wrapper.style.setProperty('--prep-layout-height', `${1024 * scale}px`);
    wrapper.style.setProperty('--prep-scale', scale);
  }
  function scheduleOriginalLayout(){
    if (!layoutFrame) layoutFrame = requestAnimationFrame(syncOriginalLayout);
  }
  addEventListener('resize', scheduleOriginalLayout, {passive:true});
  window.visualViewport?.addEventListener('resize', scheduleOriginalLayout, {passive:true});

  const RAW = 'Mineral de hierro';
  const PREPARED = 'Lingote de hierro';
  const CHARCOAL = 'Carbón vegetal';
  // Mineral V008 aprobado: 55.000 triángulos y PBR 1536; PNG RGBA en móvil.
  // El lingote V175 conserva su modelo y render anteriores.
  // Un PNG nunca se anima como si fuese geometría 3D.
  const MATERIAL_ART = Object.freeze({
    [RAW]: Object.freeze({
      poster: 'assets/playcanvas/approved/materials/iron_ore/v008_55k_pbr1536_v007/mineral_hierro_v008_transparent_0.png',
      model: 'assets/playcanvas/approved/materials/iron_ore/v008_55k_pbr1536_v007/mineral_hierro_v008_55k_pbr1536_v007.glb'
    }),
    [PREPARED]: Object.freeze({
      poster: 'assets/playcanvas/approved/materials/iron/v175/iron_v175_transparent.png',
      model: 'assets/playcanvas/candidates/materials/iron_ingot/v175/iron_v175_web_candidate.glb'
    }),
    [CHARCOAL]: Object.freeze({
      poster: 'assets/playcanvas/approved/materials/charcoal/v011/carbon_vegetal_v011_poster.png',
      model: 'assets/playcanvas/approved/materials/charcoal/v011/carbon_vegetal_v011_final_3_piezas_web.glb'
    })
  });
  // Perfil térmico por material. Solo el hierro tiene cifras DEMO: aún no
  // existen umbrales canónicos aprobados para cobre, estaño o bronce.
  // Los perfiles futuros podrán variar objetivo, tolerancia, enfriamiento,
  // respuesta al fuelle y velocidad de proceso SIN reescribir el minijuego.
  const MATERIAL_PROFILES = Object.freeze({
    [PREPARED]: Object.freeze({
      target: 72, baseTolerance: 11, initialGap: 17,
      coolingPerSecond: 0.45 * 1.90, heatResponse: 1, processingSpeed: 1.60 * 1.30
    })
  });
  const BASE_PROGRESS_PER_SECOND = 3; // Velocidad demostrativa; NO es un cronómetro límite.
  const MASS_COOLING_ADJUSTMENT = 0.02; // Diferencia suave entre tamaños dentro de un mismo tramo de dificultad.
  const THERMAL_TICK_MS = 125;
  const BELLOWS = Object.freeze([
    { label: 'BAJO', gain: 3.8, key: '1', description: 'Corrección fina' },
    { label: 'MODERADO', gain: 8.5, key: '2', description: 'Aporte equilibrado' },
    { label: 'ALTO', gain: 14.5, key: '3', description: 'Recuperación intensa' }
  ]);
  // 39 capas originales: coordenadas del layout aprobado V002.
  const SKIN_ROOT = 'assets/ui/preparacion/';
  const SKIN_LAYERS = Object.freeze([
    ["FondoEstructural", "01_Capas/Fondo/FondoEstructural.png", 0, 0, 1536, 1024, "fondo_marco_principal"],
    ["Pestana_Inventario", "01_Capas/Pestanas/Pestana_Inventario.png", 164, 42, 294, 94, "pestana"],
    ["Pestana_Preparacion", "01_Capas/Pestanas/Pestana_Preparacion.png", 458, 42, 320, 94, "pestana"],
    ["Pestana_Fabricaciones", "01_Capas/Pestanas/Pestana_Fabricaciones.png", 778, 42, 328, 94, "pestana"],
    ["Pestana_Comparacion", "01_Capas/Pestanas/Pestana_Comparacion.png", 1106, 42, 298, 94, "pestana"],
    ["PanelBasicos", "01_Capas/Paneles/PanelBasicos.png", 17, 153, 562, 380, "grupo_de_10_materiales_basicos"],
    ["PanelPreparados", "01_Capas/Paneles/PanelPreparados.png", 17, 533, 562, 380, "grupo_de_10_materiales_preparados"],
    ["FondoVisorHerreria", "01_Capas/Paneles/FondoVisorHerreria.png", 579, 153, 548, 760, "fondo_visor"],
    ["PanelDatos", "01_Capas/Paneles/PanelDatos.png", 1127, 153, 399, 624, "contenedor_sin_campos_estaticos"],
    ["PanelAccionSinBoton", "01_Capas/Paneles/PanelAccionSinBoton.png", 1127, 777, 399, 136, "panel_accion_sin_boton"],
    ["Casilla_Basicos_01", "01_Capas/Casillas/Casilla_Basicos_01.png", 37, 274, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Basicos_02", "01_Capas/Casillas/Casilla_Basicos_02.png", 145, 274, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Basicos_03", "01_Capas/Casillas/Casilla_Basicos_03.png", 245, 274, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Basicos_04", "01_Capas/Casillas/Casilla_Basicos_04.png", 348, 274, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Basicos_05", "01_Capas/Casillas/Casilla_Basicos_05.png", 451, 274, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Basicos_06", "01_Capas/Casillas/Casilla_Basicos_06.png", 37, 387, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Basicos_07", "01_Capas/Casillas/Casilla_Basicos_07.png", 145, 387, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Basicos_08", "01_Capas/Casillas/Casilla_Basicos_08.png", 245, 387, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Basicos_09", "01_Capas/Casillas/Casilla_Basicos_09.png", 348, 387, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Basicos_10", "01_Capas/Casillas/Casilla_Basicos_10.png", 451, 387, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Preparados_01", "01_Capas/Casillas/Casilla_Preparados_01.png", 37, 646, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Preparados_02", "01_Capas/Casillas/Casilla_Preparados_02.png", 145, 646, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Preparados_03", "01_Capas/Casillas/Casilla_Preparados_03.png", 245, 646, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Preparados_04", "01_Capas/Casillas/Casilla_Preparados_04.png", 348, 646, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Preparados_05", "01_Capas/Casillas/Casilla_Preparados_05.png", 451, 646, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Preparados_06", "01_Capas/Casillas/Casilla_Preparados_06.png", 37, 757, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Preparados_07", "01_Capas/Casillas/Casilla_Preparados_07.png", 145, 757, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Preparados_08", "01_Capas/Casillas/Casilla_Preparados_08.png", 245, 757, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Preparados_09", "01_Capas/Casillas/Casilla_Preparados_09.png", 348, 757, 99, 108, "casilla_marco_transparente"],
    ["Casilla_Preparados_10", "01_Capas/Casillas/Casilla_Preparados_10.png", 451, 757, 99, 108, "casilla_marco_transparente"],
    ["MarcoVisorSuperior", "01_Capas/Paneles/MarcoVisorSuperior.png", 579, 153, 548, 760, "marco_visor_superpuesto"],
    ["BotonPreparar_Normal", "01_Capas/BotonPreparar/BotonPreparar_Normal.png", 1137, 777, 378, 122, "boton_normal"],
    ["BotonPreparar_Hover", "01_Capas/BotonPreparar/BotonPreparar_Hover.png", 1137, 777, 378, 122, "boton_hover"],
    ["BotonPreparar_Presionado", "01_Capas/BotonPreparar/BotonPreparar_Presionado.png", 1137, 777, 378, 122, "boton_presionado"],
    ["BotonPreparar_Deshabilitado", "01_Capas/BotonPreparar/BotonPreparar_Deshabilitado.png", 1137, 777, 378, 122, "boton_deshabilitado"],
    ["Pestana_Inventario_HoverBrillo", "01_Capas/Efectos/Pestana_Inventario_HoverBrillo.png", 164, 42, 294, 94, "hover_overlay"],
    ["Pestana_Preparacion_HoverBrillo", "01_Capas/Efectos/Pestana_Preparacion_HoverBrillo.png", 458, 42, 320, 94, "hover_overlay"],
    ["Pestana_Fabricaciones_HoverBrillo", "01_Capas/Efectos/Pestana_Fabricaciones_HoverBrillo.png", 778, 42, 328, 94, "hover_overlay"],
    ["Pestana_Comparacion_HoverBrillo", "01_Capas/Efectos/Pestana_Comparacion_HoverBrillo.png", 1106, 42, 298, 94, "hover_overlay"]
  ]);
  const escape = value => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
  const countOf = (inventory, name) => Math.max(0, Number(inventory?.[name]) || 0);
  const whole = value => Number.isSafeInteger(value) && value > 0;
  // Los materiales ya preparados o tratados se usan en Fabricaciones, no en Preparación.
  const isPreparedStockName = name => /^(Lingote|Material preparado|Material tratado)/i.test(String(name || ''));
  const isCraftMaterial = (ctx, name) => name !== RAW &&
    (isPreparedStockName(name) || !!ctx.formula?.materials?.some(entry => entry.material === name));

  function batchProfile(count, material = PREPARED) {
    if (!whole(count)) throw new Error('Cantidad inválida');
    const materialRule = typeof material === 'string' ? MATERIAL_PROFILES[material] : material;
    if (!materialRule || !Number.isFinite(materialRule.target) || materialRule.target < 0 || materialRule.target > 100 ||
        !Number.isFinite(materialRule.baseTolerance) || materialRule.baseTolerance <= 0 ||
        !Number.isFinite(materialRule.coolingPerSecond) || materialRule.coolingPerSecond < 0 ||
        !Number.isFinite(materialRule.heatResponse) || materialRule.heatResponse <= 0 ||
        !Number.isFinite(materialRule.processingSpeed) || materialRule.processingSpeed <= 0 ||
        !Number.isFinite(materialRule.initialGap) || materialRule.initialGap < 0) {
      throw new Error('Perfil térmico del material inválido');
    }
    const extra = Math.max(0, count - 10);
    // Porcentajes aprobados: 100%, 140%, 170%; desde 11, sumar CINCO
    // puntos porcentuales por cada unidad adicional (11=175%, 12=180%).
    // Sin incrementos ocultos del 2,5% por unidad ni porcentajes compuestos.
    const effortMultiplier = count === 1 ? 1 : count <= 5 ? 1.4 : count <= 10 ? 1.7 : 1.7 + 0.05 * extra;
    const difficultyMultiplier = effortMultiplier;
    // Los porcentajes de dificultad estrechan la precisión requerida.
    // El perfil de cada material controla independientemente el comportamiento.
    const thermalLoad = Math.sqrt(difficultyMultiplier);
    const tolerance = Math.max(4, materialRule.baseTolerance / difficultyMultiplier);
    const thermalInertia = thermalLoad;
    const coolingPerSecond = materialRule.coolingPerSecond * difficultyMultiplier + MASS_COOLING_ADJUSTMENT * Math.log2(count);
    return {
      count, effortMultiplier, difficultyMultiplier, tolerance, thermalInertia,
      target: materialRule.target, initialGap: materialRule.initialGap,
      coolingPerSecond, heatResponse: materialRule.heatResponse,
      processingSpeed: materialRule.processingSpeed
    };
  }

  function rawStock(required) {
    const inventory = { ...(required || {}) };
    const iron = countOf(inventory, PREPARED);
    if (iron) {
      delete inventory[PREPARED];
      inventory[RAW] = countOf(inventory, RAW) + iron;
    }
    return inventory;
  }

  function shortages(formula, inventory) {
    const requested = {};
    for (const row of formula?.materials || []) requested[row.material] = (requested[row.material] || 0) + row.qty;
    return Object.entries(requested).map(([material, needed]) => ({ material, needed, available: countOf(inventory, material), missing: Math.max(0, needed - countOf(inventory, material)) }));
  }

  function ready(formula, inventory) {
    const rows = shortages(formula, inventory);
    return rows.length > 0 && rows.every(row => row.missing === 0);
  }

  function convert(inventory, count) {
    if (!whole(count) || countOf(inventory, RAW) < count) return false;
    inventory[RAW] -= count;
    inventory[PREPARED] = countOf(inventory, PREPARED) + count;
    return true;
  }

  function actionEffect(temperature, target, profile, action) {
    const power = BELLOWS.find(b => b.key === String(action));
    if (!power) throw new Error('Intervención desconocida');
    const nextTemperature = Math.max(0, Math.min(100, temperature + power.gain * profile.heatResponse / profile.thermalInertia));
    // SOLO 3 intensidades de fuelle. Sin pulsar, la fragua reposa y se enfría.
    // Una intervención cambia la temperatura pero no entrega puntos.
    return { temperature: nextTemperature };
  }

  function progressRate(temperature, target, tolerance) {
    // Curva continua con pico EXCLUSIVO en el centro verde:
    // amarillo (±1 tolerancia) = 20 % del ritmo ideal;
    // extremos azul/naranja (±1,55 tolerancias) = 0.
    const displacement = Math.abs(temperature - target) / tolerance;
    if (displacement >= 1.55) return 0;
    if (displacement <= 1) return 1 - 0.8 * displacement;
    return 0.2 * (1.55 - displacement) / 0.55;
  }

  function temperatureStatus(temperature, target, tolerance) {
    const rate = progressRate(temperature, target, tolerance);
    if (temperature <= target - tolerance * 1.55) return { tone: 'cold', message: 'Demasiado fría: la barra está detenida. Activá el fuelle.' };
    if (temperature >= target + tolerance * 1.55) return { tone: 'hot', message: 'Demasiado caliente: soltá los controles y dejá enfriar.' };
    if (rate >= 0.85) return { tone: 'good', message: 'Muy cerca del punto ideal: avance alto.' };
    if (temperature < target) return { tone: 'near', message: 'Por debajo del punto ideal: cuanto más te acerques, más rápido avanzará.' };
    return { tone: 'near', message: 'Por encima del punto ideal: esperá sin pulsar para recuperar eficiencia.' };
  }

  function heatBands(target, tolerance) {
    const bound = value => Math.max(0, Math.min(100, value));
    const coldEnd = bound(target - tolerance * 1.55);
    const idealStart = bound(target - tolerance);
    const idealEnd = bound(target + tolerance);
    const hotStart = bound(target + tolerance * 1.55);
    return [
      { tone: 'cold', label: 'Frío', from: 0, to: coldEnd },
      { tone: 'near', label: 'Aproximación', from: coldEnd, to: idealStart },
      { tone: 'good', label: 'Trabajo ideal', from: idealStart, to: idealEnd },
      { tone: 'near', label: 'Aproximación', from: idealEnd, to: hotStart },
      { tone: 'hot', label: 'Exceso', from: hotStart, to: 100 }
    ];
  }

  function heatGradient(target, tolerance) {
    const bands = heatBands(target, tolerance);
    const point = value => Math.max(0, Math.min(100, value)).toFixed(2) + '%';
    const blueEdge = bands[0].to;
    const coldYellow = bands[1].to;
    const hotYellow = bands[3].from;
    const orangeEdge = bands[3].to;
    return `linear-gradient(90deg, #21558d 0%, #4784bd ${point(blueEdge)}, #e9c24b ${point(coldYellow)}, #24bf62 ${point(target)}, #e9c24b ${point(hotYellow)}, #f29a42 ${point(orangeEdge)}, #d9652e 100%)`;
  }

  function passiveCooling(temperature, elapsedSeconds, profile) {
    const elapsed = Math.max(0, elapsedSeconds);
    return Math.max(0, temperature - elapsed * profile.coolingPerSecond);
  }

  function progressGain(temperature, target, profile, elapsedSeconds) {
    const elapsed = Math.max(0, elapsedSeconds);
    // La barra avanza según cercanía CONTINUA al punto ideal.
    // Al alejarse disminuye progresivamente, hasta detenerse en los extremos.
    return elapsed * BASE_PROGRESS_PER_SECOND * profile.processingSpeed *
      progressRate(temperature, target, profile.tolerance) / profile.effortMultiplier;
  }

  function advanceWork(work, elapsedSeconds) {
    const elapsed = Math.max(0, elapsedSeconds);
    // Muestra intermedia del calor para que el avance sea estable entre ticks
    // aunque se crucen levemente los bordes de una franja.
    const midTemperature = passiveCooling(work.temperature, elapsed / 2, work.batch);
    work.progress = Math.min(100, work.progress + progressGain(midTemperature, work.target, work.batch, elapsed));
    work.temperature = passiveCooling(work.temperature, elapsed, work.batch);
  }

  let session = null;
  let thermalTimer = null;

  function halt() {
    if (thermalTimer !== null) clearInterval(thermalTimer);
    thermalTimer = null;
  }

  function passiveStep() {
    const ctx = session, work = ctx?.work;
    if (!ctx || ctx.mode !== 'running' || !work || work.done) { halt(); return; }
    const now = performance.now();
    const elapsed = Math.max(0, Math.min((now - work.lastThermalAt) / 1000, 0.5));
    work.lastThermalAt = now;
    // Las pestañas en segundo plano no deben castigar ni agotar tandas.
    if (document.hidden) return;
    advanceWork(work, elapsed);
    if (work.progress >= 100 - 0.000001) {
      work.progress = 100;
      finish();
    } else {
      drawThermal();
    }
  }

  function bind(id, fn) {
    const el = document.getElementById(id);
    if (el) el.addEventListener('click', fn);
  }

  function close() {
    if (!session) return;
    const ctx = session;
    halt();
    session = null;
    document.removeEventListener('keydown', onKeyDown, true);
    ctx.closeModal();
  }

  // Recompone la interfaz de 1536 × 1024 mediante las piezas originales.
  // El mismo marco sirve para selección, control térmico y resultado.
  const skinPos = (x, y, width, height) =>
    `left:${(x / 1536 * 100).toFixed(4)}%;top:${(y / 1024 * 100).toFixed(4)}%;width:${(width / 1536 * 100).toFixed(4)}%;height:${(height / 1024 * 100).toFixed(4)}%`;

  function skinImage(layer) {
    const [name, file, x, y, width, height, role] = layer;
    const state = role.startsWith('boton_') ? role.slice(6) : '';
    const hover = role === 'hover_overlay' ? name.replace('Pestana_', '').replace('_HoverBrillo', '') : '';
    return `<img class="prepSkinPiece" data-role="${role}" data-state="${state}" data-hover="${hover}" src="${SKIN_ROOT + file}" alt="" aria-hidden="true" draggable="false" style="${skinPos(x,y,width,height)}">`;
  }

  function materialVisual(material, type) {
    const art = MATERIAL_ART[material];
    if (!art) return '';
    const name = escape(material);
    const poster = escape(art.poster);
    // Regla aprobada: el visor grande muestra una imagen PNG estática.
    // Sólo las casillas pequeñas usan GLB y giran cuando reciben hover.
    const render3D = !safePreviews && art.model && type !== 'featured';
    const exposure = material === CHARCOAL ? '1.16' : '1.45';
    const visual = render3D
      ? `<model-viewer class="prepMaterialModel" src="${escape(window.GenesisPreflight?.modelUrl(art.model) || art.model)}" poster="${poster}" loading="lazy" reveal="auto" interaction-prompt="none" camera-orbit="0deg 75deg auto" environment-image="neutral" exposure="${exposure}" shadow-intensity="0" alt="${name}"></model-viewer>`
      : `<img class="prepMaterialPoster" src="${poster}" alt="${name}" loading="lazy" draggable="false">`;
    return `<span class="prepMaterialVisual ${type}${material === CHARCOAL ? ' charcoal' : ''}" data-material="${name}">${visual}</span>`;
  }

  // Solo assets 3D de slots pequenos: oscilacion -45 a +45 en hover o
  // pulsacion sostenida; al retirar raton o dedo se suaviza hasta 0 grados.
  // El objeto 3D nunca gira fuera de sus slots; el resultado central es PNG fijo.
  function bindModelHover() {
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;
    document.querySelectorAll('.prepSkinModal .prepSkinSlot .prepMaterialVisual').forEach(surface => {
      const viewer = surface.querySelector('model-viewer');
      const slot = surface.closest('.prepSkinSlot');
      if (!viewer || !slot || viewer.dataset.genesisHoverBound) return;
      viewer.dataset.genesisHoverBound = '1';
      let active = false, heldPointer = null, angle = 0, last = 0, orbitStart = 0, frame = 0;
      const animate = now => {
        if (!viewer.isConnected) { frame = 0; return; }
        const dt = last ? Math.min(now - last, 64) : 16;
        last = now;
        if (active) angle = 45 * Math.sin((now - orbitStart) * Math.PI * 2 / 4000);
        else {
          angle *= Math.exp(-dt / 180);
          if (Math.abs(angle) < 0.08) angle = 0;
        }
        viewer.cameraOrbit = `${angle.toFixed(3)}deg 75deg auto`;
        if (active || angle !== 0) frame = requestAnimationFrame(animate);
        else frame = 0;
      };
      const enter = () => {
        if (active) return;
        active = true;
        orbitStart = performance.now() - Math.asin(Math.max(-1, Math.min(1, angle / 45))) * 4000 / (Math.PI * 2);
        if (!frame) frame = requestAnimationFrame(animate);
      };
      const leave = () => { active = false; };
      slot.addEventListener('pointerenter', event => {
        if (event.pointerType === 'mouse' && window.matchMedia?.('(hover: hover) and (pointer: fine)').matches) enter();
      });
      slot.addEventListener('pointerleave', event => {
        if (event.pointerType === 'mouse' || heldPointer === event.pointerId) leave();
      });
      slot.addEventListener('pointerdown', event => {
        if (event.pointerType !== 'touch' && event.pointerType !== 'pen') return;
        heldPointer = event.pointerId;
        try { slot.setPointerCapture?.(event.pointerId); } catch (_) { /* Safari may decline capture. */ }
        enter();
      });
      const release = event => {
        if (heldPointer !== event.pointerId) return;
        heldPointer = null;
        leave();
      };
      slot.addEventListener('pointerup', release);
      slot.addEventListener('pointercancel', release);
      slot.addEventListener('lostpointercapture', release);
    });
  }

  // Las veinte casillas conservan las posiciones exactas de Preparación.
  // El contenido depende del inventario y las creaciones reales de la partida.
  function skinSlots(ctx) {
    const tab = ctx.tab || 'Preparacion';
    const crafted = tab === 'Comparacion' || (tab === 'Inventario' && ctx.inventoryCategory === 'creations');
    const frames = SKIN_LAYERS.filter(layer => layer[6] === 'casilla_marco_transparente');
    const items = ctx.getItems ? ctx.getItems() : [];
    const stock = Object.entries(ctx.inventory).filter(([,qty]) => Number(qty) > 0);
    const basic = stock.filter(([name]) => !isPreparedStockName(name)).slice(0, 10);
    const prepared = stock.filter(([name]) => isPreparedStockName(name)).slice(0, 10);
    return frames.map((layer, index) => {
      const [, , x, y, width, height] = layer;
      const item = crafted ? items[index] : null;
      const entry = crafted ? null : index < 10 ? basic[index] : prepared[index - 10];
      const selected = crafted
        ? !!item && (tab === 'Comparacion' ? ctx.compareA === index || ctx.compareB === index : !!ctx.viewItem && ctx.selectedItem === index)
        : !!entry && !ctx.viewItem && (ctx.selectedMaterial || RAW) === entry[0];
      const active = !!item || !!entry;
      const label = item ? item.name + ' · ' + item.rarity : entry ? entry[0] + ' · ' + entry[1] : 'Casilla vacía';
      const visual = item
        ? '<span class="workspaceSlotAsset">' + (ctx.renderAsset ? ctx.renderAsset(item) : '') + '</span><small class="workspaceSlotRarity">' + escape(item.rarity) + '</small>'
        : entry ? materialVisual(entry[0], entry[0] === RAW ? 'ore' : entry[0] === CHARCOAL ? 'charcoal' : 'ingot') + '<strong>' + entry[1] + '</strong>' : '';
      const kind = item ? ' data-item-index="' + index + '"' : entry ? ' data-stock-name="' + escape(entry[0]) + '"' : '';
      const compareSide = item && tab === 'Comparacion' ? (ctx.compareA === index ? ' compareA' : ctx.compareB === index ? ' compareB' : '') : '';
      return '<button type="button" class="prepSkinSlot ' + (active ? 'occupied' : 'empty') + (selected ? ' selected' : '') + compareSide +
        '" aria-label="' + escape(label) + '" title="' + escape(label) + '"' + kind +
        ' style="' + skinPos(x+5,y+5,width-10,height-10) + '"' + (active ? '' : ' disabled') + '>' + visual + '</button>';
    }).join('');
  }
  function skinIngredients(ctx) {
    // Equivalencia 1 mineral -> 1 lingote: DEMO provisional de hierro.
    // El contador expresa la materia prima requerida PARA LA TANDA,
    // no lo que ya existe en inventario ni nuevos productos obtenidos.
    const needed = ctx.count || 0;
    const available = countOf(ctx.inventory, RAW);
    const frame = `${SKIN_ROOT}01_Capas/Casillas/Casilla_Basicos_01.png`;
    return `<section class="prepSkinIngredients" aria-label="Materiales necesarios para preparar el lingote">
      <h3>MATERIALES NECESARIOS</h3>
      <div class="prepSkinIngredientRow">
        <div class="prepSkinSlot prepSkinRecipeSlot ${available >= needed && needed ? 'occupied' : 'insufficient'}" role="img" tabindex="0" aria-label="${escape(RAW)}: ${needed} necesario${needed === 1 ? '' : 's'} para esta tanda">
          ${materialVisual(RAW, 'ore')}
          <img class="prepSkinRecipeFrame" src="${frame}" alt="" aria-hidden="true" draggable="false">
          <strong>${needed ? `×${needed}` : '0'}</strong>
        </div>
      </div>
      <p>${escape(RAW)}${needed ? ` · ${needed} para esta tanda` : ' · sin minerales disponibles'}</p>
    </section>`;
  }

  function skinDisplay(stage, center, details, footer) {
    const ctx = session;
    if (!ctx) return;
    const canCraft = ready(ctx.formula, ctx.inventory);
    const canPrepare = stage === 'menu' && ctx.profession === 'Herrero' && countOf(ctx.inventory, RAW) > 0;
    const layerHTML = SKIN_LAYERS.map(skinImage).join('');
    ctx.modal(`<div class="prepSkinScroll"><div class="prepArtboard" data-stage="${stage}" data-active-tab="${escape(ctx.tab || 'Preparacion')}">
      ${layerHTML}
      <h2 class="prepCompactTitle">${escape(ctx.tab || "PREPARACIÓN")}</h2><div class="prepSkinInventory" aria-label="Materiales básicos y preparados">${skinSlots(ctx)}</div>
      ${stage === 'menu' ? `<div class="prepSkinFeatured" aria-label="Resultado de preparación: lingote de hierro, vista estática">${materialVisual(PREPARED, 'featured')}</div>${skinIngredients(ctx)}` : ''}
      <div class="prepSkinCenter" data-stage="${stage}">${center}</div>
      <section class="prepSkinDetails" aria-label="Detalles de preparación">${details}</section>
      <button class="prepSkinTab" data-tab="Inventario" data-label="Inventario" aria-label="Inventario (no disponible en este menú)" disabled style="${skinPos(164,42,294,94)}"></button>
      <button class="prepSkinTab" data-tab="Preparacion" data-label="Preparación" aria-label="Preparación, pestaña actual" aria-current="page" disabled style="${skinPos(458,42,320,94)}"></button>
      <button class="prepSkinTab" data-tab="Fabricaciones" data-label="Fabricación" id="prepFabricateTab" aria-label="Ir a fabricar" ${canCraft && stage === 'menu' ? '' : 'disabled'} style="${skinPos(778,42,328,94)}"></button>
      <button class="prepSkinTab" data-tab="Comparacion" data-label="Comparación" aria-label="Comparación (aún no disponible)" disabled style="${skinPos(1106,42,298,94)}"></button>
      <button class="prepSkinStart" id="prepStart" data-label="Preparar lote" ${canPrepare ? '' : 'disabled'} aria-label="${canPrepare ? 'Empezar la preparación del lote' : 'Preparar no disponible'}" style="${skinPos(1137,777,378,122)}"></button>
      <button class="prepSkinClose" id="prepClose" aria-label="Cerrar preparación" title="Cerrar">×</button>
      <div class="prepSkinFooter" aria-live="polite">${footer || 'Preparación · minerales en bruto → lingotes · no otorga experiencia'}</div>
    </div></div>`, 'preparationModal prepSkinModal');
    syncOriginalLayout();
    if (!layoutObserver && typeof ResizeObserver !== 'undefined') {
      layoutObserver = new ResizeObserver(scheduleOriginalLayout);
      layoutObserver.observe(document.getElementById('modalLayer'));
    }
    bind('prepClose', close);
    bind('prepSelectIron', () => { if (ctx.mode === 'menu') renderMenu(); });
    if(!ctx.getItems)bind('prepFabricateTab', craft);
    bindModelHover();
    bindWorkspaceTabs(stage);
    if (stage === 'menu' && ctx.getItems) {
      // Desde Preparación: pulsar un material tratado va directo a Fabricaciones.
      document.querySelectorAll('.prepSkinSlot[data-stock-name]').forEach(slot => {
        slot.onclick = () => {
          ctx.selectedMaterial = slot.dataset.stockName;
          // El carbón es un insumo de receta, pero seleccionar su stock debe abrir su modelo.
          if (ctx.selectedMaterial === CHARCOAL) { ctx.inventoryCategory = 'materials'; renderWorkspace('Inventario'); }
          else if (isCraftMaterial(ctx, ctx.selectedMaterial)) renderWorkspace('Fabricaciones');
          else renderMenu();
        };
      });
    }
  }

  function bindWorkspaceTabs(stage) {
    const ctx=session;
    if(!ctx?.getItems||!['menu','workspace'].includes(stage))return;
    document.querySelectorAll('.prepSkinTab').forEach(button=>{
      button.disabled=false;button.removeAttribute('aria-current');
      const tab=button.dataset.tab;
      button.setAttribute('aria-label',button.dataset.label||tab);
      if(tab===(ctx.tab||'Preparacion'))button.setAttribute('aria-current','page');
      button.onclick=()=>{ctx.tab=tab;if(tab==='Preparacion')renderMenu();else renderWorkspace(tab)};
    });
  }
  function sheetForItem(ctx, item) {
    const isProtection = /escudo|armadura|botas/i.test(item.recipe || '');
    const channels = Array.isArray(item.channels) ? item.channels : [];
    const formula = item.formula?.materials || [];
    const tab = ctx.sheetTab || 'channels';
    const heading = '<p class="prepSkinKicker">FICHA DE CREACIÓN · ' + escape(item.rarity || '—') + '</p><h3 class="workspaceObjectTitle">' + escape(item.name) + '</h3>' +
      '<div class="workspaceSheetTabs" role="tablist" aria-label="Datos de la creación">' +
      '<button type="button" data-sheet-tab="channels" role="tab" aria-selected="' + (tab === 'channels') + '">CANALES Y DAÑO</button>' +
      '<button type="button" data-sheet-tab="craft" role="tab" aria-selected="' + (tab === 'craft') + '">FABRICACIÓN</button></div>';
    let body;
    if (tab === 'channels') {
      body = channels.length ? channels.map((channel, index) => {
        const metric = ctx.metricForChannel ? ctx.metricForChannel(item, channel, index) :
          {label:index === 0 ? (isProtection ? 'Protección base' : 'Daño base') : (isProtection ? 'Protección de ' : 'Daño de ') + channel[0],
           display:(index === 0 ? '' : '+') + String(channel[1]) + (index === 0 ? '' : '%')};
        return '<div class="workspaceMetric"><span>' + escape(metric.label) + '</span><b>' + escape(metric.display) + '</b></div>';
      }).join('') : '<p>La ficha de canales se habilita al terminar la fabricación.</p>';
      body += '<div class="workspaceMetric"><span>Canales activos</span><b>' + channels.length + '</b></div>';
    } else {
      body = '<p class="workspaceSubhead">Fórmula utilizada en este cierre</p>' +
        (formula.length ? formula.map(m => '<div class="workspaceMetric"><span>' + escape(m.material) + '</span><b>' + Number(m.qty || 0) + '×</b></div>').join('') : '<p>Sin fórmula registrada.</p>') +
        '<p class="workspaceFootnote">La fórmula pertenece a la sesión. Cada fabricación produce un objeto individual, incluso si su rareza es Inútil.</p>';
    }
    const reading = typeof ctx.namingReason === 'function' ? ctx.namingReason(item) : 'Nombre y rareza proceden del cierre registrado.';
    return heading + '<div class="workspaceSheetBody">' + body + '</div>' +
      '<section class="workspaceNge"><div class="workspaceNgeLabel">NGE · LECTURA DEL NOMBRE</div>' +
      '<div class="workspaceNgeScroll" tabindex="0">' + reading + '</div></section>';
  }

  // Integración visual aprobada (PNG exactos); carga aislada, con fallback al controlador previo.
  let approvedUiLoadState='idle',approvedUiPending=null;
  function loadApprovedUi(next){
    if(window.GenesisApprovedUI?.render)return true;
    if(approvedUiLoadState==='failed')return false;
    approvedUiPending=next;
    if(approvedUiLoadState==='loading')return false;
    approvedUiLoadState='loading';
    const style=document.createElement('link');
    style.rel='stylesheet';style.href='genesis_ui_approved.css?v=014028';
    document.head.append(style);
    const script=document.createElement('script');
    script.src='genesis_ui_approved.js?v=014028';
    script.onload=()=>{
      approvedUiLoadState=window.GenesisApprovedUI?.render?'ready':'failed';
      if(approvedUiLoadState==='failed')console.error('[Genesis UI] Falta el módulo de arte aprobado');
      const fn=approvedUiPending;approvedUiPending=null;fn?.();
    };
    script.onerror=()=>{
      approvedUiLoadState='failed';style.remove();
      console.error('[Genesis UI] No se pudo cargar el arte aprobado; se conserva interfaz anterior');
      const fn=approvedUiPending;approvedUiPending=null;fn?.();
    };
    document.head.append(script);
    return false;
  }
  function approvedUiNav(){return {renderMenu,renderWorkspace,craft,start,close,sheetForItem};}
  function renderWorkspace(tab) {
    const ctx=session;
    if(!ctx) return;
    // Único arte aprobado para Inventario V11 y Fabricaciones V07, sin cambiar los originales.
    if(ctx.profession==='Herrero'&&ctx.getItems&&['Inventario','Fabricaciones'].includes(tab)){
      if(window.GenesisApprovedUI?.render){
        halt();ctx.mode='workspace';ctx.tab=tab;
        window.GenesisApprovedUI.render(ctx,approvedUiNav(),tab);
        return;
      }
      if(approvedUiLoadState!=='failed'){
        loadApprovedUi(()=>renderWorkspace(tab));
        return;
      }
    }
    // Inventario panorámico aislado: no altera Preparación, Fabricación ni Comparación.
    // Conserva datos de la sesión real, nunca resultados incrustados en el arte.
    if(tab==='Inventario') {
      if(window.GenesisInventory16?.render) {
        halt();ctx.mode='workspace';ctx.tab=tab;
        window.GenesisInventory16.render(ctx,{renderMenu,renderWorkspace,sheetForItem});
        return;
      }
      if(!window.__GenesisInv16Loading){
        window.__GenesisInv16Loading=true;
        const style=document.createElement('link');
        style.rel='stylesheet';style.href='inventario_genesis_16x9.css?v=0.14.031-main';
        document.head.append(style);
        const approvedArtLayout=document.createElement('link');
        approvedArtLayout.rel='stylesheet';
        approvedArtLayout.href='inventario_arte_aprobado_1to1.css?v=0.14.031-main';
        document.head.append(approvedArtLayout);
        const loader=document.createElement('script');
        loader.src='inventario_genesis_16x9.js?v=0.14.031-main';
        loader.onload=()=>renderWorkspace('Inventario');
        loader.onerror=()=>{window.__GenesisInv16Loading=false;style.remove();approvedArtLayout.remove();};
        document.head.append(loader);
      }
    }
    halt();
    ctx.mode='workspace';ctx.tab=tab;
    const items=ctx.getItems ? ctx.getItems() : [];
    const stock=Object.entries(ctx.inventory).filter(([,q])=>Number(q)>0);
    ctx.selectedItem=Math.min(Math.max(0,ctx.selectedItem||0),Math.max(0,items.length-1));
    if(!ctx.inventoryCategory) ctx.inventoryCategory='materials';
    let details='',viewer='',action='',enabled=false,run=()=>{};
    const optionList=selected=>items.map((it,i)=>'<option value="'+i+'" '+(i===selected?'selected':'')+'>'+escape(it.name)+' · '+escape(it.rarity)+'</option>').join('');
    const material=stock.some(([m])=>m===ctx.selectedMaterial)?ctx.selectedMaterial:(stock[0]?.[0]||RAW);
    if(tab==='Inventario') {
      const crafted=ctx.inventoryCategory==='creations';
      ctx.viewItem=crafted && items.length>0;
      details='<p class="prepSkinKicker">INVENTARIO DEL HERRERO</p><div class="workspaceCategory" role="group" aria-label="Categorías del inventario">' +
        '<button data-inventory-category="materials" aria-pressed="'+(!crafted)+'">MATERIALES</button><button data-inventory-category="creations" aria-pressed="'+crafted+'">CREACIONES ('+items.length+')</button></div>';
      if(crafted) {
        if(items.length) {
          const item=items[ctx.selectedItem];
          details+=sheetForItem(ctx,item);
          viewer='<div class="workspaceHero">'+ctx.renderAsset(item)+'<p>'+escape(item.name)+' · '+escape(item.rarity)+'</p></div>';
          action='Comparar creaciones';enabled=items.length>1;
          run=()=>renderWorkspace('Comparacion');
        } else {
          details+='<div class="workspaceEmptyText">Todavía no hay objetos terminados. Cada fabricación aparecerá en estas casillas al cerrar su creación.</div>';
          viewer='<p class="workspaceViewEmpty">Tus creaciones aparecerán aquí</p>';
          action='Volver a materiales';enabled=true;run=()=>{ctx.inventoryCategory='materials';renderWorkspace('Inventario')};
        }
      } else if (!stock.length) {
        // Las casillas empiezan vacías; jamás exhibir recursos que no posee el jugador.
        details+='<div class="workspaceEmptyText">Todavía no hay materiales básicos ni preparados. Al recogerlos, aparecerán en estas casillas.</div>';
        if(ctx.manageGear)details+='<button type="button" class="workspaceMaterial" id="workspaceGear">Gestionar equipo del mercenario</button>';
        if(ctx.extraInventory)details+=ctx.extraInventory();
        viewer='<p class="workspaceViewEmpty">Casillas vacías · sin materiales</p>';
        action='Sin materiales';enabled=false;
      } else {
        details+='<h3>'+escape(material)+'</h3><p class="prepSkinIntro">Existencias del baúl y materiales preparados en la partida.</p>' +
          '<div class="prepSkinStat"><span>Disponibles</span><b>'+countOf(ctx.inventory,material)+'</b></div>' +
          '<p class="workspaceFootnote">Elegí un material directamente en las casillas del inventario para consultar sus existencias.</p>';
        if(ctx.manageGear)details+='<button type="button" class="workspaceMaterial" id="workspaceGear">Gestionar equipo del mercenario</button>';
        if(ctx.extraInventory)details+=ctx.extraInventory();
        viewer=materialVisual(material,'featured');
        action=isCraftMaterial(ctx,material)?'Ir a Fabricaciones':'Ir a Preparación';enabled=true;
        run=()=>{if(isCraftMaterial(ctx,material))renderWorkspace('Fabricaciones');else renderMenu()};
      }
    } else if(tab==='Fabricaciones') {
      // El repertorio es el conocimiento YA generado del personaje: el menú jamás llama a generateSession.
      const catalog = typeof ctx.getRecipeCatalog === 'function' ? ctx.getRecipeCatalog() : [];
      const hasCatalog = Array.isArray(catalog) && catalog.length > 0;
      const recipes = hasCatalog ? catalog.filter(entry => entry && entry.id && entry.family && entry.subfamily && entry.formula) : [];
      const availableIds = new Set(recipes.map(entry => String(entry.id)));
      if (!availableIds.has(String(ctx.selectedRecipeId))) ctx.selectedRecipeId =
        recipes.find(entry => String(entry.id) === String(ctx.activeRecipeId))?.id || recipes[0]?.id || null;
      const selected = recipes.find(entry => String(entry.id) === String(ctx.selectedRecipeId)) || null;
      const selectedFormula = selected ? selected.formula : ctx.formula;
      const selectedName = selected ? selected.subfamily : ctx.recipeName;
      const selectedId = selected?.id || null;
      const needs = shortages(selectedFormula, ctx.inventory);
      const canCraft = selected
        ? (typeof ctx.canCraftRecipe === 'function' ? ctx.canCraftRecipe(selectedId) === true : false)
        : (ctx.canCraftNow?.() === true && !hasCatalog);
      enabled = !!selectedFormula && ready(selectedFormula, ctx.inventory) && canCraft;
      if (hasCatalog) {
        const families = [...new Set(recipes.map(entry => entry.family))];
        details = '<p class="prepSkinKicker">CONOCIMIENTO DEL PERSONAJE</p>' +
          '<h3>Recetas del herrero</h3>' +
          '<div class="workspaceRecipeTree" role="group" aria-label="Familias y subfamilias conocidas">' +
          families.map(family => {
            const group = recipes.filter(entry => entry.family === family);
            return '<section class="workspaceRecipeFamily"><h4>' + escape(family) + '</h4>' +
              group.map(entry => '<button type="button" class="workspaceRecipeChoice" data-recipe-id="' + escape(entry.id) +
                '" aria-pressed="' + (String(entry.id) === String(selectedId)) + '">' + escape(entry.subfamily) + '</button>').join('') +
              '</section>';
          }).join('') + '</div>' +
          '<p class="workspaceRecipeSubhead">MATERIALES DE LA RECETA SELECCIONADA</p>';
      } else {
        details = '<p class="prepSkinKicker">RECETA DE LA PARTIDA</p><h3>' + escape(selectedName || 'Sin receta') + '</h3>' +
          '<p class="workspaceFootnote">Esta vista sólo consulta la receta guardada.</p>';
      }
      details += '<div class="workspaceIngredients">' +
        (needs.length ? needs.map(row => '<div class="workspaceMetric ' + (row.missing ? 'short' : 'met') + '">' +
          '<span>' + escape(row.material) + '</span><b>' + row.available + ' / ' + row.needed + '</b></div>').join('')
          : '<p class="workspaceFootnote">Todavía no hay una fórmula disponible.</p>') + '</div>' +
        '<p class="workspaceCraftState">' +
          (!canCraft ? 'Receta conocida. Su fabricación se habilita en la etapa correspondiente del recorrido.'
          : enabled ? 'Materiales disponibles. Podés fabricar esta receta.'
          : 'Faltan materiales preparados para esta receta.') + '</p>' +
        '<button type="button" class="prepSkinCraft secondary" id="workspaceGoPrep">Ver Preparación</button>';
      viewer = '<div class="workspaceHero workspaceRecipeHero">' +
        (ctx.recipeAsset ? ctx.recipeAsset(selectedId) : '') + '<p>' + escape(selectedName || 'Seleccioná una receta') + '</p></div>';
      action = 'Confirmar fabricación';
      run = craft;
    } else if(tab==='Comparacion') {
      ctx.compareA=Math.min(Math.max(0,ctx.compareA||0),Math.max(0,items.length-1));
      ctx.compareB=Math.min(Math.max(0,ctx.compareB??1),Math.max(0,items.length-1));
      const a=items[ctx.compareA],b=items[ctx.compareB];
      const valid=!!(a&&b&&a!==b&&a.recipe===b.recipe);
      details='<p class="prepSkinKicker">COMPARACIÓN DE CREACIONES REALES</p><h3>Dos cierres · una familia</h3>';
      if(items.length) {
        details+='<div class="workspaceSelectPair"><label>OBJETO A<select id="workspaceA">'+optionList(ctx.compareA)+'</select></label>' +
          '<label>OBJETO B<select id="workspaceB">'+optionList(ctx.compareB)+'</select></label></div>';
        if(valid) {
          const keys=[...new Set([...(a.channels||[]),...(b.channels||[])].map(c=>c[0]))];
          const fmt=(item,key)=>{const ix=(item.channels||[]).findIndex(c=>c[0]===key);if(ix<0)return '—';const ch=item.channels[ix];return ctx.metricForChannel?ctx.metricForChannel(item,ch,ix).display:String(ch[1])+(ix?'%':'')};
          details+='<div class="workspaceCompareHeader"><span>RESULTADO</span><b>A</b><b>B</b></div>' +
            '<div class="workspaceCompareRow"><span>Rareza</span><b>'+escape(a.rarity)+'</b><b>'+escape(b.rarity)+'</b></div>' +
            '<div class="workspaceCompareRow"><span>Canales</span><b>'+(a.channels||[]).length+'</b><b>'+(b.channels||[]).length+'</b></div>' +
            keys.map(key=>'<div class="workspaceCompareRow"><span>'+escape(key)+'</span><b>'+escape(fmt(a,key))+'</b><b>'+escape(fmt(b,key))+'</b></div>').join('') +
            '<p class="workspaceFootnote">Misma familia y fórmula de sesión. Cada cierre conserva sus valores propios.</p>';
        } else details+='<p class="workspaceCompareHint">Elegí dos objetos distintos de la misma familia para comparar sus canales.</p>';
        viewer=valid?'<div class="workspacePair"><div class="workspacePairA">'+ctx.renderAsset(a)+'<p>A · '+escape(a.name)+'</p></div><div class="workspacePairB">'+ctx.renderAsset(b)+'<p>B · '+escape(b.name)+'</p></div></div>':
          '<p class="workspaceViewEmpty">Elegí dos creaciones compatibles</p>';
      } else {
        details+='<p class="workspaceEmptyText">Todavía no fabricaste objetos. Acá aparecerán sus propiedades reales al cerrar al menos dos creaciones.</p>';
        viewer='<p class="workspaceViewEmpty">Sin creaciones para comparar</p>';
      }
      action=ctx.onComparisonContinue?'Continuar recorrido':'Volver al inventario';
      enabled=ctx.onComparisonContinue?valid:true;
      run=()=>{if(ctx.onComparisonContinue){const done=ctx.onComparisonContinue;close();done()}else{ctx.inventoryCategory='creations';renderWorkspace('Inventario')}};
    }
    skinDisplay('workspace','',details,tab+' · '+stock.reduce((n,[,q])=>n+Number(q),0)+' unidades · '+items.length+' creaciones');
    const board=document.querySelector('.prepArtboard');
    // Se preserva el botón decorativo, pero no el rótulo PREPARAR horneado en Preparación.
    board.querySelectorAll('[data-role^="boton_"]').forEach(piece => piece.remove());
    if(tab==='Comparacion'||(tab==='Inventario'&&ctx.inventoryCategory==='creations')) {
      const titles=['CREACIONES · 1–10','CREACIONES · 11–20'];
      titles.forEach((title,i)=>board.insertAdjacentHTML('beforeend','<div class="workspaceCollectionLabel '+(i?'lower':'upper')+'" aria-hidden="true"><span>✦</span>'+title+'<span>✦</span></div>'));
    }
    const view=document.createElement('div');view.className='workspaceViewer';view.innerHTML=viewer;board.append(view);
    // El visor grande es una imagen fija. El hover ya se conectó sólo a las casillas en skinDisplay().
    const button=document.getElementById('prepStart');button.classList.add('workspaceAction');button.innerHTML='<span class="workspaceActionLabel">'+escape(action)+'</span>';button.disabled=!enabled;button.onclick=run;
    board.querySelectorAll('[data-item-index]').forEach(e=>e.onclick=()=>{
      const index=Number(e.dataset.itemIndex);
      if(tab==='Comparacion') {if(ctx.comparePick==='B')ctx.compareB=index;else ctx.compareA=index;ctx.comparePick=ctx.comparePick==='B'?'A':'B';}
      else {ctx.inventoryCategory='creations';ctx.selectedItem=index;ctx.viewItem=true;}
      renderWorkspace(tab);
    });
    board.querySelectorAll('[data-stock-name]').forEach(e=>e.onclick=()=>{
      ctx.selectedMaterial=e.dataset.stockName;ctx.viewItem=false;ctx.inventoryCategory='materials';
      if(ctx.selectedMaterial===CHARCOAL)renderWorkspace('Inventario');
      else if(isCraftMaterial(ctx,ctx.selectedMaterial))renderWorkspace('Fabricaciones');
      else renderWorkspace('Inventario');
    });
    board.querySelectorAll('[data-recipe-id]').forEach(button => {
      button.onclick = () => {
        const catalog = typeof ctx.getRecipeCatalog === 'function' ? ctx.getRecipeCatalog() : [];
        const chosen = catalog.find(entry => String(entry.id) === button.dataset.recipeId);
        if (!chosen) return;
        ctx.selectedRecipeId = chosen.id;
        renderWorkspace('Fabricaciones');
      };
    });
    board.querySelectorAll('[data-inventory-category]').forEach(e=>e.onclick=()=>{ctx.inventoryCategory=e.dataset.inventoryCategory;ctx.viewItem=ctx.inventoryCategory==='creations';renderWorkspace('Inventario')});
    board.querySelectorAll('[data-material]').forEach(e=>{if(e.tagName==='BUTTON')e.onclick=()=>{ctx.selectedMaterial=e.dataset.material;renderWorkspace(ctx.selectedMaterial===CHARCOAL?'Inventario':isCraftMaterial(ctx,ctx.selectedMaterial)?'Fabricaciones':'Inventario')}});
    const select=document.getElementById('workspaceItem');if(select)select.onchange=()=>{ctx.selectedItem=Math.max(0,Number(select.value));ctx.inventoryCategory='creations';renderWorkspace('Inventario')};
    for(const [id,key] of [['workspaceA','compareA'],['workspaceB','compareB']]){const el=document.getElementById(id);if(el)el.onchange=()=>{ctx[key]=Number(el.value);ctx.comparePick=key==='compareA'?'B':'A';renderWorkspace('Comparacion')}}
    board.querySelectorAll('[data-sheet-tab]').forEach(e=>e.onclick=()=>{ctx.sheetTab=e.dataset.sheetTab;renderWorkspace('Inventario')});
    bind('workspaceGoPrep',renderMenu);
    bind('workspaceGear',()=>{const fn=ctx.manageGear;close();fn()});
    ctx.bindExtraInventory?.();
  }
  function display(content, compact = false) {
    const ctx = session;
    if (!ctx) return;
    ctx.modal(`<div class="prepRoot" id="prepRoot">
      <header class="prepMasthead"><div class="prepMark">✥</div><div><small>EL EQUILIBRIO TAMBIÉN CREA</small><h2>PROJECT GENESIS</h2><span>TALLER DEL ${escape(ctx.profession.toUpperCase())} · PREPARACIÓN</span></div><button class="prepClose" id="prepClose" aria-label="Cerrar menú">✕</button></header>
      ${content}<footer class="prepFoot"><span>PERFIL DE DEMOSTRACIÓN · SIN XP, PÉRDIDA DE MATERIALES NI MODIFICACIÓN DE RAREZA</span><span>ESC para cerrar · 1/2/3 fuelle · sin pulsar: enfriar</span></footer>
    </div>`, compact ? 'preparationModal preparationCompact' : 'preparationModal');
    bind('prepClose', close);
  }

  function renderLegacyMenu() {
    const ctx = session;
    if (!ctx) return;
    halt();
    ctx.mode = 'menu';
    const raw = countOf(ctx.inventory, RAW), iron = countOf(ctx.inventory, PREPARED), max = countOf(ctx.requiredStock, PREPARED);
    ctx.count = raw ? Math.min(Math.max(ctx.count || 1, 1), raw) : 0;
    const shortage = shortages(ctx.formula, ctx.inventory), canCraft = ready(ctx.formula, ctx.inventory);
    const currentNeeds = shortage.map(row => `<div class="prepNeed ${row.missing ? 'short' : 'met'}"><span>${escape(row.material)}</span><strong>${row.available} / ${row.needed}</strong></div>`).join('');
    const batch = raw ? batchProfile(ctx.count) : null;
    const materialPanel = ctx.profession === 'Herrero' ? `<div class="prepMaterials"><button class="prepMaterial selected" id="prepSelectIron" ${raw ? '' : 'disabled'}><span class="prepMaterialIcon">◆</span><span><b>${PREPARED}</b><small>Desde ${RAW} · fundición</small></span><span class="prepMaterialCount"><strong>${raw}</strong> en bruto<br><em>${iron} preparado${iron !== 1 ? 's' : ''}</em></span></button></div>`
      : `<div class="prepNotice">El proceso térmico de lingotes corresponde al Herrero. Esta ruta conserva sus materiales de sesión; no se inventó un minijuego de fuelle para Curtidor.</div>`;
    const preview = raw && ctx.profession === 'Herrero' ? `<div class="prepSelectedSymbol">◆</div><p class="prepEy">MINERAL → LINGOTE</p><h3>Fundición de hierro</h3><p class="prepSub">Regulá el calor con tres intensidades de fuelle; soltá para enfriar. La barra avanza según la cercanía al punto ideal, no al pulsar.</p><div class="prepBalance"><span>En bruto<b>${raw}</b></span><span>Preparados<b>${iron}</b></span><span>Total de sesión<b>${max}</b></span></div><div class="prepQuantity"><span>Cantidad de la tanda</span><div><button id="prepLess" aria-label="Reducir cantidad" ${ctx.count <= 1 ? 'disabled' : ''}>−</button><strong>${ctx.count}</strong><button id="prepMore" aria-label="Aumentar cantidad" ${ctx.count >= raw ? 'disabled' : ''}>+</button></div></div><p class="prepBatchInfo">Dificultad relativa: <strong>${Math.round(batch.difficultyMultiplier * 100)} %</strong> · Tolerancia térmica ${batch.tolerance.toFixed(1)} puntos.</p><button class="prepPrimary" id="prepStart">INICIAR TANDA DE ${ctx.count} LINGOTE${ctx.count === 1 ? '' : 'S'}</button>`
      : `<div class="prepSelectedSymbol">✓</div><h3>${ctx.profession === 'Herrero' ? 'No quedan minerales por preparar' : 'Ruta de fabricación disponible'}</h3><p class="prepSub">${ctx.profession === 'Herrero' ? 'Todos los lingotes de esta sesión ya se procesaron.' : 'El sistema térmico del Herrero se encuentra separado de esta profesión.'}</p>`;
    display(`<nav class="prepTabs" aria-label="Menú de trabajo"><span class="prepTab active">PREPARACIÓN</span><button id="prepFabricateTab" class="prepTab ${canCraft ? 'available' : ''}" ${canCraft ? '' : 'disabled'}>FABRICACIÓN ${canCraft ? '↗' : '🔒'}</button><button class="prepTab locked" disabled>REFINAMIENTO 🔒</button><button class="prepTab locked" disabled>FUSIONES 🔒</button></nav>
      <div class="prepColumns"><section class="prepPanel prepList"><h3>MATERIALES</h3><p>El inventario distingue materia prima y material preparado. Las fórmulas permanecen intactas.</p>${materialPanel}</section><section class="prepPanel prepScene"><div class="prepSceneTop"><span>FRAGUA · CONTROL TÉRMICO</span><span>VISTA DE DEMO</span></div>${preview}</section><section class="prepPanel prepRequirement"><h3>${escape(ctx.recipeName)}</h3><p>Materiales requeridos para la próxima fabricación.</p><div class="prepChecklist">${currentNeeds}</div><div class="prepStatus ${canCraft ? 'ready' : ''}">${canCraft ? '✓ FÓRMULA COMPLETA' : '◌ PREPARAR MATERIALES'}</div><button class="prepPrimary" id="prepFabricate" ${canCraft ? '' : 'disabled'}>FABRICAR</button><p class="prepNotice">Ni la cantidad de la tanda ni la habilidad térmica modifican el cierre procedural del objeto.</p></section></div>`);
    bind('prepLess', () => { ctx.count = Math.max(1, ctx.count - 1); renderMenu(); });
    bind('prepMore', () => { ctx.count = Math.min(raw, ctx.count + 1); renderMenu(); });
    bind('prepStart', start);
    bind('prepFabricate', craft);
    bind('prepFabricateTab', craft);
  }

  function renderMenu() {
    const ctx = session;
    if (!ctx) return;
    if (ctx.profession !== 'Herrero') { renderLegacyMenu(); return; }
    if(ctx.getItems){
      const raw=countOf(ctx.inventory,RAW);
      ctx.count=raw?Math.min(Math.max(ctx.count||1,1),raw):0;
      if(window.GenesisApprovedUI?.render){
        halt();ctx.mode='menu';ctx.tab='Preparacion';
        window.GenesisApprovedUI.render(ctx,approvedUiNav(),'Preparacion');
        return;
      }
      if(approvedUiLoadState!=='failed'){
        loadApprovedUi(renderMenu);
        return;
      }
    }
    halt();
    ctx.mode = 'menu';ctx.tab='Preparacion';
    const raw = countOf(ctx.inventory, RAW), ingots = countOf(ctx.inventory, PREPARED);
    ctx.count = raw ? Math.min(Math.max(ctx.count || 1, 1), raw) : 0;
    const batch = raw ? batchProfile(ctx.count, PREPARED) : null;
    const missing = shortages(ctx.formula, ctx.inventory);
    const canCraft = ready(ctx.formula, ctx.inventory);
    const craftAllowed = canCraft && (typeof ctx.canCraftNow !== 'function' || ctx.canCraftNow());
    const details = `<p class="prepSkinKicker">TALLER DEL HERRERO</p>
      <h3>Fundición de hierro</h3>
      <p class="prepSkinIntro">Transformá el mineral en lingotes antes de fabricar. Cada tanda se completa al llegar a 100.</p>
      <div class="prepSkinStat"><span>Mineral de hierro</span><b>${raw}</b></div>
      <div class="prepSkinStat"><span>Lingotes disponibles</span><b>${ingots}</b></div>
      <div class="prepSkinQty"><label>Cantidad del lote</label><div><button id="prepLess" aria-label="Reducir cantidad de lingotes" ${ctx.count <= 1 ? 'disabled' : ''}>−</button><b>${ctx.count}</b><button id="prepMore" aria-label="Aumentar cantidad de lingotes" ${ctx.count >= raw ? 'disabled' : ''}>+</button></div></div>
      <p class="prepSkinMinor">${batch ? `Dificultad relativa: ${Math.round(batch.difficultyMultiplier * 100)} %. A más mineral, mayor exigencia térmica.` : 'No queda mineral de hierro sin preparar.'}</p>
      <div class="prepSkinDivider"></div>
      <p class="prepSkinKicker">PRÓXIMA FABRICACIÓN</p>
      <h4>${escape(ctx.recipeName)}</h4>
      ${missing.map(row => `<div class="prepSkinNeed ${row.missing ? 'short' : 'met'}"><span>${escape(row.material)}</span><b>${row.available}/${row.needed}</b></div>`).join('')}
      <p class="prepSkinReady">${canCraft ? '✓ Materiales listos para fabricar.' : 'Prepará los materiales que requiere la fórmula.'}</p>
      ${craftAllowed ? '<button class="prepSkinCraft" id="prepFabricate">Ir a fabricar →</button>' : ''}`;
    // Las instrucciones están en el panel derecho; el centro queda libre
    // para la pieza final estática y los materiales necesarios debajo.
    const center = '';
    skinDisplay('menu', center, details, `En bruto: ${raw} · preparados: ${ingots} · la preparación no modifica rareza ni receta`);
    bind('prepLess', () => { ctx.count = Math.max(1, ctx.count - 1); renderMenu(); });
    bind('prepMore', () => { ctx.count = Math.min(raw, ctx.count + 1); renderMenu(); });
    bind('prepStart', start);
    bind('prepFabricate', craft);
  }

  function craft() {
    const ctx = session;
    if (!ctx) return;
    const catalog = typeof ctx.getRecipeCatalog === 'function' ? ctx.getRecipeCatalog() : [];
    if (Array.isArray(catalog) && catalog.length) {
      const selected = catalog.find(entry => String(entry.id) === String(ctx.selectedRecipeId));
      if (!selected || !ready(selected.formula, ctx.inventory) ||
          typeof ctx.canCraftRecipe !== 'function' || ctx.canCraftRecipe(selected.id) !== true ||
          typeof ctx.onCraftRecipe !== 'function') return;
      halt();
      session = null;
      document.removeEventListener('keydown', onKeyDown, true);
      ctx.onCraftRecipe(selected.id);
      return;
    }
    if (!ready(ctx.formula, ctx.inventory) || (typeof ctx.canCraftNow === 'function' && !ctx.canCraftNow())) return;
    halt();
    session = null;
    document.removeEventListener('keydown', onKeyDown, true);
    ctx.onCraft();
  }

  function start() {
    const ctx = session;
    if (!ctx || ctx.profession !== 'Herrero' || !whole(ctx.count) || ctx.count > countOf(ctx.inventory, RAW)) return;
    const batch = batchProfile(ctx.count, PREPARED), target = batch.target;
    ctx.mode = 'running';
    ctx.work = { count: ctx.count, batch, target, temperature: Math.max(0, target - batch.initialGap), progress: 0, clicks: 0, done: false };
    renderThermalSkin();
  }

  function intervene(action) {
    const ctx = session, work = ctx?.work;
    if (!ctx || ctx.mode !== 'running' || !work || work.done) return false;
    passiveStep(); // Primero liquidar el avance térmico acumulado, sin premios por clic.
    if (work.done || ctx.mode !== 'running') return false;
    const result = actionEffect(work.temperature, work.target, work.batch, action);
    work.temperature = result.temperature;
    work.clicks++;
    drawThermal();
    return true;
  }

  function drawThermal() {
    const ctx = session, work = ctx?.work;
    if (!ctx || !work || ctx.mode !== 'running') return;
    const temperature = Math.max(0, Math.min(100, work.temperature));
    const status = temperatureStatus(temperature, work.target, work.batch.tolerance);
    const needle = document.getElementById('prepHeatNeedle');
    const gauge = document.getElementById('prepHeatGauge');
    const number = document.getElementById('prepHeatNumber');
    const message = document.getElementById('prepHeatMessage');
    const progress = document.getElementById('prepCraftProgress');
    const progressText = document.getElementById('prepCraftNumber');
    const clicksText = document.getElementById('prepActions');
    const pointsText = document.getElementById('prepActionPoints');
    if (needle) { needle.style.left = `${temperature}%`; needle.dataset.tone = status.tone; }
    if (gauge) { gauge.setAttribute('aria-valuenow', String(Math.round(temperature))); gauge.setAttribute('aria-valuetext', status.message); }
    if (number) number.textContent = `${Math.round(temperature)} / 100`;
    if (message) { message.textContent = status.message; message.dataset.tone = status.tone; }
    if (progress) { progress.style.width = `${Math.min(100, work.progress)}%`; progress.setAttribute('aria-valuenow', work.progress.toFixed(2)); }
    if (progressText) progressText.textContent = `${work.progress.toFixed(1)} / 100`;
    if (clicksText) clicksText.textContent = String(work.clicks);
    if (pointsText) {
      const effectiveness = progressRate(temperature, work.target, work.batch.tolerance);
      pointsText.textContent = effectiveness === 0
        ? '● AVANCE DETENIDO · demasiado frío o caliente.'
        : `● EFICIENCIA TÉRMICA ${(effectiveness * 100).toFixed(1)} % · el avance crece cuanto más cerca del centro verde.`;
      pointsText.dataset.tone = status.tone;
    }
  }

  function renderThermalSkin() {
    const ctx = session, work = ctx?.work;
    if (!ctx || !work) return;
    halt();
    work.lastThermalAt = performance.now();
    const gradient = heatGradient(work.target, work.batch.tolerance);
    // V014.026: embed thermal controls in the approved 16:9 Preparación board.
    // Retain legacy skin only as fallback for older standalone previews.
    if(ctx.getItems && window.GenesisApprovedUI?.renderThermal){
      window.GenesisApprovedUI.renderThermal(ctx,approvedUiNav(),{
        gradient, bellows:BELLOWS, intervene, abandon:renderMenu
      });
      drawThermal();
      thermalTimer=setInterval(passiveStep,THERMAL_TICK_MS);
      return;
    }
    const center = `<section class="prepSkinHeatWindow">
      <h3>Control de la fragua</h3>
      <p>Mantené la temperatura cerca del verde. Cuanto más te alejás, menos avanza la preparación.</p>
      <div class="prepSkinHeatGauge" id="prepHeatGauge" role="meter" aria-label="Temperatura de la fragua" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(work.temperature)}" style="background:${gradient}">
        <span class="prepHeatTarget" style="left:${work.target}%" aria-hidden="true"></span>
        <span class="prepHeatNeedle" id="prepHeatNeedle" aria-hidden="true"></span>
      </div>
      <div class="prepSkinHeatEnds"><span>AZUL · FRÍO</span><span>VERDE · IDEAL</span><span>NARANJA · EXCESO</span></div>
      <div class="prepSkinProgressTitle"><span>AVANCE DE PREPARACIÓN</span><b id="prepCraftNumber">0.0 / 100</b></div>
      <div class="prepSkinProgressBar"><span id="prepCraftProgress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-label="Avance de preparación"></span></div>
      <p class="prepSkinDirections">El progreso aumenta mientras la fragua permanece en temperatura útil; no hay límite de tiempo.</p>
      <div class="prepSkinBellowButtons">${BELLOWS.map((power, index) => `<button id="prepBellow${index}" aria-label="Fuelle ${power.label.toLowerCase()}"><b>${power.label}</b><small>${power.description}</small><em>${power.key}</em></button>`).join('')}</div>
      <p class="prepSkinCooling">Sin pulsar, la temperatura baja naturalmente.</p>
    </section>`;
    const details = `<p class="prepSkinKicker">PREPARACIÓN EN CURSO</p><h3>Mineral de hierro</h3>
      <div class="prepSkinStat"><span>Lote</span><b>${work.count}</b></div>
      <div class="prepSkinStat"><span>Dificultad</span><b>${Math.round(work.batch.difficultyMultiplier * 100)} %</b></div>
      <div class="prepSkinStat"><span>Temperatura</span><b id="prepHeatNumber">${Math.round(work.temperature)} / 100</b></div>
      <div class="prepSkinStat"><span>Punto ideal</span><b>${Math.round(work.target)} / 100</b></div>
      <div class="prepSkinStat"><span>Intervenciones</span><b id="prepActions">0</b></div>
      <p class="prepSkinHeatMessage" id="prepHeatMessage" aria-live="polite">Acercá la línea blanca al centro verde.</p>
      <p class="prepSkinEffectiveness" id="prepActionPoints">El avance se calcula continuamente, no por golpe.</p>
      <div class="prepSkinDivider"></div>
      <button class="prepSkinCraft" id="prepAbandon">Cancelar tanda sin consumir mineral</button>`;
    skinDisplay('running', center, details, '1/2/3: intensidad del fuelle · sin pulsar: reposo · progreso 0–100');
    BELLOWS.forEach((power, index) => bind(`prepBellow${index}`, () => intervene(power.key)));
    bind('prepAbandon', renderMenu);
    drawThermal();
    thermalTimer = setInterval(passiveStep, THERMAL_TICK_MS);
  }

  function renderThermal() {
    const ctx = session, work = ctx?.work;
    if (!ctx || !work) return;
    halt();
    work.lastThermalAt = performance.now();
    const gradient = heatGradient(work.target, work.batch.tolerance);
    display(`<div class="prepThermal"><div class="prepThermalHeading"><div><p class="prepEy">MINIJUEGO · PREPARACIÓN DE MATERIALES</p><h3>Control de la fragua</h3><p>${work.count}× ${PREPARED} · mantené el calor en la franja de trabajo para completar la barra.</p></div><div class="prepThermalBatch">TANDA: ${work.count} · DIFICULTAD ${Math.round(work.batch.difficultyMultiplier * 100)}%</div></div>
      <section class="prepThermalStage"><div class="prepFireVisual"><div class="prepFireIcon" aria-hidden="true">♨</div><span>FRAGUA · DEMOSTRACIÓN</span></div><div class="prepThermalReadouts"><div class="prepReadout"><span>TEMPERATURA ACTUAL</span><strong id="prepHeatNumber">${Math.round(work.temperature)} / 100</strong></div><div class="prepReadout"><span>PUNTO IDEAL DEL MATERIAL</span><strong>${Math.round(work.target)} / 100</strong></div><div class="prepReadout"><span>INTERVENCIONES</span><strong id="prepActions">0</strong></div></div><div class="prepHeatGauge" id="prepHeatGauge" role="meter" aria-label="Temperatura de la fragua" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(work.temperature)}" style="background:${gradient}"><span class="prepHeatTarget" style="left:${work.target}%" aria-hidden="true"></span><span class="prepHeatNeedle" id="prepHeatNeedle" aria-hidden="true"></span></div><div class="prepHeatLegend" aria-label="Significado de los colores"><span><i class="cold"></i>AZUL · FRÍO</span><span><i class="near"></i>AMARILLO · AJUSTE</span><span><i class="good"></i>VERDE · IDEAL</span><span><i class="hot"></i>NARANJA · EXCESO</span></div><div class="prepHeatMessage" id="prepHeatMessage" aria-live="polite">Acercá la línea blanca al centro verde.</div><p>El degradado muestra cómo cambia la eficiencia. La línea blanca es el calor actual; la marca fija señala el objetivo del material. Al no pulsar nada la fragua se enfría sola.</p></section>
      <section class="prepThermalControls"><h4>INTERVENÍ SOBRE LA FRAGUA</h4><p>Tres intensidades de fuelle para subir el calor. Soltá los controles para dejarlo bajar. El avance es máximo en el centro verde, disminuye gradualmente hacia amarillo y se detiene en azul o naranja. Cada material tendrá su propio comportamiento térmico.</p><div class="prepBellowButtons">${BELLOWS.map((power, index) => `<button id="prepBellow${index}" class="prepBellow"><b>${power.label}</b><small>${power.description}</small><span>TECLA ${power.key}</span></button>`).join('')}</div></section>
      <section class="prepThermalProgress"><div class="prepThermalProgressTitle"><strong>AVANCE DE PREPARACIÓN</strong><b id="prepCraftNumber">0.0 / 100</b></div><div class="prepProgressBar"><span id="prepCraftProgress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-label="Avance de preparación"></span></div><p id="prepActionPoints">La barra avanzará cuando la fragua entre en el rango de trabajo.</p><p>El avance nunca retrocede. Llegar a 100 completa la preparación; las intervenciones no otorgan puntos por sí mismas ni modifican el futuro objeto.</p></section><div class="prepGameActions"><button id="prepAbandon" class="secondary">Cancelar tanda sin consumir mineral</button></div></div>`, false);
    BELLOWS.forEach((power, index) => bind(`prepBellow${index}`, () => intervene(power.key)));
     bind('prepAbandon', renderMenu);
    drawThermal();
    thermalTimer = setInterval(passiveStep, THERMAL_TICK_MS);
  }

  function renderResultSkin(ctx, work, success) {
    // On current game sessions keep using the approved 16:9 preparation board.
    // Legacy 1536x1024 result mode has stale model-viewer slots and hides posters.
    if(ctx.getItems && window.GenesisApprovedUI?.renderResult){
      window.GenesisApprovedUI.renderResult(ctx, approvedUiNav(), {
        work, success, back:renderMenu, close
      });
      return;
    }

    const raw = countOf(ctx.inventory, RAW), ingots = countOf(ctx.inventory, PREPARED);
    const center = `<section class="prepSkinResultBox"><div class="prepSkinResultIcon">${success ? '✓' : '!'}</div>
      <h3>${success ? 'Preparación completada' : 'Lote no aplicado'}</h3>
      <p>${success ? `${work.count} lingote${work.count === 1 ? '' : 's'} incorporado${work.count === 1 ? '' : 's'} al inventario.` : 'El inventario cambió durante el proceso. No se descontó mineral.'}</p>
      <p>La fabricación conserva su fórmula y resolución procedural.</p></section>`;
    const details = `<p class="prepSkinKicker">RESULTADO DE LA TANDA</p><h3>${success ? 'Lingotes preparados' : 'Preparación interrumpida'}</h3>
      <div class="prepSkinStat"><span>Mineral restante</span><b>${raw}</b></div>
      <div class="prepSkinStat"><span>Lingotes listos</span><b>${ingots}</b></div>
      <div class="prepSkinStat"><span>Intervenciones</span><b>${work.clicks}</b></div>
      <div class="prepSkinDivider"></div>
      <button id="prepResultBack" class="prepSkinCraft">Volver a Preparación</button>
      <button id="prepResultClose" class="prepSkinCraft secondary">Cerrar menú</button>`;
    skinDisplay('result', center, details, 'Tanda completada · los materiales preparados están disponibles para Fabricación');
    bind('prepResultBack', renderMenu);
    bind('prepResultClose', close);
  }

  function finish() {
    const ctx = session, work = ctx?.work;
    if (!ctx || !work || work.done) return;
    work.done = true;
    halt();
    const success = convert(ctx.inventory, work.count);
    if (success) ctx.onInventoryChanged?.();
    ctx.mode = 'result';
    if (ctx.profession === 'Herrero') { renderResultSkin(ctx, work, success); return; }
    display(`<div class="prepResult"><div class="prepResultSymbol">${success ? '✓' : '!'}</div><p class="prepEy">${success ? 'PREPARACIÓN COMPLETADA' : 'LOTE NO APLICADO'}</p><h3>${work.count}× ${PREPARED}</h3><p>${success ? 'Los lingotes se incorporaron al inventario. La fórmula procedural y sus futuros resultados permanecen intactos.' : 'El inventario cambió durante el proceso. No se descontó material.'}</p><div class="prepBalance"><span>Mineral restante<b>${countOf(ctx.inventory, RAW)}</b></span><span>Lingotes listos<b>${countOf(ctx.inventory, PREPARED)}</b></span><span>Intervenciones<b>${work.clicks}</b></span></div><div class="prepGameActions"><button id="prepResultClose" class="secondary">Cerrar</button><button id="prepResultBack" class="prepPrimary">Volver al menú del taller</button></div></div>`, false);
    bind('prepResultClose', close);
    bind('prepResultBack', renderMenu);
  }

  function onKeyDown(event) {
    const ctx = session;
    if (!ctx) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      event.stopImmediatePropagation();
      if (ctx.mode === 'running') renderMenu();
      else close();
      return;
    }
    if (ctx.mode === 'running' && /^[123]$/.test(event.key)) {
      event.preventDefault();
      event.stopImmediatePropagation();
      intervene(event.key);
    }
  }

  function open(options) {
    if (!options || typeof options.modal !== 'function' || typeof options.closeModal !== 'function' || typeof options.onCraft !== 'function' || !options.inventory || !options.formula || !options.requiredStock) throw new Error('Preparación: faltan datos del taller');
    if (session) close();
    session = { ...options, mode: 'menu', count: 1, work: null };
    document.addEventListener('keydown', onKeyDown, true);
    if(options.startTab&&options.startTab!=='Preparacion'&&options.getItems)renderWorkspace(options.startTab);else renderMenu();
  }

  // Navegación explícita para TAB/INV del juego; no confundir una sesión abierta con su pestaña activa.
  function activeTab(){return session?.getItems ? (session.tab || 'Preparacion') : null;}
  function navigate(tab){
    if (!session?.getItems || session.mode === 'running' || !['Inventario','Preparacion','Fabricaciones','Comparacion'].includes(tab)) return false;
    if (tab === 'Preparacion') renderMenu(); else renderWorkspace(tab);
    return true;
  }
  window.GenesisPreparation = Object.freeze({ dismiss(){halt();session=null;document.removeEventListener('keydown',onKeyDown,true)}, activeTab, navigate, rawStock, shortages, ready, batchProfile, actionEffect, progressRate, progressGain, temperatureStatus, heatBands, heatGradient, passiveCooling, convert, open });
})();

