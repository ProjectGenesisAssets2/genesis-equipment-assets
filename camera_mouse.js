/* Relative mouse input for windowed desktop play. Touchpad and touch controls
   stay in their existing input paths. Capture always requires a mouse gesture. */
(() => {
  'use strict';
  function create({ surface, hud, allowed, blocked, mode, rotate, stopped, changed, failed }) {
    const supported = typeof surface.requestPointerLock === 'function';
    const hint = document.createElement('button');
    hint.id = 'mouseCaptureHint';
    hint.textContent = 'Clic para controlar la cámara · Esc libera el mouse';
    hint.type = 'button';
    hud.append(hint);
    let pending = false, held = false, wantsCapture = false;
    const locked = () => document.pointerLockElement === surface;
    function refresh() {
      if (!allowed()) release();
      hint.hidden = !supported || !allowed() || locked() || mode() === 'drag';
      changed?.(locked());
    }
    function release() {
      wantsCapture = false;
      held = false;
      if (locked()) document.exitPointerLock();
    }
    function error() {
      pending = false;
      wantsCapture = false;
      held = false;
      refresh();
      failed?.();
    }
    function request() {
      if (!supported || !allowed() || pending || locked()) return;
      pending = true;
      wantsCapture = true;
      try {
        const result = surface.requestPointerLock();
        // Older browsers signal errors via pointerlockerror only.
        result?.catch?.(() => { if (pending) error(); });
      } catch (_) { error(); }
    }
    document.addEventListener('pointerdown', event => {
      if (event.pointerType !== 'mouse' || !allowed() || blocked(event)) return;
      if ((mode() === 'drag' && event.button !== 2) || (mode() !== 'drag' && event.button !== 0)) return;
      held = true;
      request();
    });
    hint.addEventListener('click', request);
    document.addEventListener('mousemove', event => {
      if (!locked() || !allowed() || blocked(event) || (mode() === 'drag' && !held)) return;
      rotate(event.movementX || 0, event.movementY || 0);
    });
    document.addEventListener('pointerup', event => {
      if (event.pointerType === 'mouse' && event.button === 2 && mode() === 'drag') release();
    });
    document.addEventListener('pointerlockchange', () => {
      pending = false;
      if (locked() && (!wantsCapture || !allowed())) { release(); return; }
      if (!locked()) { wantsCapture = false; held = false; stopped?.(); }
      refresh();
    });
    document.addEventListener('pointerlockerror', () => { if (pending) error(); });
    addEventListener('blur', release);
    addEventListener('pagehide', release);
    document.addEventListener('visibilitychange', () => { if (document.hidden) release(); });
    refresh();
    return Object.freeze({ refresh, release, locked, supported });
  }
  window.GenesisMouseCapture = Object.freeze({ create });
})();
