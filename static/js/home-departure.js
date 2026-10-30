/* Start visible travel while the browser requests the next document. The next
   document receives the current geometry and only completes the remaining trip.
   No HTML is fetched twice, and page/form controllers keep their normal owner. */
(() => {
  "use strict";
  const layoutKey = "swedesweets-home-layout";
  const root = document.documentElement;
  const box = e => { const b = e?.getBoundingClientRect(); return b?.width && b.height ? { x: b.x, y: b.y, width: b.width, height: b.height } : null; };
  let parts = [], motions = [], previews = [], timers = [];
  function cloudState(element, pseudo = "::before") {
    const style = getComputedStyle(element, pseudo);
    // A pointer layer may have opacity 1 but no artwork. Carrying that
    // opacity to the navbar's real cloud would invent a flash at handoff.
    const painted = style.backgroundImage !== "none"
      || !["transparent", "rgba(0, 0, 0, 0)"].includes(style.backgroundColor);
    return {
      opacity: painted && style.visibility !== "hidden" && style.display !== "none" ? style.opacity : "0",
      transform: style.transform,
    };
  }
  function rememberLanding() {
    const brand = document.querySelector(".landing__logo-art");
    if (!brand) return;
    try { sessionStorage.setItem(layoutKey, JSON.stringify({ width: innerWidth, height: innerHeight, language: root.lang, theme: root.dataset.theme,
      brand: box(brand), cloud: box(document.querySelector(".landing__logo")), cart: box(document.querySelector(".landing__cart-link")), menu: box(document.querySelector(".landing__top .site-menu > summary")),
      links: [...document.querySelectorAll(".landing-menu__link")].map(link => ({ url: link.href, ...box(link) })) })); } catch {}
  }
  function preview(record) {
    const shell = document.createElement("div"); shell.className = "home-measure"; shell.inert = true;
    if (record.cloudBrand) {
      shell.innerHTML = '<header class="entrance-header entrance-header--landing"><a class="entrance-header__brand entrance-header__brand--landing"></a></header>';
      const svg = document.querySelector(".landing__logo-art").cloneNode(true); svg.setAttribute("class", "brand-logo entrance-header__logo");
      shell.querySelector("a").append(svg); document.body.append(shell); previews.push(shell);
      return { brand: box(shell.querySelector("a")), links: [] };
    }
    shell.innerHTML = '<header class="site-header"><div class="container"><nav class="site-nav"><a class="site-brand"></a><div class="site-nav__content"><div class="site-nav__links"></div><div class="site-nav__auth"></div></div><div class="site-nav-current"></div></nav></div></header>';
    const svg = document.querySelector(".landing__logo-art").cloneNode(true); svg.setAttribute("class", "brand-logo site-brand__logo"); shell.querySelector(".site-brand").append(svg);
    const strip = shell.querySelector(".site-nav__links"), host = shell.querySelector(".site-nav-current");
    for (const original of document.querySelectorAll(".landing-menu__link")) {
      const a = document.createElement("a"); a.className = "site-nav__link"; a.href = original.href; a.dataset.navCloud = original.dataset.navCloud;
      const icon = document.createElement("span"); icon.className = "site-nav__icon"; icon.append(original.querySelector(".landing-menu__icon svg").cloneNode(true));
      const text = document.createElement("span"); text.className = "site-nav__label"; text.textContent = original.querySelector(".landing-menu__text").textContent;
      a.append(icon, text);
      if (record.links.some(link => link.current && link.url === a.href)) { a.setAttribute("aria-current", "page"); a.classList.add("site-nav__link--active"); }
      (innerWidth < 768 && a.hasAttribute("aria-current") ? host : strip).append(a);
    }
    strip.style.setProperty("--site-nav-count", document.querySelectorAll(".landing-menu__link").length);
    const auth = shell.querySelector(".site-nav__auth"), originalCart = document.querySelector(".landing__cart-link");
    const cart = document.createElement("summary");
    if (originalCart) cart.append(...[...originalCart.childNodes].map(node => node.cloneNode(true)));
    cart.className = "site-nav-cart__trigger menu-dropdown-trigger";
    const cartSlot = document.createElement("div"); cartSlot.setAttribute("data-navbar-cart-container", "");
    const cartDetails = document.createElement("details"); cartDetails.className = "site-nav-cart";
    cartDetails.append(cart); cartSlot.append(cartDetails); auth.append(cartSlot);
    const menu = document.querySelector(".landing__top .site-menu > summary")?.cloneNode(true);
    if (menu) { const details = document.createElement("details"); details.className = "site-menu"; details.append(menu); auth.append(details); }
    if (record.cart) strip.style.display = "none";
    shell.querySelectorAll("[id]").forEach(e => e.removeAttribute("id"));
    document.body.append(shell); previews.push(shell);
    const cartBox = box(cart), header = box(shell.querySelector(".site-header"));
    if (record.cart && cartBox && header) { cartBox.x = innerWidth / 2 - cartBox.width / 2; cartBox.y = header.y + header.height / 2 - cartBox.height / 2; }
    return { brand: box(svg), cart: cartBox, menu: box(menu), links: [...shell.querySelectorAll(".site-nav__link")].map(link => ({ url: link.href, ...box(link) })) };
  }
  function homePreview(record) {
    // Direct visits may not have stored landing geometry yet. Measure the
    // same layout classes with the current brand and navigation labels.
    const shell = document.createElement("div"); shell.className = "home-measure"; shell.inert = true;
    shell.innerHTML = '<main class="landing landing--seen"><div class="landing__top"></div><div class="landing__stage"><div class="landing__brand"><h1 class="landing__logo"><span class="landing__logo-trigger"></span></h1><p class="landing__tagline">Sweden’s sweetest tradition</p></div><nav class="landing__menu"><div class="landing__menu-inner"><ul class="landing-menu"></ul></div></nav></div><div class="landing__bottom"><span class="landing__account">Login</span></div></main>';
    const svg = document.querySelector(".site-brand .brand-logo, .entrance-header__logo").cloneNode(true);
    svg.setAttribute("class", "brand-logo landing__logo-art"); svg.removeAttribute("style"); shell.querySelector(".landing__logo-trigger").append(svg);
    const links = [...document.querySelectorAll(".site-header .site-nav__link")].sort((a,b) => Number(a.dataset.navIndex) - Number(b.dataset.navIndex));
    for (const original of links) {
      const item = document.createElement("li"), a = document.createElement("a"); a.className = "landing-menu__link"; a.href = original.href;
      const icon = document.createElement("span"); icon.className = "ui-icon-block landing-menu__icon"; icon.append(original.querySelector(".site-nav__icon svg").cloneNode(true));
      const label = document.createElement("span"), text = document.createElement("span"); label.className = "landing-menu__label"; text.className = "landing-menu__text"; text.textContent = original.querySelector(".site-nav__label").textContent;
      label.append(text); a.append(icon,label); item.append(a); shell.querySelector("ul").append(item);
    }
    const cart = headerCartClone(); if (cart) shell.querySelector(".landing__top").append(cart);
    shell.querySelectorAll("[id], [data-home-travel-name]").forEach(e => { e.removeAttribute("id"); e.removeAttribute("data-home-travel-name"); e.style.removeProperty("view-transition-name"); });
    document.body.append(shell); previews.push(shell);
    const menu = document.querySelector(".site-header .site-menu > summary")?.cloneNode(true);
    if (menu) { const details = document.createElement("details"); details.className = "site-menu"; details.append(menu); shell.querySelector(".landing__top").append(details); }
    return { brand: box(record.cloudBrand ? shell.querySelector(".landing__logo") : svg), cart: box(cart), menu: box(menu), links: [...shell.querySelectorAll(".landing-menu__link")].map(a => ({ url: a.href, ...box(a) })) };
  }
  function headerCartClone() {
    const original = document.querySelector(".site-header .site-nav-cart__trigger");
    if (!original) return null;
    const cart = original.cloneNode(true); cart.className = "site-nav-cart__trigger landing__cart-link";
    cart.removeAttribute("aria-current"); cart.removeAttribute("style"); return cart;
  }
  function move(element, target, delay) {
    const from = box(element);
    if (!from || !target) return;
    element.style.transformOrigin = "0 0";
    const motion = element.animate([{ transform: "none" }, { transform: `translate(${target.x - from.x}px, ${target.y - from.y}px) scale(${target.width / from.width},${target.height / from.height})` }],
      { duration: 600, delay, easing: "cubic-bezier(.2,.7,.2,1)", fill: "forwards" });
    motions.push(motion); motion.finished.catch(() => {});
  }
  function start(record, elements) {
    let target;
    if (record.mode === "home") {
      try { const saved = JSON.parse(sessionStorage.getItem(layoutKey));
        if (saved?.width === innerWidth && saved.language === root.lang && saved.theme === root.dataset.theme) {
          const resize = b => b && ({ ...b, y: b.y * innerHeight / saved.height });
          target = { brand: resize(record.cloudBrand ? saved.cloud : saved.brand), cart: resize(saved.cart), menu: resize(saved.menu), links: saved.links.map(b => ({ ...resize(b), url: b.url })) };
        }
      } catch {}
      if (!target) target = homePreview(record);
    } else { rememberLanding(); target = preview(record); }
    if (!target) return;
    const delay = record.mode === "home" ? 180 : record.mode === "login" ? 260 : 180;
    record.departureDelay = delay;
    record.motionStartAt = Date.now() + delay;
    record.endAt = record.motionStartAt + 600; record.continuous = true;
    parts = [[elements.brand, record], ...(elements.links || [])];
    if (record.login) parts.push([document.querySelector("[data-login-travel]"), record.login]);
    if (elements.cart && record.cart) parts.push([elements.cart, record.cart]);
    if (elements.sideCart && record.sideCart) parts.push([elements.sideCart, record.sideCart]);
    if (elements.menu && record.menu) parts.push([elements.menu, record.menu]);
    move(elements.brand, target.brand, delay);
    for (const [element, entry] of elements.links || []) move(element, target.links.find(link => link.url === entry.url), delay);
    if (elements.cart) move(elements.cart, target.cart, delay);
    if (elements.sideCart) move(elements.sideCart, target.cart, delay);
    if (elements.menu) move(elements.menu, target.menu, delay);
    const waiting = document.createElement("div"); waiting.className = "home-network-wait"; waiting.setAttribute("role", "status");
    const burst = document.querySelector('template[data-status-burst="default"]')?.content.cloneNode(true);
    if (burst) waiting.append(burst);
    waiting.setAttribute("aria-label", document.documentElement.lang === "fr" ? "Chargement" : "Loading");
    previews.push(waiting);
    timers.push(setTimeout(() => { document.body.append(waiting); root.classList.add("home-flight-waiting"); }, delay + 650));
    previews.filter(e => e !== waiting).forEach(e => e.remove());
  }
  function capture(record) {
    if (!record?.continuous) return;
    // Geometry and progress must use the same rendered animation frame, not
    // wall time (which can run ahead while a new document is being prepared).
    const elapsed = Number(motions[0]?.currentTime ?? 0) - record.departureDelay;
    record.delayAtCapture = Math.max(0, -elapsed);
    record.remainingAtCapture = Math.max(60, 600 - Math.max(0, elapsed));
    record.progressAtCapture = Math.max(0, Math.min(1, elapsed / 600));
    for (const [element, entry] of parts) { const current = box(element); if (current) Object.assign(entry, current); }
    const chosen = parts.find(([, entry]) => entry.current)?.[0];
    if (record.mode === "exit" && chosen) {
      record.departingCloud = cloudState(chosen);
    }
  }
  function continuation(record) {
    const progress = record?.progressAtCapture || 0;
    if (progress >= .995) return "linear";
    const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
    // De Casteljau subdivision preserves velocity through a document handoff.
    const split = t => {
      const a = mix([0, 0], [.2, .7], t), b = mix([.2, .7], [.2, 1], t), c = mix([.2, 1], [1, 1], t);
      const d = mix(a, b, t), e = mix(b, c, t);
      return [mix(d, e, t), e, c];
    };
    let lo = 0, hi = 1;
    for (let i = 0; i < 20; i++) {
      const mid = (lo + hi) / 2;
      if (split(mid)[0][0] < progress) lo = mid; else hi = mid;
    }
    const [start, a, b] = split((lo + hi) / 2);
    const normalize = p => p.map((v, i) => (v - start[i]) / (1 - start[i]));
    return `cubic-bezier(${[...normalize(a), ...normalize(b)].map(v => v.toFixed(6)).join(",")})`;
  }
  function clear() {
    timers.splice(0).forEach(clearTimeout); motions.splice(0).forEach(m => { const target = m.effect?.target; m.cancel(); target?.style.removeProperty("transform-origin"); });
    previews.splice(0).forEach(e => e.remove()); parts = []; root.classList.remove("home-flight-waiting");
  }
  window.SwedeSweetsHomeDeparture = { start, capture, continuation, clear, cloudState };
})();
