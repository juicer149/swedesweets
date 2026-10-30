/* Geometry belongs to the travel/panel controllers. This shared decoration
   keeps pointer feedback during travel, then swells into the selected state. */
(() => {
  "use strict";
  const versions = new WeakMap();
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  function clear(element) {
    if (!element) return;
    versions.set(element, {});
    delete element.dataset.navSelected;
    element.classList.remove("is-nav-travelling", "is-nav-arriving");
  }
  function hold(element) {
    clear(element);
    element?.classList.add("is-nav-travelling");
  }
  async function arrive(element, { retain = false } = {}) {
    if (!element) return;
    clear(element);
    element.dataset.navSelected = "";
    if (reduced.matches) return;
    const version = {}; versions.set(element, version);
    element.classList.add("is-nav-arriving");
    const effects = element.getAnimations({ subtree: true }).filter(animation =>
      /^nav-(arrival|cloud-pop|crown-pop)/.test(animation.animationName || "")
    );
    await Promise.all(effects.map(effect => effect.finished.catch(() => {})));
    if (!retain && versions.get(element) === version) element.classList.remove("is-nav-arriving");
  }
  async function movement(element) {
    if (!element || reduced.matches) return;
    // getAnimations flushes the just-applied destination style. Waiting for
    // its actual translate avoids a guessed timeout or a second position owner.
    // Opening a sheet can cause a second layout sync. Re-check after a
    // cancelled/replaced transition rather than treating cancellation as arrival.
    do {
      await new Promise(resolve => requestAnimationFrame(resolve));
      const effects = element.getAnimations().filter(animation =>
        animation.transitionProperty === "translate" && animation.playState !== "finished"
      );
      if (!effects.length) return;
      await Promise.all(effects.map(effect => effect.finished.catch(() => {})));
    } while (element.isConnected && !reduced.matches);
  }
  window.SwedeSweetsNavArrival = { hold, arrive, clear, movement };
})();
