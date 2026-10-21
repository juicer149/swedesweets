/* The navbar's Menu (includes/site_menu.html): its levels, its Return and
   Escape. mobile-menu.js opens, closes and animates the panel itself (and
   Back closes it); this only chooses which level shows and its title.

   Escape: on Settings it returns to the menu; otherwise, with a panel or a
   sheet open, mobile-menu.js and details-popover.js close it; with nothing
   open (no dialog, no product opened over the catalog, no dropdown, not
   typing) it opens the menu. */
(() => {
  "use strict";
  const menus = [...document.querySelectorAll("[data-site-menu]")];
  if (!menus.length) return;

  function show(menu, level, focus = true) {
    const title = menu.querySelector("[data-site-menu-title]");
    for (const panel of menu.querySelectorAll("[data-menu-level]")) {
      panel.toggleAttribute("data-menu-active", panel.dataset.menuLevel === level);
    }
    menu.dataset.menuLevel = level;
    if (title) {
      title.textContent = level === "settings" ? title.dataset.titleSettings : title.dataset.titleMain;
    }
    if (focus) {
      menu.querySelector(`[data-menu-level="${level}"]`)
        ?.querySelector("a, button:not([hidden]), [aria-pressed]")
        ?.focus({ preventScroll: true });
    }
  }

  for (const menu of menus) {
    menu.dataset.menuReady = "";
    for (const hidden of menu.querySelectorAll("[data-menu-go], .site-menu__return")) hidden.hidden = false;
    show(menu, "main", false);
    for (const go of menu.querySelectorAll("[data-menu-go]")) {
      go.addEventListener("click", () => show(menu, go.dataset.menuGo));
    }
    // Back to the first level whenever it closes.
    menu.addEventListener("toggle", () => {
      if (!menu.open) show(menu, "main", false);
    });
  }

  const request = (key) => document.dispatchEvent(
    new CustomEvent("mobile-menu-request", { detail: { key, restoreFocus: true } })
  );

  window.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || event.defaultPrevented) return;

    const open = menus.find((menu) => menu.open);
    if (open && open.dataset.menuLevel !== "main") {
      event.preventDefault();
      event.stopImmediatePropagation();
      show(open, "main");
      return;
    }

    const busy = document.querySelector("details[data-mobile-menu][open], dialog[open], .ts-dropdown:not([style*='display: none'])")
      || document.documentElement.classList.contains("catalog--detail-open")
      || event.target.closest?.("input, textarea, select, [contenteditable]");
    if (busy) return;

    // Stopped here, or details-popover.js would see the menu just opened
    // and close it again on the same key.
    event.preventDefault();
    event.stopImmediatePropagation();
    request(menus[0].dataset.mobileMenu);
  }, true);
})();
