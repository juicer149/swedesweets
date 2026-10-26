/* Motion is independent of palette. Night deliberately shares today's profile;
   replace its entry when a dedicated night effect is designed. Load before
   home-arrival so cross-document travel can opt in before first paint. */
(() => {
  "use strict";
  const root = document.documentElement;
  const shared = Object.freeze({ navigation: "cloud", travel: "cloud", celebration: "candy-rain" });
  const profiles = Object.freeze({ light: shared, dark: shared });
  const profile = () => profiles[root.dataset.theme] || shared;
  function sync() {
    root.dataset.motionProfile = profile().navigation;
    root.dataset.celebrationProfile = profile().celebration;
  }
  window.SwedeSweetsEffects = Object.freeze({ profile });
  sync();
  new MutationObserver(sync).observe(root, { attributes: true, attributeFilter: ["data-theme"] });
})();
