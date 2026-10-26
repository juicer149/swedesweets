/* Native home links, with a shared cloud/wordmark flight where supported.
   This head script registers pagereveal before the first rendering chance.
   Other navigation and reduced motion keep their normal behaviour. */
(() => {
  "use strict";
  const root = document.documentElement;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const key = "swedesweets-home-flight";
  const cloudURL = document.currentScript.dataset.cloud;
  const canMove = () => window.SwedeSweetsEffects?.profile().travel === "cloud" && root.dataset.siteZone !== "ops" && !reduced.matches;
  const brandSelector = "a.site-brand[href], a.entrance-header__brand[href]";
  let outgoing = null;
  let started = false;
  let landed = false;
  let cloud = null;
  let hero = null;
  let landing = null;
  let warmImage = null;
  let flightSheet = null;
  function enableNative() {
    if (!("adoptedStyleSheets" in document) || !CSSStyleSheet.prototype.replaceSync) return;
    if (!flightSheet) {
      flightSheet = new CSSStyleSheet();
      flightSheet.replaceSync("@view-transition { navigation: auto; }");
    }
    if (!document.adoptedStyleSheets.includes(flightSheet)) {
      document.adoptedStyleSheets = [...document.adoptedStyleSheets, flightSheet];
    }
  }
  function disableNative() {
    if (flightSheet) document.adoptedStyleSheets = document.adoptedStyleSheets.filter(sheet => sheet !== flightSheet);
  }

  function read() {
    try {
      const value = JSON.parse(sessionStorage.getItem(key));
      if (value?.url !== location.href || Date.now() - value.time > 10000) return null;
      if (![value.time, value.x, value.y, value.width, value.height].every(Number.isFinite)
        || value.width <= 0 || value.height <= 0) return null;
      sessionStorage.removeItem(key);
      return value;
    } catch { return null; }
  }
  const incoming = read();
  if (incoming && canMove()) {
    enableNative();
    root.classList.add(incoming.mode === "exit" ? "home-flight-exit-target" : incoming.mode === "cart" ? "cart-flight-target" : "home-flight-target");
    // The marker is after the complete landing logo/menu, including streamed HTML.
    const expect = document.createElement("link");
    expect.rel = "expect"; expect.href = incoming.mode ? "#site-ready" : "#landing-ready";
    expect.setAttribute("blocking", "render");
    document.head.append(expect);
  }

  function makeCloud(parent, target = false) {
    const element = document.createElement("span");
    element.className = "home-flight-cloud" + (target ? " home-flight-cloud--target" : "");
    element.setAttribute("aria-hidden", "true");
    element.style.backgroundImage = `url("${cloudURL}")`;
    parent.append(element);
    return element;
  }
  function warm(event) {
    if (!canMove() || warmImage || !event.target.closest?.(brandSelector)) return;
    warmImage = new Image(); warmImage.src = cloudURL;
  }
  document.addEventListener("pointerover", warm, true);
  document.addEventListener("pointerdown", warm, true);
  document.addEventListener("focusin", warm);
  document.addEventListener("click", event => {
    const brand = event.target.closest?.(brandSelector);
    if (!brand || !canMove() || event.defaultPrevented || event.button !== 0
      || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey
      || brand.download || (brand.target && brand.target !== "_self")) return;
    const url = new URL(brand.href);
    const art = brand.querySelector(".brand-logo");
    if (!art || url.origin !== location.origin || url.href === location.href) return;
    const box = art.getBoundingClientRect();
    outgoing = { url: url.href, time: Date.now(), x: box.x, y: box.y,
      width: box.width, height: box.height, background: getComputedStyle(document.body).backgroundColor };
    try { sessionStorage.setItem(key, JSON.stringify(outgoing)); } catch { outgoing = null; return; }
    enableNative();
    root.classList.add("home-flight-source");
    for (const old of brand.querySelectorAll(".home-flight-cloud")) old.remove();
    makeCloud(brand);
    // Do not intercept the link or close its open panel/history first.
  });

  const rect = element => { const b = element.getBoundingClientRect(); return { x: b.x, y: b.y, width: b.width, height: b.height }; };
  function nameFor(element, name) {
    if (!element) return;
    element.style.viewTransitionName = name; element.dataset.homeTravelName = "";
  }
  document.addEventListener("click", event => {
    const link = event.target.closest?.(".landing-menu__link[href]");
    if (!link || !canMove() || event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey
      || link.download || (link.target && link.target !== "_self")) return;
    const url = new URL(link.href), logo = document.querySelector(".landing__logo-art");
    if (!logo || url.origin !== location.origin) return;
    const entries = [...document.querySelectorAll(".landing-menu__link")].map((anchor, index) => ({
      url: anchor.href, name: `home-link-${index}`, ...rect(anchor.querySelector(".landing-menu__text")),
    }));
    outgoing = { mode: "exit", url: url.href, time: Date.now(), ...rect(logo), links: entries };
    try { sessionStorage.setItem(key, JSON.stringify(outgoing)); } catch { outgoing = null; return; }
    enableNative();
    root.classList.add("home-flight-source-out");
    document.querySelector("[data-landing]").dataset.homeExit = "";
    makeCloud(logo.closest(".landing__logo"), true);
    for (const [index, anchor] of [...document.querySelectorAll(".landing-menu__link")].entries()) nameFor(anchor.querySelector(".landing-menu__text"), `home-link-${index}`);
  }, true);

  // Cart return uses the same native transition owner, avoiding two competing
  // pageswap handlers. Only geometry is carried, never an order or form.
  window.SwedeSweetsHomeTravel = { cartReturn(url, scroll = null) {
    const icon = document.querySelector('.site-header .site-nav-cart__icon');
    if (!canMove() || !icon) return;
    outgoing = { mode: "cart", url, time: Date.now(), ...rect(icon), scroll };
    try { sessionStorage.setItem(key, JSON.stringify(outgoing)); } catch { outgoing = null; return; }
    enableNative();
    nameFor(icon, "cart-return-icon");
  } };
  function fly(element, from, duration = 600, delay = 0) {
    const box = element.getBoundingClientRect();
    element.style.transformOrigin = "0 0";
    return element.animate([
      { transform: `translate(${from.x - box.x}px, ${from.y - box.y}px) scale(${from.width / box.width}, ${from.height / box.height})` },
      { transform: "none" },
    ], { duration, delay, easing: "cubic-bezier(.2,.7,.2,1)", fill: "backwards" }).finished.catch(() => {}).then(() => { element.style.transformOrigin = ""; });
  }
  async function enterNavbar(transition) {
    const logo = document.querySelector(".site-brand .brand-logo");
    if (incoming.mode === "cart") {
      const icon = document.querySelector(".site-header .site-nav-cart__icon, .landing__cart-link .site-nav-cart__icon");
      if (!icon) { transition?.skipTransition(); landed = true; reveal(); return; }
      nameFor(icon, "cart-return-icon");
      if (Array.isArray(incoming.scroll)) scrollTo({ left: incoming.scroll[0], top: incoming.scroll[1], behavior: "instant" });
      if (transition) await transition.finished.catch(() => {}); else await fly(icon, incoming, 360);
      if (Array.isArray(incoming.scroll)) scrollTo({ left: incoming.scroll[0], top: incoming.scroll[1], behavior: "instant" });
    } else {
      if (!logo) { transition?.skipTransition(); landed = true; reveal(); return; }
      nameFor(logo, "home-wordmark"); cloud = makeCloud(logo.closest(".site-brand"));
      const pairs = [];
      for (const entry of incoming.links || []) {
        const anchor = [...document.querySelectorAll(".site-header .site-nav__link[href]")].find(link => link.href === entry.url);
        const label = anchor?.querySelector(".site-nav__label");
        if (label) { nameFor(label, entry.name); pairs.push([label, entry]); }
      }
      if (transition) await transition.finished.catch(() => {});
      else await Promise.all([fly(logo, incoming, 650), ...pairs.map(([label, entry], index) => fly(label, entry, 480, index * 50))]);
    }
    landed = true; reveal();
    if (incoming.mode === "exit") {
      const active = document.querySelector('.site-header .site-nav__link[aria-current="page"]');
      active?.classList.add("is-nav-arriving"); setTimeout(() => active?.classList.remove("is-nav-arriving"), 220);
    }
  }

  function prepare() {
    landing = document.querySelector("[data-landing]");
    hero = landing?.querySelector(".landing__logo");
    if (!incoming || !canMove() || !hero) return false;
    landing.classList.add("landing--seen");
    landing.dataset.homeArrival = "flying";
    for (const element of landing.querySelectorAll(".landing__top, .landing__menu, .landing__bottom")) element.inert = true;
    cloud = makeCloud(hero, true);
    return true;
  }
  function reveal() {
    // Let the native pseudo-tree finish teardown before opting out again.
    requestAnimationFrame(() => requestAnimationFrame(disableNative));
    root.classList.remove("home-flight-target", "home-flight-exit-target", "cart-flight-target");
    for (const element of document.querySelectorAll("[data-home-travel-name]")) {
      element.style.removeProperty("view-transition-name");
      delete element.dataset.homeTravelName;
    }
    for (const element of document.querySelectorAll(".home-flight-cloud")) element.remove();
    if (!landing) return;
    delete landing.dataset.homeArrival;
    for (const element of landing.querySelectorAll(".landing__top, .landing__menu, .landing__bottom")) element.inert = false;
    cloud?.remove();
  }
  async function settle() {
    if (landed) return;
    landed = true;
    if (!landing || !canMove()) { reveal(); return; }
    landing.dataset.homeArrival = "braking";
    // A small squash/stretch gives the engraved lobes a braking after-sway;
    // the lettering remains steady as the menu appears.
    const brake = cloud?.animate([
      { transform: "scale(1)" },
      { transform: "scale(1.08, .92)", offset: .25 },
      { transform: "scale(.96, 1.04)", offset: .6 },
      { transform: "scale(1)" },
    ], { duration: 300, easing: "ease-out" });
    const links = landing.querySelectorAll(".landing-menu li, .landing__tagline, .landing__top, .landing__bottom");
    for (const [index, element] of [...links].entries()) {
      element.animate([{ opacity: 0, transform: "translateY(8px)" }, { opacity: 1, transform: "none" }],
        { duration: 180, delay: Math.min(index * 25, 100), easing: "ease-out", fill: "backwards" });
    }
    await brake?.finished.catch(() => {});
    reveal();
  }
  async function start(transition) {
    if (started) return;
    started = true;
    if (incoming?.mode && canMove()) { await enterNavbar(transition); return; }
    if (!prepare()) { transition?.skipTransition(); reveal(); return; }
    if (transition) {
      await transition.finished.catch(() => {});
    } else {
      // Browsers without cross-document transitions still get the flight.
      // Their old document is unavailable, so fade its surface colour to blue.
      const box = hero.getBoundingClientRect();
      const flight = hero.animate([
        { transform: `translate(${incoming.x - box.x}px, ${incoming.y - box.y}px) scale(${incoming.width / box.width}, ${incoming.height / box.height})` },
        { transform: "none" },
      ], { duration: 700, easing: "cubic-bezier(.2,.7,.2,1)" });
      hero.style.transformOrigin = "0 0";
      landing.animate([{ backgroundColor: incoming.background }, { backgroundColor: getComputedStyle(landing).backgroundColor }], { duration: 650, easing: "ease-out" });
      await flight.finished.catch(() => {});
      hero.style.transformOrigin = "";
    }
    void settle();
  }
  window.addEventListener("pageswap", event => {
    // A skipped/disabled native transition rejects ready; it is an expected fallback.
    event.viewTransition?.ready.catch(() => {});
    event.viewTransition?.updateCallbackDone.catch(() => {});
    event.viewTransition?.finished.catch(() => {});
    if (!outgoing || !canMove() || event.activation?.entry?.url !== outgoing.url) event.viewTransition?.skipTransition();
  });
  window.addEventListener("pagereveal", event => {
    event.viewTransition?.ready.catch(() => {});
    event.viewTransition?.updateCallbackDone.catch(() => {});
    event.viewTransition?.finished.catch(() => {});
    if (!incoming || !canMove()) { event.viewTransition?.skipTransition(); return; }
    void start(event.viewTransition);
  });
  document.addEventListener("DOMContentLoaded", () => {
    // Fallback for browsers without pagereveal, or a skipped native transition.
    if (incoming) setTimeout(() => { if (!started) void start(null); }, 50);
  });
  window.addEventListener("pageshow", event => {
    if (!event.persisted) return;
    root.classList.remove("home-flight-source", "home-flight-source-out", "home-flight-target", "home-flight-exit-target", "cart-flight-target");
    document.querySelector("[data-home-exit]")?.removeAttribute("data-home-exit");
    for (const element of document.querySelectorAll(".home-flight-cloud")) element.remove();
    reveal(); outgoing = null;
  });
  if (incoming) setTimeout(() => { if (!landed) { started = true; landed = true; reveal(); } }, 2000);
})();
