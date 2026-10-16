/* Resolve the customer palette before CSS loads. Light is the default.
 * ?theme=light|dark|auto previews a palette for this tab and its navigation.
 * Auto follows Paris time (06–22 light). Ops stays light during rollout.
 */
(() => {
  "use strict";
  const root = document.documentElement;
  const modes = new Set(["light", "dark", "auto"]);
  const storageKey = "swedesweets-theme-preview";
  const requested = new URLSearchParams(window.location.search).get("theme");
  let saved = null;
  try {
    saved = sessionStorage.getItem(storageKey);
    if (modes.has(requested)) sessionStorage.setItem(storageKey, requested);
  } catch {
    // Explicit previews also work when storage is unavailable.
  }
  const mode = modes.has(requested) ? requested
    : modes.has(saved) ? saved
    : modes.has(root.dataset.theme) ? root.dataset.theme : "light";

  if (root.dataset.siteZone === "ops") {
    root.dataset.theme = "light";
    return;
  }
  root.dataset.themeMode = mode;
  if (mode !== "auto") {
    root.dataset.theme = mode;
    return;
  }

  const clock = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Paris", hour: "2-digit", hourCycle: "h23",
  });
  let appliedTheme;
  function updateTheme() {
    const hour = Number(clock.format(new Date()));
    appliedTheme = hour >= 22 || hour < 6 ? "dark" : "light";
    root.dataset.theme = appliedTheme;
  }
  updateTheme();
  setInterval(() => {
    if (root.dataset.themeMode !== "auto" || root.dataset.theme !== appliedTheme) return;
    updateTheme();
  }, 60_000);
})();
