/* One owner for landing, header, cart and login travel. Only navigation
   geometry crosses documents; forms and order data remain server-owned. */
(() => {
  "use strict";
  const root = document.documentElement;
  const mobile = matchMedia("(max-width: 767px)");
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const key = "swedesweets-home-flight";
  const canMove = () => ["cloud", "wordmark"].includes(window.SwedeSweetsEffects?.profile().travel) && root.dataset.siteZone !== "ops" && !reduced.matches;
  const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
  const rect = element => {
    if (!element) return null;
    const b = element.getBoundingClientRect();
    return b.width > 0 && b.height > 0 ? { x: b.x, y: b.y, width: b.width, height: b.height } : null;
  };
  const homeClasses = ["home-flight-source", "home-flight-source-out", "home-flight-departing", "home-flight-target", "home-flight-exit-target", "home-flight-login-target", "cart-flight-target"];
  let outgoing = null, started = false, landed = false, landing = null, flightSheet = null, capturedSwap = false;
  const sourceMotions = [];
  function enableNative() {
    if (!("adoptedStyleSheets" in document) || !CSSStyleSheet.prototype.replaceSync) return;
    if (!flightSheet) {
      flightSheet = new CSSStyleSheet();
      flightSheet.replaceSync("@view-transition { navigation: auto; }");
    }
    if (!document.adoptedStyleSheets.includes(flightSheet)) document.adoptedStyleSheets = [...document.adoptedStyleSheets, flightSheet];
  }
  function disableNative() {
    if (flightSheet) document.adoptedStyleSheets = document.adoptedStyleSheets.filter(sheet => sheet !== flightSheet);
  }
  function remember(value) {
    try { sessionStorage.setItem(key, JSON.stringify(value)); outgoing = value; enableNative(); return true; }
    catch { return false; }
  }
  function read() {
    try {
      const value = JSON.parse(sessionStorage.getItem(key));
      if (value?.url !== location.href || Date.now() - value.time > 10000) return null;

      if (![value.time, value.x, value.y, value.width, value.height].every(Number.isFinite) || value.width <= 0 || value.height <= 0) return null;
      return value;
    } catch { return null; }
  }
  const incoming = read();
  if (incoming && canMove()) {
    enableNative();
    root.classList.add(incoming.mode === "exit" ? "home-flight-exit-target" : incoming.mode === "login" ? "home-flight-login-target" : incoming.mode === "cart" ? "cart-flight-target" : "home-flight-target");
    root.dataset.homePhase = "flight";
    if (incoming.cloudBrand) root.dataset.homeCloudBrand = "";
    if (incoming.cart) root.dataset.homeCart = "";
    const expect = document.createElement("link");
    expect.rel = "expect"; expect.href = incoming.mode === "home" ? "#landing-ready" : "#site-ready";
    expect.setAttribute("blocking", "render"); document.head.append(expect);
  }
  function nameFor(element, name) {
    if (!element) return;
    element.style.viewTransitionName = name; element.dataset.homeTravelName = "";
  }
  function entries(selector, chosen) {
    return [...document.querySelectorAll(selector)].flatMap((anchor, index) => {
      const box = rect(anchor);
      return box && (!mobile.matches || (chosen ? anchor === chosen : anchor.getAttribute("aria-current") === "page")) ? [{ url: anchor.href, name: `home-link-${index}`, current: chosen ? anchor === chosen : anchor.getAttribute("aria-current") === "page", ...box }] : [];
    });
  }
  function matchLinks(record, selector) {
    return (record.links || []).flatMap(entry => {
      const anchor = [...document.querySelectorAll(selector)].find(link => link.href === entry.url && rect(link));
      if (!anchor) return [];
      anchor.toggleAttribute("data-home-chosen", entry.current);
      nameFor(anchor, entry.name); return [[anchor, entry]];
    });
  }
  function normalClick(event, link) {
    return link && canMove() && !event.defaultPrevented && event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey
      && !link.download && (!link.target || link.target === "_self") && new URL(link.href).origin === location.origin;
  }
  async function animate(element, frames, options) {
    if (!element) return;
    const motion = element.animate(frames, options);
    if (options.fill === "forwards") sourceMotions.push(motion);
    await motion.finished.catch(() => {});
  }
  function fly(element, from, duration = 650, delay = 0) {
    const box = rect(element);
    if (!box || !from) return Promise.resolve();
    element.style.transformOrigin = "0 0";
    return animate(element, [
      { transform: `translate(${from.x - box.x}px, ${from.y - box.y}px) scale(${from.width / box.width}, ${from.height / box.height})` },
      { transform: "none" },
    ], { duration, delay, easing: window.SwedeSweetsHomeDeparture?.continuation(incoming) || "cubic-bezier(.2,.7,.2,1)", fill: "backwards" }).then(() => { element.style.transformOrigin = ""; });
  }
  function headerCart() { return document.querySelector(".site-header .site-nav-cart__trigger"); }
  function headerMenu() { return document.querySelector(".site-header .site-menu > summary"); }
  function startHome(url) {
    if (!canMove() || outgoing) return false;
    const brand = document.querySelector(".site-brand .brand-logo, .entrance-header__brand");
    const cloudBrand = brand?.matches(".entrance-header__brand--landing");
    const box = rect(brand);
    if (!box) return false;
    const cart = rect(headerCart());
    const record = { mode: "home", url, time: Date.now(), ...box, cloudBrand, links: entries(".site-header .site-nav__link[href]"), cart, menu: rect(headerMenu()) };
    if (!remember(record)) return false;
    root.classList.add("home-flight-departing");
    if (cloudBrand) root.dataset.homeCloudBrand = "";
    root.classList.add("home-flight-source");
    nameFor(brand, cloudBrand ? "home-brand" : "home-wordmark");
    const pairs = matchLinks(record, ".site-header .site-nav__link[href]");
    if (cart) nameFor(headerCart(), "home-cart");
    if (record.menu) nameFor(headerMenu(), "home-menu");
    window.SwedeSweetsHomeDeparture?.start(record, { brand, links: pairs, cart: headerCart(), menu: headerMenu() });
    remember(record);
    location.assign(url);
    return true;
  }
  document.addEventListener("click", event => {
    const brand = event.target.closest?.("a.site-brand[href], a.entrance-header__brand[href]");
    if (!normalClick(event, brand) || brand.href === location.href) return;
    if (outgoing || startHome(brand.href)) event.preventDefault();
  });
  document.addEventListener("click", event => {
    const link = event.target.closest?.(".landing-menu__link[href], .landing__cart-link[href], a.landing__account[href]");
    if (!normalClick(event, link)) return;
    if (outgoing) { event.preventDefault(); return; }
    landing = document.querySelector("[data-landing]");
    const login = link.matches(".landing__account"), cart = link.matches(".landing__cart-link");
    const brand = landing?.querySelector(login ? ".landing__logo" : ".landing__logo-art");
    const box = rect(brand);
    if (!box) return;
    const record = { mode: login ? "login" : "exit", url: link.href, time: Date.now(), ...box,
      cloudBrand: login, links: login || cart ? [] : entries(".landing-menu__link[href]", link), cart: cart ? rect(link) : null,
      sideCart: !login && !cart ? rect(landing.querySelector(".landing__cart-link")) : null,
      menu: !login ? rect(landing.querySelector(".site-menu > summary")) : null };
    if (!remember(record)) return;
    if (cart) document.dispatchEvent(new Event("cart-navigation-start"));
    event.preventDefault();
    root.classList.add("home-flight-source-out");
    if (login) root.dataset.homeCloudBrand = "";
    if (cart) root.dataset.homeCart = "";
    landing.dataset.homeExit = login ? "login" : cart ? "cart" : "nav";
    let pairs = [];
    if (!login && !cart) {
      pairs = matchLinks(record, ".landing-menu__link[href]");
      link.dataset.homeChosen = "";
    }
    if (cart) { link.dataset.homeChosen = ""; nameFor(link, "home-cart"); }
    const sideCart = record.sideCart ? landing.querySelector(".landing__cart-link") : null;
    const menu = record.menu ? landing.querySelector(".site-menu > summary") : null;
    if (sideCart) nameFor(sideCart, "home-cart");
    if (menu) nameFor(menu, "home-menu");
    nameFor(brand, login ? "home-brand" : "home-wordmark");
    window.SwedeSweetsHomeDeparture?.start(record, { brand, links: pairs, cart: cart ? link : null, sideCart, menu });
    remember(record);
    location.assign(record.url);
    // Fold login controls while the request and brand travel are underway.
    // Login folds its controls towards the cloud before the cloud moves.
    void (async () => {
      if (login) {
        const target = brand.getBoundingClientRect();
        await Promise.all([...landing.querySelectorAll(".landing__menu, .landing__tagline, .landing__top, .landing__bottom")].map(element => {
          const b = element.getBoundingClientRect();
          return animate(element, [{ opacity: 1, transform: "none" }, { opacity: 0, transform: `translate(${target.x + target.width / 2 - b.x - b.width / 2}px, ${target.y + target.height / 2 - b.y - b.height / 2}px) scale(.08)` }],
            { duration: 260, easing: "ease-in", fill: "forwards" });
        }));
      }
    })();
  }, true);

  // Existing cart-return callers can hand over the whole return to landing.
  // Other browsing destinations retain their small icon-only return.
  window.SwedeSweetsHomeTravel = { cartReturn(url, scroll = null) {
    if (outgoing) return true;
    const home = document.querySelector("a.site-brand[href]")?.href;
    if (home && new URL(url, location.href).pathname === new URL(home).pathname && startHome(url)) return true;
    const icon = document.querySelector(".site-header .site-nav-cart__icon"), box = rect(icon);
    if (!canMove() || !box) return false;
    if (remember({ mode: "cart", url, time: Date.now(), ...box, scroll })) nameFor(icon, "cart-return-icon");
    return false;
  } };
  const remaining = () => incoming?.continuous ? Math.max(60, incoming.remainingAtCapture ?? incoming.endAt - Date.now()) : 650;
  async function finishPage() {
    root.dataset.homePhase = "selection"; // the navbar rule begins here
    await pause(mobile.matches ? 120 : 80);
    if (mobile.matches && incoming.mode === "exit" && !incoming.cart) {
      root.dataset.homePhase = "bottom";
      await pause(180);
    }
    root.dataset.homePhase = "surface";
    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    root.dataset.homePhase = "content";
    const main = document.querySelector("main.site-main");
    await animate(main, [
      { opacity: 0, transform: "translateY(6px)" },
      { opacity: 1, transform: "none" },
    ], { duration: 220, easing: "ease-out", fill: "backwards" });
    landed = true; reveal();
  }
  async function enterPage(transition) {
    if (incoming.mode === "cart") {
      const icon = document.querySelector(".site-header .site-nav-cart__icon, .landing__cart-link .site-nav-cart__icon");
      if (!icon) { transition?.skipTransition(); reveal(); return; }
      nameFor(icon, "cart-return-icon");
      if (Array.isArray(incoming.scroll)) scrollTo({ left: incoming.scroll[0], top: incoming.scroll[1], behavior: "instant" });
      if (transition) await transition.finished.catch(() => {}); else await fly(icon, incoming, 360);
      if (Array.isArray(incoming.scroll)) scrollTo({ left: incoming.scroll[0], top: incoming.scroll[1], behavior: "instant" });
      landed = true; reveal(); return;
    }
    const brand = document.querySelector(incoming.cloudBrand ? ".entrance-header__brand" : ".site-brand .brand-logo");
    if (!brand) { transition?.skipTransition(); reveal(); return; }
    nameFor(brand, incoming.cloudBrand ? "home-brand" : "home-wordmark");
    const pairs = matchLinks(incoming, ".site-header .site-nav__link[href]");
    if (incoming.cart) { nameFor(headerCart(), "home-cart"); pairs.push([headerCart(), incoming.cart]); }
    if (incoming.sideCart) { nameFor(headerCart(), "home-cart"); pairs.push([headerCart(), incoming.sideCart]); }
    if (incoming.menu) { nameFor(headerMenu(), "home-menu"); pairs.push([headerMenu(), incoming.menu]); }
    if (transition) await transition.finished.catch(() => {});
    else await Promise.all([fly(brand, incoming, remaining(), incoming.delayAtCapture || 0), ...pairs.map(([element, from], index) => fly(element, from, remaining(), incoming.continuous ? incoming.delayAtCapture || 0 : index * 35))]);
    await finishPage();
  }
  function prepareHome() {
    landing = document.querySelector("[data-landing]");
    if (!landing) return null;
    landing.classList.add("landing--seen"); landing.dataset.homeArrival = "flying";
    for (const element of landing.querySelectorAll(".landing__top, .landing__menu, .landing__bottom")) element.inert = true;
    const brand = landing.querySelector(incoming.cloudBrand ? ".landing__logo" : ".landing__logo-art");
    nameFor(brand, incoming.cloudBrand ? "home-brand" : "home-wordmark");
    const pairs = matchLinks(incoming, ".landing-menu__link[href]");
    for (const [link, entry] of pairs) if (entry.current) {
      for (const other of landing.querySelectorAll(".landing-menu__link")) other.classList.toggle("landing-menu__link--chosen", other === link);
    }
    if (incoming.cart) {
      const cart = landing.querySelector(".landing__cart-link");
      if (cart) { nameFor(cart, "home-cart"); pairs.push([cart, incoming.cart]); }
    }
    if (incoming.menu) {
      const menu = landing.querySelector(".site-menu > summary");
      if (menu) { nameFor(menu, "home-menu"); pairs.push([menu, incoming.menu]); }
    }
    return { brand, pairs };
  }
  function reveal() {
    landed = true;
    requestAnimationFrame(() => requestAnimationFrame(disableNative));
    root.classList.remove(...homeClasses);
    root.style.removeProperty("--home-travel-remaining"); root.style.removeProperty("--home-travel-stagger"); root.style.removeProperty("--home-travel-easing");
    delete root.dataset.homePhase; delete root.dataset.homeCloudBrand; delete root.dataset.homeCart; delete root.dataset.homePrepared;
    for (const element of document.querySelectorAll("[data-home-travel-name]")) {
      element.style.removeProperty("view-transition-name"); delete element.dataset.homeTravelName;
    }
    for (const element of document.querySelectorAll("[data-home-chosen]")) element.removeAttribute("data-home-chosen");
    if (landing) {
      delete landing.dataset.homeArrival;
      for (const element of landing.querySelectorAll(".landing__top, .landing__menu, .landing__bottom")) element.inert = false;
    }
  }
  async function start(transition) {
    if (started) return;
    started = true;
    // A new document can parse its head before pageswap updates the record.
    // Re-read at reveal, after the old document has captured its final frame.
    const latest = read();
    if (incoming && latest) Object.assign(incoming, latest);
    try { sessionStorage.removeItem(key); } catch {}
    if (incoming?.continuous) {
      root.style.setProperty("--home-travel-remaining", `${remaining()}ms`);
      root.style.setProperty("--home-travel-stagger", `${incoming.delayAtCapture || 0}ms`);
      root.style.setProperty("--home-travel-easing", window.SwedeSweetsHomeDeparture?.continuation(incoming) || "ease-out");
    }
    window.SwedeSweetsCurrentNav?.sync();
    if (!incoming || !canMove()) { transition?.skipTransition(); reveal(); return; }
    root.dataset.homePrepared = "";
    if (incoming.mode !== "home") { await enterPage(transition); return; }
    const prepared = prepareHome();
    if (!prepared) { transition?.skipTransition(); reveal(); return; }
    if (transition) await transition.finished.catch(() => {});
    else await Promise.all([fly(prepared.brand, incoming, remaining(), incoming.delayAtCapture || 0), ...prepared.pairs.map(([element, from], index) => fly(element, from, remaining(), incoming.continuous ? incoming.delayAtCapture || 0 : index * 35))]);
    landing.dataset.homeArrival = "braking"; root.dataset.homePhase = "selection";
    for (const element of landing.querySelectorAll(".landing__tagline, .landing__top, .landing__bottom")) {
      // The returning cart has its own flight, so don't fade its parent.
      if (incoming.cart && element.matches(".landing__top")) continue;
      void animate(element, [{ opacity: 0, transform: "translateY(8px)" }, { opacity: 1, transform: "none" }], { duration: 180, easing: "ease-out" });
    }
    await pause(incoming.cloudBrand ? 180 : 620); reveal();
  }
  function watchTransition(transition) {
    transition?.ready.catch(() => {}); transition?.updateCallbackDone.catch(() => {}); transition?.finished.catch(() => {});
  }
  window.addEventListener("pageswap", event => {
    watchTransition(event.viewTransition);
    if (outgoing) { window.SwedeSweetsHomeDeparture?.capture(outgoing); remember(outgoing); capturedSwap = true; }
    if (!outgoing || !canMove() || event.activation?.entry?.url !== outgoing.url) event.viewTransition?.skipTransition();
  });
  window.addEventListener("pagereveal", event => {
    watchTransition(event.viewTransition);
    if (!incoming || !canMove()) { event.viewTransition?.skipTransition(); return; }
    void start(event.viewTransition);
  });
  window.addEventListener("pagehide", () => {
    // pageswap owns the old snapshot. Do not overwrite its geometry with a
    // second, later sample in pagehide; unsupported browsers use this fallback.
    if (outgoing && !capturedSwap) { window.SwedeSweetsHomeDeparture?.capture(outgoing); remember(outgoing); }
  });
  document.addEventListener("DOMContentLoaded", () => {
    // pagereveal owns native snapshots. Fallback starts before a paint, not
    // after a 50ms timer that can flash all triggers at their final positions.
    if (incoming) requestAnimationFrame(() => { if (!started) void start(null); });
  });
  window.addEventListener("pageshow", event => {
    if (!event.persisted) return;
    window.SwedeSweetsHomeDeparture?.clear();
    for (const animation of sourceMotions.splice(0)) animation.cancel();
    document.querySelector("[data-home-exit]")?.removeAttribute("data-home-exit");
    reveal(); outgoing = null; capturedSwap = false;
  });
  if (incoming) setTimeout(() => { if (!landed) { started = true; reveal(); } }, 5000);
})();
