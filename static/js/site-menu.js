/* The navbar's Menu (includes/site_menu.html): its levels, its keys and
   Escape. mobile-menu.js opens, closes and animates the panel itself (and
   Back closes it); this chooses which level shows, its title, and which
   choice is the chosen one.

   Played like the start page's menu (landing.js): the chosen choice has
   the gold and the crown, no box around it. Pointing at a choice, or
   focusing it with the keys, makes it the chosen one; on the menu's links it stays when
   the pointer moves on, while a language or theme the pointer leaves lets
   go (the one in use keeps its moonlight). ↓ and ↑ go from row to row
   (round from the last to the first), ← and → between the choices of a row
   (Language, Theme), Home and End to the ends; Enter takes it.

   Escape: on Settings it returns to the menu; otherwise, with a panel or a
   sheet open, mobile-menu.js and details-popover.js close it; with nothing
   open (no dialog, no product opened over the catalog, no dropdown, not
   typing) it opens the menu.

   Opened, the first choice is the chosen one (by day its cloud shows where
   you are), whatever opened it; Settings opens on the theme in use, the
   cloud in front of the sun or the moon.

   A staff member switching views (the corner's house and wrench) keeps the
   Menu in front: the new site opens with it already there. */
(() => {
  "use strict";
  const menus = [...document.querySelectorAll("[data-site-menu]")];
  if (!menus.length) return;

  const CHOSEN = "is-chosen";
  const STAY = "site-menu-stay";
  const ITEMS = ".site-menu__link, .language-switcher__option";

  const activeLevel = (menu) => menu.querySelector("[data-menu-level][data-menu-active]");
  const visible = (element) => !element.hidden && element.getClientRects().length > 0;
  const items = (menu) => [...(activeLevel(menu)?.querySelectorAll(ITEMS) || [])].filter(visible);

  // Rows: a link on its own, or a group's choices side by side.
  function rows(menu) {
    const result = [];
    for (const item of items(menu)) {
      const group = item.closest(".site-menu__choices");
      const last = result.at(-1);
      if (group && last?.group === group) last.items.push(item);
      else result.push({ group, items: [item] });
    }
    return result;
  }

  function choose(menu, item) {
    for (const other of menu.querySelectorAll(`.${CHOSEN}`)) {
      if (other !== item) other.classList.remove(CHOSEN);
    }
    item?.classList.add(CHOSEN);
  }

  // Whether the visitor is using the keys: then the focus is the chosen
  // one. With the mouse the pointer chooses, and a focus set for it (opening
  // the Menu, going into Settings) puts no gold on the choice in use.
  let viaKeys = false;
  window.addEventListener("keydown", () => { viaKeys = true; }, true);
  window.addEventListener("pointerdown", () => { viaKeys = false; }, true);

  function take(menu, item, mark = viaKeys) {
    if (!item) return;
    if (mark) choose(menu, item);
    else choose(menu, null);
    item.focus({ preventScroll: true });
  }

  // Into a row: on the choice in use (the language, the theme, the site you
  // are on), or its first. Settings starts on the theme's row.
  const entry = (row) => row.items.find((item) =>
    item.matches('[aria-current="true"], [aria-pressed="true"], .language-switcher__option--active')
  ) || row.items[0];

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
      // Back from Settings, the crown waits on Settings; elsewhere on the
      // first row.
      const from = level === "main" && menu.querySelector('[data-menu-go="settings"]');
      const all = rows(menu);
      const first = (level === "settings" && all.find((row) => row.group?.closest("[data-theme-preferences]"))) || all[0];
      take(menu, from && visible(from) ? from : first && entry(first), true);
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
      if (!menu.open) {
        choose(menu, null);
        show(menu, "main", false);
      }
    });
    // Opened (mobile-menu.js puts the focus on the first choice): that one
    // is the chosen one, by the keys or not.
    document.addEventListener("mobile-menu-settled", (event) => {
      if (!menu.open || event.detail?.key !== menu.dataset.mobileMenu) return;
      const focused = document.activeElement;
      if (menu.contains(focused) && focused.matches?.(ITEMS)) choose(menu, focused);
    });
    // The chosen one follows the focus and the pointer, and stays.
    menu.addEventListener("focusin", (event) => {
      if (viaKeys && event.target.matches?.(ITEMS)) choose(menu, event.target);
    });
    menu.addEventListener("pointerover", (event) => {
      const item = event.target.closest?.(ITEMS);
      if (item && menu.contains(item) && event.pointerType === "mouse") take(menu, item, true);
    });
    // A language or theme the pointer leaves lets go of the gold and the
    // crown; the keys still find it where the focus is.
    menu.addEventListener("pointerout", (event) => {
      const item = event.target.closest?.(".site-menu__choices .language-switcher__option");
      if (!item || event.pointerType !== "mouse" || item.contains(event.relatedTarget)) return;
      item.classList.remove(CHOSEN);
    });
    // Switching sites: open the Menu again, at once, on the new site.
    for (const link of menu.querySelectorAll("[data-site-menu-stay]")) {
      link.addEventListener("click", () => {
        try { sessionStorage.setItem(STAY, "1"); } catch (error) {}
      });
    }
    menu.addEventListener("keydown", (event) => {
      if (!menu.open || event.altKey || event.ctrlKey || event.metaKey) return;
      const all = rows(menu);
      if (!all.length) return;
      const current = document.activeElement;
      let index = all.findIndex((row) => row.items.includes(current));
      const row = all[index];
      let target = null;
      switch (event.key) {
        case "ArrowDown":
          target = entry(all[index < 0 || index === all.length - 1 ? 0 : index + 1]);
          break;
        case "ArrowUp":
          target = entry(all[index <= 0 ? all.length - 1 : index - 1]);
          break;
        case "Home":
          target = entry(all[0]);
          break;
        case "End":
          target = entry(all.at(-1));
          break;
        case "ArrowRight":
        case "ArrowLeft": {
          if (!row || row.items.length < 2) return;
          const at = row.items.indexOf(current);
          const step = event.key === "ArrowRight" ? 1 : -1;
          target = row.items[(at + step + row.items.length) % row.items.length];
          break;
        }
        default:
          return;
      }
      event.preventDefault();
      take(menu, target);
    });
  }

  const request = (key, detail = {}) => document.dispatchEvent(
    new CustomEvent("mobile-menu-request", { detail: { key, restoreFocus: true, ...detail } })
  );

  // Arrived from a view switch: the Menu is already in front.
  let stay = false;
  try {
    stay = sessionStorage.getItem(STAY) === "1";
    sessionStorage.removeItem(STAY);
  } catch (error) {}
  if (stay) {
    const menu = menus[0];
    // After the other deferred scripts: mobile-menu.js must be listening.
    const open = () => request(menu.dataset.mobileMenu, { instant: true });
    if (document.readyState === "complete") open();
    else document.addEventListener("DOMContentLoaded", open, { once: true });
  }

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
