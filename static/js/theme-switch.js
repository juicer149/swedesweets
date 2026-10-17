/* Temporary customer preview. theme.js owns palette resolution/persistence. */
(() => {
  "use strict";
  const controller = window.siteTheme;
  const buttons = [...document.querySelectorAll("[data-theme-switch]")];
  if (!controller || !buttons.length) return;
  const root = document.documentElement;

  function sync() {
    const dark = root.dataset.theme === "dark";
    for (const button of buttons) {
      button.setAttribute("aria-pressed", String(dark));
      button.title = dark ? button.dataset.lightLabel : button.dataset.darkLabel;
    }
  }

  for (const button of buttons) {
    button.addEventListener("click", () => {
      const theme = root.dataset.theme === "dark" ? "light" : "dark";
      controller.set(theme);
      // A preview URL must agree with the new choice on reload. Keep the
      // catalog overlay's history state, other query parameters and hash.
      const url = new URL(window.location.href);
      if (url.searchParams.has("theme")) {
        url.searchParams.set("theme", theme);
        window.history.replaceState(window.history.state, "", url);
      }
      sync();
    });
  }
  sync();
  for (const button of buttons) button.hidden = false;
  new MutationObserver(sync).observe(root, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });
})();
