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
  const headerInertBefore = new Map();
  const backdrop = document.createElement("div");
  backdrop.className = "menu-panel-backdrop";
  backdrop.setAttribute("aria-hidden", "true");
  document.body.append(backdrop);
  let wanted = null;
  let running = false;
  let motion = null;
  let restoreFocus = false;
  // Opened without its motion: the Menu staying in front across a site switch.
  let instant = false;
  // Keep the sheet at its layout-viewport position while an on-screen keyboard
  // covers its lower part. It must not lift the close circle above the keys.
  let editingHeight = null;
  let editingWidth = null;
  const textEditor = element => element instanceof HTMLElement && element.matches(
    'input:not([type="hidden"], [type="checkbox"], [type="radio"], [type="button"], [type="submit"], [type="range"]), textarea, [contenteditable="true"]'
  );
  document.addEventListener("focusin", event => {
    if (mobile.matches && event.target.closest(selector) && textEditor(event.target)) {
      editingHeight ??= innerHeight;
      editingWidth = innerWidth;
    }
  });
  document.addEventListener("focusout", () => {
    if (editingHeight !== null) setTimeout(sync, 0);
  });
  document.addEventListener("pointerdown", event => {
    const active = document.activeElement;
    if (!mobile.matches || !textEditor(active) || !active.closest(selector)) return;
    const wrapper = active.closest(".ts-wrapper");
    if (event.target === active || wrapper?.contains(event.target)) return;
    // Keep option selection and the next control's native click behaviour.
    active.blur();
    const select = [...document.querySelectorAll("select")].find(element => element.tomselect?.wrapper === wrapper);
    select?.tomselect?.blur();
  }, true);
  const menuFor = key => [...document.querySelectorAll(selector)].find(menu => menu.dataset.mobileMenu === key);
  const openMenu = () => document.querySelector(`${selector}[open]`);

  function syncHeader(key = running ? wanted : openMenu()?.dataset.mobileMenu) {
    const header = document.querySelector(".site-header");
    if (!header || root.dataset.siteZone === "ops") return;
    const flow = root.hasAttribute("data-checkout-flow");
    if (flow && (!mobile.matches || !key)) key = "cart";
    if ((!mobile.matches && !flow) || !["cart", "menu"].includes(key)) {
      delete header.dataset.mobilePanel;
      for (const [link, inert] of headerInertBefore) {
        link.inert = inert;
        link.classList.remove("is-mobile-panel-underlay");
      }
      headerInertBefore.clear();
      return;
    }
    const trigger = menuFor(key)?.querySelector(":scope > summary");
    if (!trigger) return;
    const pageLink = header.querySelector('.site-nav__link[aria-current="page"]');
    if (pageLink) {
      if (!headerInertBefore.has(pageLink)) headerInertBefore.set(pageLink, pageLink.inert);
      pageLink.classList.add("is-mobile-panel-underlay");
      pageLink.inert = true;
    }
    const box = trigger.getBoundingClientRect();
    const shift = getComputedStyle(trigger).translate.split(" ").map(value => parseFloat(value) || 0);
    const bar = header.getBoundingClientRect();
    // Subtract the live translate, including a half-finished movement or a
    // newly refreshed cart fragment, to recover the unchanged layout slot.
    const x = innerWidth / 2 - (box.left + box.width / 2 - shift[0]);
    const y = bar.top + bar.height / 2 - (box.top + box.height / 2 - (shift[1] || 0));
    header.style.setProperty(`--mobile-${key}-shift-x`, `${x}px`);
    header.style.setProperty(`--mobile-${key}-shift-y`, `${y}px`);
    header.dataset.mobilePanel = key;
  }

  function sync() {
    const next = openMenu();
    const covered = next || (wanted && menuFor(wanted));
    root.classList.toggle("menu-panel-open", Boolean(covered));
    root.classList.toggle("mobile-menu-open", mobile.matches && Boolean(covered));
    syncHeader();
    for (const [element, inert] of inertBefore) element.inert = inert;
    inertBefore.clear();
    const header = document.querySelector(".site-header, .entrance-header, .landing__top");
    const headerBottom = Math.max(0, header?.getBoundingClientRect().bottom || 0);
    for (const menu of document.querySelectorAll(selector)) {
      menu.querySelector(".mobile-menu-viewport").style.setProperty("--menu-panel-top", `${headerBottom}px`);
    }
    if (editingHeight !== null && editingWidth !== innerWidth) {
      editingHeight = textEditor(document.activeElement) ? innerHeight : null;
      editingWidth = innerWidth;
    }
    if (!covered || !mobile.matches
      || (editingHeight !== null && !textEditor(document.activeElement) && innerHeight >= editingHeight - 1)) editingHeight = null;
    if (!covered) return;

    const viewport = covered.querySelector(".mobile-menu-viewport");
    const top = document.querySelector(".site-header, .entrance-header, .landing__top");
    // Browsers may resize only the visual viewport, or the layout viewport
    // too. Neither should lift the sheet's close circle while typing.
    const bottom = editingHeight === null ? 0 : Math.min(0, innerHeight - editingHeight);
    viewport.style.setProperty("--mobile-menu-top", `${Math.max(0, top?.getBoundingClientRect().bottom || 0)}px`);
    viewport.style.setProperty("--mobile-menu-viewport-bottom", `${bottom}px`);
    for (const element of document.querySelectorAll("main, footer, .landing__stage, .landing__bottom, .catalog__detail")) {
      if (!element.contains(covered) && !covered.contains(element)) {
        inertBefore.set(element, element.inert);
        element.inert = true;
      }
    }
  }

  async function animate(menu, opening) {
    if (instant || reducedMotion.matches || !menu?.isConnected) return;
    // Wider screens open every panel as a centred box (the Menu, the cart).
    const centered = Boolean(menu.closest("[data-landing], .entrance-header")) || !mobile.matches;
    const frames = centered
      ? [{ opacity: 0, transform: "scale(.96)" }, { opacity: 1, transform: "scale(1)" }]
      : [{ transform: "translateY(-102%)" }, { transform: "translateY(0)" }];
    const animation = menu.querySelector(".mobile-menu-panel").animate(
      opening ? frames : [...frames].reverse(),
      { duration: centered ? (opening ? 180 : 140) : (opening ? 320 : 240), easing: "cubic-bezier(.22,.7,.2,1)", fill: "both" },
    );
    motion = animation;
    await animation.finished.catch(() => {});
    return animation;
  }

  async function request(key, focus = false, still = false) {
    if (openMenu()?.dataset.mobileMenu === "cart" && window.SwedeSweets?.orderFlow?.busy() && key !== "cart") return;
    if (key === "cart" && menuFor(key)?.dataset.cartLocked === "true" && menuFor(key)?.dataset.flowHost !== "true") return;
    if (!key && openMenu()) {
      const intercepted = new CustomEvent("panel-close-request", { cancelable: true, bubbles: true });
      if (!openMenu().dispatchEvent(intercepted)) return;
    }
    wanted = key;
    restoreFocus = focus;
    instant = still;
    syncHeader(wanted);
    if (running) return;
    running = true;
    let focusTarget = null;
    let active = openMenu()?.dataset.mobileMenu || null;
    while (active !== wanted) {
      if (active) {
        const closing = menuFor(active);
        closing?.removeAttribute("data-panel-lit");
        if (!reducedMotion.matches) await new Promise(resolve => setTimeout(resolve, 140));
        const animation = await animate(menuFor(active), false);
        // Resolve it again: a quantity change may have replaced the fragment.
        const current = menuFor(active);
        if (current) current.open = false;
        animation?.cancel();
        if (!wanted && restoreFocus) focusTarget = current?.querySelector("summary");
        active = null;
      } else if (wanted) {
        active = wanted;
        const opening = menuFor(active);
        if (!opening) { wanted = null; active = null; break; }
        opening.removeAttribute("data-panel-lit");
        opening.open = true;
        sync();
        const animation = await animate(opening, true);
        animation?.cancel();
        if (active === wanted) {
          menuFor(active)?.setAttribute("data-panel-lit", "");
          menuFor(active)?.querySelector(".mobile-menu-panel a, .mobile-menu-panel button")?.focus({ preventScroll: true });
        }
      }
    }
    motion = null;
    running = false;
    instant = false;
    sync();
    syncHistory();
    // Mobile triggers become visible again only after sync clears the sheet.
    if (!openMenu()) focusTarget?.focus({ preventScroll: true });
    document.dispatchEvent(new CustomEvent("mobile-menu-settled", {
      detail: { key: openMenu()?.dataset.mobileMenu || null },
    }));
  }

  /* Back closes the open panel, as it closes a product opened over the
     catalog: opening one adds a step to the history (switching between
     panels replaces it), and closing it another way takes that step back.
     The page's own state (catalog.js's open product) is kept in it. */
  const panelState = () => window.history.state?.menuPanel || null;
  function syncHistory() {
    const key = openMenu()?.dataset.mobileMenu || null;
    const current = panelState();
    if (key === current) return;
    if (key && !current) {
      window.history.pushState({ ...(window.history.state || {}), menuPanel: key }, "", window.location.href);
    } else if (key) {
      window.history.replaceState({ ...window.history.state, menuPanel: key }, "", window.location.href);
    } else {
      window.history.back();
    }
  }
  window.addEventListener("popstate", () => {
    const key = panelState();
    if (openMenu() && !key) request(null, true);
    else if (key && !openMenu() && menuFor(key)) request(key, false);
  });
  // Back here from a page a panel led to: the panel is closed, so is its step.
  if (panelState()) {
    const { menuPanel, ...rest } = window.history.state;
    window.history.replaceState(Object.keys(rest).length ? rest : null, "", window.location.href);
  }

  document.addEventListener("click", event => {
    const summary = event.target.closest("summary");
    const menu = summary?.parentElement;
    if (menu?.matches(selector)) {
      event.preventDefault();
      event.stopPropagation();
      request(wanted === menu.dataset.mobileMenu || (!running && menu.open) ? null : menu.dataset.mobileMenu, true);
      return;
    }
    const close = event.target.closest("[data-close-details]");
    if (close) {
      const details = close.closest(selector);
      if (details) request(null, true);
    }
  }, true);
  document.addEventListener("details-request-close", event => {
    if (!event.target.matches(selector)) return;
    event.preventDefault();
    request(null, event.detail.restoreFocus);
  }, true);
  document.addEventListener("toggle", event => {
    if (event.target.matches?.(selector)) sync();
  }, true);
  backdrop.addEventListener("click", () => {
    request(null, true);
  });
  document.addEventListener("mobile-menu-request", event => {
    request(event.detail.key, Boolean(event.detail.restoreFocus), Boolean(event.detail.instant));
  });
  document.addEventListener("navbar-cart-refreshed", sync);
  document.addEventListener("order-flow-chrome", sync);
  mobile.addEventListener("change", () => { motion?.finish(); sync(); });
  reducedMotion.addEventListener("change", () => { if (reducedMotion.matches) motion?.finish(); });
  window.addEventListener("resize", sync);
  window.visualViewport?.addEventListener("resize", sync);
  window.visualViewport?.addEventListener("scroll", sync);
  window.addEventListener("pageshow", sync);
})();
