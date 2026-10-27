/* Native home links, with a shared cloud/wordmark flight where supported.
   This head script registers pagereveal before the first rendering chance.
   Other navigation and reduced motion keep their normal behaviour. */
(() => {
  "use strict";
  const root = document.documentElement;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const key = "swedesweets-home-flight";
  const canMove = () => ["cloud", "wordmark"].includes(window.SwedeSweetsEffects?.profile().travel) && root.dataset.siteZone !== "ops" && !reduced.matches;
  const brandSelector = "a.site-brand[href], a.entrance-header__brand[href]";
  let outgoing = null;
  let started = false;
  let landed = false;
  let hero = null;
  let landing = null;
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
    root.dataset.homePhase = "flight";
    // Wait for the destination geometry, including streamed HTML.
    const expect = document.createElement("link");
    expect.rel = "expect"; expect.href = ["exit", "cart"].includes(incoming.mode) ? "#site-ready" : "#landing-ready";
    expect.setAttribute("blocking", "render");
    document.head.append(expect);
  }

  const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
  function headerEntries() {
    return [...document.querySelectorAll(".site-header .site-nav__link[href]")].map((anchor, index) => ({
      url: anchor.href, name: `home-link-${index}`, current: anchor.getAttribute("aria-current") === "page",
      ...rect(anchor.querySelector(".site-nav__label")),
    }));
  }
  document.addEventListener("click", event => {
    const brand = event.target.closest?.(brandSelector);
    if (!brand || !canMove() || event.defaultPrevented || event.button !== 0
      || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey
      || brand.download || (brand.target && brand.target !== "_self")) return;
    const url = new URL(brand.href);
    const art = brand.querySelector(".brand-logo");
    if (!art || url.origin !== location.origin || url.href === location.href) return;
    const box = art.getBoundingClientRect();
    if (outgoing) { event.preventDefault(); return; }
    outgoing = { mode: "home", url: url.href, time: Date.now(), x: box.x, y: box.y,
      width: box.width, height: box.height, links: headerEntries() };
    try { sessionStorage.setItem(key, JSON.stringify(outgoing)); } catch { outgoing = null; return; }
    enableNative();
    event.preventDefault();
    root.classList.add("home-flight-departing");
    // Fade the page onto the landing surface before moving its navigation.
    // Open panels travel away with the page; their history is never closed first.
    void pause(220).then(() => {
      root.classList.add("home-flight-source");
      outgoing.links.forEach(entry => {
        const anchor = [...document.querySelectorAll(".site-header .site-nav__link")].find(link => link.href === entry.url);
        nameFor(anchor?.querySelector(".site-nav__label"), entry.name);
      });
      location.assign(url.href);
    });
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
      nameFor(logo, "home-wordmark");
      const pairs = [];
      for (const entry of incoming.links || []) {
        const anchor = [...document.querySelectorAll(".site-header .site-nav__link[href]")].find(link => link.href === entry.url);
        const label = anchor?.querySelector(".site-nav__label");
        if (label) { nameFor(label, entry.name); pairs.push([label, entry]); }
      }
      if (transition) await transition.finished.catch(() => {});
      else await Promise.all([fly(logo, incoming, 650), ...pairs.map(([label, entry], index) => fly(label, entry, 480, index * 50))]);
    }
    if (incoming.mode === "exit") {
      root.dataset.homePhase = "selection";
      const active = document.querySelector('.site-header .site-nav__link[aria-current="page"]');
      active?.classList.add("is-nav-arriving");
      const pop = getComputedStyle(root).getPropertyValue("--public-nav-pop-time").trim();
      const popMs = parseFloat(pop) * (pop.endsWith("ms") ? 1 : 1000);
      await pause((Number.isFinite(popMs) ? popMs : 200) + 180);
      active?.classList.remove("is-nav-arriving");
      root.dataset.homePhase = "rule";
      await pause(100);
      root.dataset.homePhase = "surface";
      await pause(160);
      root.dataset.homePhase = "content";
      const main = document.querySelector("main.site-main");
      await main?.animate([
        { opacity: 0, clipPath: "inset(0 0 100% 0)" },
        { opacity: 1, clipPath: `inset(0 0 ${Math.max(0, main.offsetHeight - innerHeight)}px 0)` },
      ], { duration: 340, easing: "ease-out", fill: "backwards" }).finished.catch(() => {});
    }
    landed = true; reveal();
  }

  function prepare() {
    landing = document.querySelector("[data-landing]");
    hero = landing?.querySelector(".landing__logo");
    if (!incoming || !canMove() || !hero) return false;
    landing.classList.add("landing--seen");
    landing.dataset.homeArrival = "flying";
    for (const element of landing.querySelectorAll(".landing__top, .landing__menu, .landing__bottom")) element.inert = true;
    for (const entry of incoming.links || []) {
      const anchor = [...landing.querySelectorAll(".landing-menu__link")].find(link => link.href === entry.url);
      nameFor(anchor?.querySelector(".landing-menu__text"), entry.name);
      if (anchor && entry.current) {
        for (const link of landing.querySelectorAll(".landing-menu__link")) link.classList.toggle("landing-menu__link--chosen", link === anchor);
      }
    }
    return true;
  }
  function reveal() {
    // Let the native pseudo-tree finish teardown before opting out again.
    requestAnimationFrame(() => requestAnimationFrame(disableNative));
    root.classList.remove("home-flight-target", "home-flight-exit-target", "cart-flight-target");
    delete root.dataset.homePhase;
    for (const element of document.querySelectorAll("[data-home-travel-name]")) {
      element.style.removeProperty("view-transition-name");
      delete element.dataset.homeTravelName;
    }
    if (!landing) return;
    delete landing.dataset.homeArrival;
    for (const element of landing.querySelectorAll(".landing__top, .landing__menu, .landing__bottom")) element.inert = false;
  }
  async function settle() {
    if (landed) return;
    landed = true;
    if (!landing || !canMove()) { reveal(); return; }
    landing.dataset.homeArrival = "braking";
    // The actual landing cloud/ink appears only after the wordmark lands.
    root.dataset.homePhase = "selection";
    const links = landing.querySelectorAll(".landing__tagline, .landing__top, .landing__bottom");
    for (const [index, element] of [...links].entries()) {
      element.animate([{ opacity: 0, transform: "translateY(8px)" }, { opacity: 1, transform: "none" }],
        { duration: 180, delay: Math.min(index * 25, 100), easing: "ease-out", fill: "backwards" });
    }
    await pause(440);
    reveal();
  }
  async function start(transition) {
    if (started) return;
    started = true;
    if (["exit", "cart"].includes(incoming?.mode) && canMove()) { await enterNavbar(transition); return; }
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
      const pairs = (incoming.links || []).map(entry => {
        const anchor = [...landing.querySelectorAll(".landing-menu__link")].find(link => link.href === entry.url);
        return [anchor?.querySelector(".landing-menu__text"), entry];
      }).filter(([label]) => label);
      await Promise.all([flight.finished.catch(() => {}), ...pairs.map(([label, entry], index) => fly(label, entry, 500, index * 45))]);
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
    root.classList.remove("home-flight-source", "home-flight-source-out", "home-flight-departing", "home-flight-target", "home-flight-exit-target", "cart-flight-target");
    document.querySelector("[data-home-exit]")?.removeAttribute("data-home-exit");
    reveal(); outgoing = null;
  });
  if (incoming) setTimeout(() => { if (!landed) { started = true; landed = true; reveal(); } }, 5000);
})();
