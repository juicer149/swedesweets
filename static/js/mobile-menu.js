/* Native details keep desktop/outside/Escape behaviour. On phones account
   and settings cover the page between its navigation bars, without scrolling
   or leaving the covered page in the keyboard/accessibility tree. */
(() => {
  "use strict";
  const menus = [...document.querySelectorAll("details[data-mobile-menu]")];
  if (!menus.length) return;
  const mobile = matchMedia("(max-width: 767px)");
  const root = document.documentElement;
  const inertBefore = new Map();
  let active = null;

  function sync() {
    const next = mobile.matches ? menus.find(menu => menu.open) : null;
    for (const [element, inert] of inertBefore) element.inert = inert;
    inertBefore.clear();
    root.classList.toggle("mobile-menu-open", Boolean(next));

    if (next) {
      const panel = next.querySelector(".mobile-menu-panel");
      const top = document.querySelector(".site-header, .entrance-header, .landing__top");
      const nav = document.querySelector(".site-nav__links:not(.site-nav__links--empty)");
      const bottom = nav && getComputedStyle(nav).position === "fixed"
        ? innerHeight - nav.getBoundingClientRect().top + 8 : 12;
      panel.style.setProperty("--mobile-menu-top", `${Math.max(0, top?.getBoundingClientRect().bottom || 0)}px`);
      panel.style.setProperty("--mobile-menu-bottom", `${bottom}px`);

      for (const element of document.querySelectorAll("main, footer, .landing__stage, .landing__bottom")) {
        if (!element.contains(next)) {
          inertBefore.set(element, element.inert);
          element.inert = true;
        }
      }
      if (next !== active) panel.querySelector("a, button")?.focus({ preventScroll: true });
    }
    active = next;
  }

  for (const menu of menus) {
    menu.addEventListener("toggle", sync);
    menu.querySelector("[data-close-details]").addEventListener("click", () => {
      menu.open = false;
      menu.querySelector("summary").focus({ preventScroll: true });
    });
  }
  mobile.addEventListener("change", sync);
  window.addEventListener("resize", sync);
  window.visualViewport?.addEventListener("resize", sync);
  window.addEventListener("pageshow", sync);
})();
