/* Motion is independent of palette. Night shares navigation motion but travels without day cloud art;
   its celebration stays disabled until a dedicated effect is designed. Load before
   home-arrival so cross-document travel can opt in before first paint. */
(() => {
  "use strict";
  const root = document.documentElement;
  const shared = Object.freeze({ navigation: "cloud", travel: "cloud", celebration: "candy-rain" });
  const night = Object.freeze({ navigation: "cloud", travel: "wordmark", celebration: "none" });
  const profiles = Object.freeze({ light: shared, dark: night });
  const profile = () => profiles[root.dataset.theme] || shared;
  function sync() {
    root.dataset.motionProfile = profile().navigation;
    root.dataset.celebrationProfile = profile().celebration;
  }
  window.SwedeSweetsEffects = Object.freeze({ profile });
  sync();
  new MutationObserver(sync).observe(root, { attributes: true, attributeFilter: ["data-theme"] });
})();
