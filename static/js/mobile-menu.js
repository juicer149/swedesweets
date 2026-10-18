/* Desktop keeps native details. Mobile sheets reveal downward and retract
   upward, finishing a close before opening the latest requested sheet. */
(() => {
  "use strict";
  const menus = [...document.querySelectorAll("details[data-mobile-menu]")];
  if (!menus.length) return;
  const mobile = matchMedia("(max-width: 767px)");
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const root = document.documentElement;
  const inertBefore = new Map();
  let active = null;
  let wanted = null;
  let running = false;
  let motion = null;
  let restoreFocus = false;

  function sync() {
    const next = mobile.matches ? menus.find(menu => menu.open) : null;
    for (const [element, inert] of inertBefore) element.inert = inert;
    inertBefore.clear();
    root.classList.toggle("mobile-menu-open", mobile.matches && Boolean(next || wanted));

    if (next) {
      const panel = next.querySelector(".mobile-menu-panel");
      const top = document.querySelector(".site-header, .entrance-header, .landing__top");
      const nav = document.querySelector(".site-nav__links:not(.site-nav__links--empty)");
      const bottom = nav && getComputedStyle(nav).position === "fixed"
        ? innerHeight - nav.getBoundingClientRect().top + 8 : 12;
      panel.style.setProperty("--mobile-menu-top", `${Math.max(0, top?.getBoundingClientRect().bottom || 0)}px`);
      panel.style.setProperty("--mobile-menu-bottom", `${bottom}px`);
    }
    if (mobile.matches && (next || wanted)) {
      for (const element of document.querySelectorAll("main, footer, .landing__stage, .landing__bottom")) {
        if (!element.contains(next || wanted)) {
          inertBefore.set(element, element.inert);
          element.inert = true;
        }
      }
    }
  }

  async function animate(menu, opening) {
    if (!mobile.matches || reducedMotion.matches) return;
    const frames = [{ clipPath: "inset(0 0 100% 0)" }, { clipPath: "inset(0 0 0% 0)" }];
    motion = menu.querySelector(".mobile-menu-panel").animate(
      opening ? frames : [...frames].reverse(),
      { duration: opening ? 280 : 220, easing: "cubic-bezier(.2,.7,.2,1)" },
    );
    await motion.finished.catch(() => {});
    motion = null;
  }

  async function request(menu, focus = false) {
    wanted = menu;
    restoreFocus = focus;
    if (running) return;
    running = true;
    active = menus.find(item => item.open) || null;
    while (active !== wanted && mobile.matches) {
      if (active) {
        const closing = active;
        await animate(closing, false);
        closing.open = false;
        active = null;
        if (!wanted && restoreFocus) closing.querySelector("summary").focus({ preventScroll: true });
      } else if (wanted) {
        active = wanted;
        // Summary clicks are handled here, so close desktop-style popovers
        // (notably cart) that the document outside-click handler would close.
        for (const disclosure of document.querySelectorAll("details[data-dismiss-on-outside-click][open]")) {
          if (!menus.includes(disclosure)) disclosure.open = false;
        }
        active.open = true;
        sync();
        await animate(active, true);
        if (active === wanted && mobile.matches) {
          active.querySelector(".mobile-menu-panel a, .mobile-menu-panel button")?.focus({ preventScroll: true });
        }
      }
    }
    running = false;
    sync();
  }

  for (const menu of menus) {
    menu.addEventListener("toggle", sync);
    menu.querySelector("summary").addEventListener("click", event => {
      if (!mobile.matches) return;
      event.preventDefault();
      // The generic outside-click closer must not close the old sheet again
      // while a deliberate switch to another sheet is already queued.
      event.stopPropagation();
      request(wanted === menu || (!running && menu.open) ? null : menu, true);
    });
    menu.addEventListener("details-request-close", event => {
      if (!mobile.matches) return;
      event.preventDefault();
      request(null, event.detail.restoreFocus);
    });
    menu.querySelector("[data-close-details]").addEventListener("click", () => {
      if (mobile.matches) request(null, true);
      else menu.open = false;
    });
  }
  mobile.addEventListener("change", () => {
    wanted = null;
    motion?.finish();
    sync();
  });
  reducedMotion.addEventListener("change", () => { if (reducedMotion.matches) motion?.finish(); });
  window.addEventListener("resize", sync);
  window.visualViewport?.addEventListener("resize", sync);
  window.addEventListener("pageshow", sync);
})();
