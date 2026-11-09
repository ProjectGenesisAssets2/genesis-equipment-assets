/* One sample per completed PlayCanvas render, not the separate gameplay loop.
   Display cadence is 1s. Milliseconds describe frame spacing, not GPU time. */
(() => {
  'use strict';
  const attached = new WeakSet();
  function attach(app, badge) {
    if (!app || !badge || attached.has(app)) return;
    attached.add(app);
    let previous = null, elapsed = 0, frames = 0;
    badge.classList.add('fpsCounter');
    badge.title = 'FPS renderizados · promedio del último segundo. ms: intervalo medio entre cuadros; no es tiempo de GPU.';
    function reset() {
      previous = null; elapsed = 0; frames = 0;
      badge.textContent = document.hidden ? 'FPS · pausa' : '— FPS';
    }
    function sample() {
      if (document.hidden) return;
      const now = performance.now();
      if (previous !== null) {
        elapsed += now - previous;
        frames++;
        if (elapsed >= 1000) {
          const fps = frames * 1000 / elapsed;
          badge.textContent = `${Math.round(fps)} FPS · ${(elapsed / frames).toFixed(1).replace('.', ',')} ms`;
          elapsed = 0; frames = 0;
        }
      }
      previous = now;
    }
    reset();
    app.on('postrender', sample);
    document.addEventListener('visibilitychange', reset);
    app.once('destroy', () => {
      app.off('postrender', sample);
      document.removeEventListener('visibilitychange', reset);
      attached.delete(app);
    });
  }
  window.GenesisFPS = Object.freeze({ attach });
})();
