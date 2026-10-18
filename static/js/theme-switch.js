/* theme.js owns palette resolution/persistence; this controls its switches. */
(() => {
  "use strict";
  const controller = window.siteTheme;
  const buttons = [...document.querySelectorAll("[data-theme-switch]")];
  if (!controller || !buttons.length) return;
  const root = document.documentElement;

  function sync() {
    const dark = root.dataset.theme === "dark";
    for (const button of buttons) {
      button.setAttribute("aria-checked", String(dark));
      button.title = dark ? button.dataset.lightLabel : button.dataset.darkLabel;
    }
  }

  for (const button of buttons) {
    button.addEventListener("click", () => {
      const theme = root.dataset.theme === "dark" ? "light" : "dark";
      controller.set(theme);
      // Preserve catalog overlay history, unrelated parameters and the hash.
      const url = new URL(window.location.href);
      if (url.searchParams.has("theme")) {
        url.searchParams.set("theme", theme);
        window.history.replaceState(window.history.state, "", url);
      }
      // A language POST must return to the newly selected preview too.
      for (const next of document.querySelectorAll('[data-language-preferences] [name="next"]')) {
        next.value = url.pathname + url.search + url.hash;
      }
      sync();
    });
  }
  sync();
  for (const group of document.querySelectorAll("[data-theme-preferences]")) {
    group.hidden = false;
  }
  new MutationObserver(sync).observe(root, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });
})();
