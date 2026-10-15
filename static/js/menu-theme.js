/*
 * Shared menu theme for the landing page, navigation and entrance pages.
 * Use Paris wall-clock time, regardless of the visitor's time zone.
 * Set data-menu-theme to night, dawn, morning or day in base.html to
 * preview a fixed theme; auto (the default) follows this schedule:
 * 22–06 night, 06–08 dawn, 08–10 morning, 10–18 day,
 * 18–20 morning, 20–22 dawn.
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
    let theme;
    if (hour >= 22 || hour < 6) theme = "night";
    else if (hour < 8 || hour >= 20) theme = "dawn";
    else if (hour < 10 || hour >= 18) theme = "morning";
    else theme = "day";
    root.setAttribute("data-menu-theme", theme);
    appliedTheme = theme;
  }

  updateTheme();

  // Re-check at minute boundaries while the tab remains open.
  // An explicit preview override is never replaced by the clock.
  setInterval(() => {
    if (root.dataset.menuThemeAuto !== "true" || root.dataset.menuTheme !== appliedTheme) return;
    updateTheme();
  }, 60_000);
})();
