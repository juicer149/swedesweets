/* Stable menu keys survive navbar-cart fragment replacement. The viewport
   clips a real sliding sheet while the original page stays visible beneath. */
(() => {
  "use strict";
  const selector = "details[data-mobile-menu]";
  if (!document.querySelector(selector)) return;
  const mobile = matchMedia("(max-width: 767px)");
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const root = document.documentElement;
  const inertBefore = new Map();
  const backdrop = document.createElement("div");
  backdrop.className = "menu-panel-backdrop";
  backdrop.setAttribute("aria-hidden", "true");
  document.body.append(backdrop);
  let wanted = null;
  let running = false;
  let motion = null;
  let restoreFocus = false;
  const menuFor = key => [...document.querySelectorAll(selector)].find(menu => menu.dataset.mobileMenu === key);
  const openMenu = () => document.querySelector(`${selector}[open]`);

  function sync() {
    const next = openMenu();
    const covered = next || (mobile.matches && wanted && menuFor(wanted));
    root.classList.toggle("menu-panel-open", Boolean(covered));
    root.classList.toggle("mobile-menu-open", mobile.matches && Boolean(covered));
    for (const [element, inert] of inertBefore) element.inert = inert;
    inertBefore.clear();
    if (!mobile.matches || !covered) return;

    const viewport = covered.querySelector(".mobile-menu-viewport");
    const top = document.querySelector(".site-header, .entrance-header, .landing__top");
    const nav = document.querySelector(".site-nav__links:not(.site-nav__links--empty)");
    const bottom = nav && getComputedStyle(nav).position === "fixed"
      ? innerHeight - nav.getBoundingClientRect().top + 8 : 12;
    viewport.style.setProperty("--mobile-menu-top", `${Math.max(0, top?.getBoundingClientRect().bottom || 0)}px`);
    viewport.style.setProperty("--mobile-menu-bottom", `${bottom}px`);
    for (const element of document.querySelectorAll("main, footer, .landing__stage, .landing__bottom")) {
      if (!element.contains(covered) && !covered.contains(element)) {
        inertBefore.set(element, element.inert);
        element.inert = true;
      }
    }
  }

  async function animate(menu, opening) {
    if (!mobile.matches || reducedMotion.matches || !menu?.isConnected) return;
    const frames = [{ transform: "translateY(-102%)" }, { transform: "translateY(0)" }];
    const animation = menu.querySelector(".mobile-menu-panel").animate(
      opening ? frames : [...frames].reverse(),
      { duration: opening ? 320 : 240, easing: "cubic-bezier(.22,.7,.2,1)", fill: "both" },
    );
    motion = animation;
    await animation.finished.catch(() => {});
    return animation;
  }

  async function request(key, focus = false) {
    wanted = key;
    restoreFocus = focus;
    if (running) return;
    running = true;
    let active = openMenu()?.dataset.mobileMenu || null;
    while (active !== wanted && mobile.matches) {
      if (active) {
        const closing = menuFor(active);
        const animation = await animate(closing, false);
        // Resolve it again: a quantity change may have replaced the fragment.
        const current = menuFor(active);
        if (current) current.open = false;
        animation?.cancel();
        if (!wanted && restoreFocus) current?.querySelector("summary").focus({ preventScroll: true });
        active = null;
      } else if (wanted) {
        active = wanted;
        const opening = menuFor(active);
        if (!opening) { wanted = null; active = null; break; }
        opening.open = true;
        sync();
        const animation = await animate(opening, true);
        animation?.cancel();
        if (active === wanted && mobile.matches) {
          menuFor(active)?.querySelector(".mobile-menu-panel a, .mobile-menu-panel button")?.focus({ preventScroll: true });
        }
      }
    }
    motion = null;
    running = false;
    sync();
  }

  document.addEventListener("click", event => {
    const summary = event.target.closest("summary");
    const menu = summary?.parentElement;
    if (mobile.matches && menu?.matches(selector)) {
      event.preventDefault();
      event.stopPropagation();
      request(wanted === menu.dataset.mobileMenu || (!running && menu.open) ? null : menu.dataset.mobileMenu, true);
      return;
    }
    const close = event.target.closest("[data-close-details]");
    if (close) {
      const details = close.closest(selector);
      if (mobile.matches) request(null, true);
      else if (details) details.open = false;
    }
  }, true);
  document.addEventListener("details-request-close", event => {
    if (!mobile.matches || !event.target.matches(selector)) return;
    event.preventDefault();
    request(null, event.detail.restoreFocus);
  }, true);
  document.addEventListener("toggle", event => {
    if (event.target.matches?.(selector)) sync();
  }, true);
  backdrop.addEventListener("click", () => {
    if (mobile.matches) request(null, true);
    else { if (openMenu()) openMenu().open = false; sync(); }
  });
  document.addEventListener("navbar-cart-refreshed", sync);
  mobile.addEventListener("change", () => { wanted = null; motion?.finish(); sync(); });
  reducedMotion.addEventListener("change", () => { if (reducedMotion.matches) motion?.finish(); });
  window.addEventListener("resize", sync);
  window.visualViewport?.addEventListener("resize", sync);
  window.addEventListener("pageshow", sync);
})();
