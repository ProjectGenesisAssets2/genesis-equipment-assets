/* Project Genesis · mercado v001. Pura logica, sin precios ni objetos ajenos a la semilla. */
(function (root) {
  'use strict';

  function catalog(session, toRawStock) {
    if (!session || !session.profession || !session.formulas ||
        typeof toRawStock !== 'function') return [];
    const needed = Object.create(null);
    for (const formula of Object.values(session.formulas)) {
      if (!formula || !Array.isArray(formula.materials)) continue;
      for (const part of formula.materials) {
        if (!part || typeof part.material !== 'string' ||
            !Number.isSafeInteger(part.qty) || part.qty <= 0) continue;
        needed[part.material] = (needed[part.material] || 0) + part.qty;
      }
    }
    // El conversor del inventario del juego convierte Lingote de hierro en
    // Mineral de hierro. No se venden materiales preparados por accidente.
    const raw = toRawStock(needed);
    if (!raw || typeof raw !== 'object') return [];
    return Object.keys(raw).filter(function (name) {
      return Object.prototype.hasOwnProperty.call(raw, name) &&
        Number.isFinite(raw[name]) && raw[name] > 0;
    }).sort(function (a,b) { return a.localeCompare(b, 'es'); });
  }

  function buy(options) {
    const session = options && options.session;
    const inventory = options && options.inventory;
    const material = options && options.material;
    const quantity = options && options.quantity;
    const names = catalog(session, options && options.toRawStock);
    if (typeof material !== 'string' || !names.includes(material)) {
      return { ok: false, reason: 'not_known_in_initial_seed' };
    }
    if (!Number.isSafeInteger(quantity) || quantity < 1 || quantity > 99) {
      return { ok: false, reason: 'invalid_quantity' };
    }
    if (!inventory || typeof inventory !== 'object') {
      return { ok: false, reason: 'inventory_unavailable' };
    }
    const previous = Number(inventory[material] || 0);
    if (!Number.isSafeInteger(previous) || previous < 0 ||
        !Number.isSafeInteger(previous + quantity)) {
      return { ok: false, reason: 'invalid_stock' };
    }
    inventory[material] = previous + quantity;
    return { ok: true, material: material, quantity: quantity,
      before: previous, after: inventory[material], cost: 0 };
  }

  const api = Object.freeze({ version: 'MARKET_DOMAIN_V001', catalog: catalog, buy: buy });
  root.GenesisMarketDomain = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window === 'undefined' ? globalThis : window);
