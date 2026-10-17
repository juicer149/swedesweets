/* Shared preferences. theme.js owns palette resolution and persistence. */
(() => {
  "use strict";
  for (const form of document.querySelectorAll("[data-language-preferences]")) {
    form.addEventListener("change", () => form.requestSubmit());
  }

  const controller = window.siteTheme;
  const choices = [...document.querySelectorAll("[data-theme-choice]")];
  if (!controller || !choices.length) return;
  const root = document.documentElement;

  function sync() {
    for (const choice of choices) {
      choice.checked = choice.value === root.dataset.theme;
    }
  }

  for (const choice of choices) {
    choice.addEventListener("change", () => {
      if (!choice.checked) return;
      controller.set(choice.value);
      // Preserve catalog overlay history, unrelated parameters and the hash.
      const url = new URL(window.location.href);
      if (url.searchParams.has("theme")) {
        url.searchParams.set("theme", choice.value);
        window.history.replaceState(window.history.state, "", url);
      }
      // Language submission must return to the newly selected preview too.
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
