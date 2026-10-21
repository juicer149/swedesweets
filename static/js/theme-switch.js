/* theme.js owns palette resolution/persistence; this controls the theme
   choices in the settings panel: the sun (light) and the moon (dark), the
   one in use pressed and lit like the chosen language beside them. */
(() => {
  "use strict";
  const controller = window.siteTheme;
  const buttons = [...document.querySelectorAll("[data-theme-choice]")];
  if (!controller || !buttons.length) return;
  const root = document.documentElement;

  function sync() {
    const current = root.dataset.theme === "dark" ? "dark" : "light";
    for (const button of buttons) {
      const on = button.dataset.themeChoice === current;
      button.setAttribute("aria-pressed", String(on));
      button.classList.toggle("language-switcher__option--active", on);
    }
  }

  for (const button of buttons) {
    button.addEventListener("click", () => {
      const theme = button.dataset.themeChoice;
      if (theme === root.dataset.theme) return;
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
  document.addEventListener("site-language-changed", sync);
  sync();
  for (const group of document.querySelectorAll("[data-theme-preferences]")) {
    group.hidden = false;
  }
  new MutationObserver(sync).observe(root, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });
})();
