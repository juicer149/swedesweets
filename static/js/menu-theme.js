/*
 * Shared day/night menu palette for landing, navigation and entrance pages.
 * The default "auto" follows Paris time: day 06:00–22:00, night 22:00–06:00.
 * A fixed data-menu-theme="day" or "night" in base.html is never overridden.
 * The OS preference could be supported later via prefers-color-scheme.
 */
(() => {
  "use strict";

  const root = document.documentElement;
  if (root.getAttribute("data-menu-theme") !== "auto") return;
  root.dataset.menuThemeAuto = "true";

  const clock = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Paris",
    hour: "2-digit",
    hourCycle: "h23",
  });

  let appliedTheme = null;

  function updateTheme() {
    const hour = Number(clock.format(new Date()));
    const theme = hour >= 22 || hour < 6 ? "night" : "day";
    root.setAttribute("data-menu-theme", theme);
    appliedTheme = theme;
  }

  updateTheme();

  // Re-check at minute boundaries while the tab remains open.
  // A manual preview override is not replaced by the clock.
  setInterval(() => {
    if (root.dataset.menuThemeAuto !== "true" || root.dataset.menuTheme !== appliedTheme) return;
    updateTheme();
  }, 60_000);
})();
