/* Keep the customer's navbar mounted between the four public reading/catalog
   pages. Forms, checkout, product history, Menu and ops keep their own owners. */
(() => {
  "use strict";
  if (document.documentElement.dataset.siteZone !== "public") return;
  const links = [...document.querySelectorAll(".site-header .site-nav__link[href]")];
  const routes = new Set(links.map(link => new URL(link.href).pathname));
  const surface = () => document.querySelector("main.site-main [data-public-page]");
  if (!surface() || !links.length) return;
  const app = window.SwedeSweets = window.SwedeSweets || {};
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const positions = new Map();
  const scriptLoads = new Map();
  let renderedURL = location.href;
  let request = null;
  let busy = false;
  const previousRestoration = history.scrollRestoration;
  history.scrollRestoration = "manual";

  const duration = (name, fallback) => {
    const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    const number = parseFloat(value);
    return Number.isFinite(number) ? number * (value.endsWith("ms") ? 1 : 1000) : fallback;
  };
  const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
  const signature = root => JSON.stringify([
    [...root.querySelectorAll(".site-header .site-nav__link[href]")].map(link => new URL(link.getAttribute("href"), location.origin).pathname),
    root.querySelector("[data-navbar-cart-container]")?.dataset.navbarCartUrl,
    [...root.querySelectorAll("[data-site-menu] a[href], [data-site-menu] form[action]")].map(e => e.getAttribute("href") || e.getAttribute("action")),
  ]);
  const allowed = url => url.origin === location.origin && routes.has(url.pathname);
  const panelOpen = () => document.querySelector("details[data-mobile-menu][open], dialog[open]");
  const overlay = () => panelOpen()
    || document.documentElement.classList.contains("catalog--detail-open");
  const isPageActive = () => Boolean(surface()) && (routes.has(location.pathname) || Boolean(history.state?.catalogProduct));

  function resetAnimation() {
    for (const link of links) {
      link.classList.remove("is-nav-leaving", "is-nav-arriving");
    }
  }
  function remember() {
    if (!busy && location.href === renderedURL) positions.set(renderedURL, [scrollX, scrollY]);
  }
  window.addEventListener("scroll", remember, { passive: true });
  window.addEventListener("pagehide", () => { history.scrollRestoration = previousRestoration; request?.abort(); });
  window.addEventListener("pageshow", () => { history.scrollRestoration = "manual"; });

  async function dependencies(page) {
    for (const source of page.querySelectorAll("script[data-public-page-script][src]")) {
      const url = new URL(source.getAttribute("src"), location.origin);
      if (url.origin !== location.origin || !/\/js\/(tabs|catalog_detail|catalog|smooth-details)(?:\.[a-f0-9]+)?\.js$/.test(url.pathname)) throw new Error("Unknown page script");
      if ([...document.scripts].some(script => script.src === url.href)) continue;
      if (!scriptLoads.has(url.href)) scriptLoads.set(url.href, new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = url.href; script.onload = resolve; script.onerror = reject;
        document.body.append(script);
      }));
      await scriptLoads.get(url.href);
    }
  }

  function metadata(page) {
    document.title = page.title;
    for (const name of ["description", "og:title", "og:description", "og:url", "og:image"]) {
      const selector = `meta[name="${name}"], meta[property="${name}"]`;
      const value = page.querySelector(selector)?.getAttribute("content");
      if (value !== undefined) document.querySelector(selector)?.setAttribute("content", value);
    }
    for (const next of document.querySelectorAll('[data-language-preferences] [name="next"]')) next.value = location.pathname + location.search;
  }

  async function visit(url, { pop = false, state = null } = {}) {
    request?.abort();
    const controller = new AbortController(); request = controller;
    remember(); busy = true; resetAnimation();
    document.querySelector("main.site-main")?.setAttribute("aria-busy", "true");
    let committed = false;
    try {
      const response = await fetch(url, { credentials: "same-origin", headers: { Accept: "text/html" }, signal: controller.signal, cache: "no-store" });
      const destination = new URL(response.url);
      if (!response.ok || !allowed(destination)) throw new Error("Different destination");
      const page = new DOMParser().parseFromString(await response.text(), "text/html");
      const nextMain = page.querySelector("main.site-main");
      const currentMain = document.querySelector("main.site-main");
      if (controller.signal.aborted || panelOpen() || (!pop && overlay())) return;
      if (!nextMain?.querySelector("[data-public-page]") || page.documentElement.dataset.siteZone !== "public"
        || page.documentElement.lang !== document.documentElement.lang || signature(page) !== signature(document)
        || page.querySelector('link[rel="stylesheet"]')?.getAttribute("href") !== document.querySelector('link[rel="stylesheet"]')?.getAttribute("href")) throw new Error("Different page shell");
      // A deployment must get a fresh document, not combine old controllers
      // with new versions of page scripts.
      for (const script of page.querySelectorAll("script[src]")) {
        const path = new URL(script.getAttribute("src"), location.origin).pathname;
        const file = path.replace(/\.[a-f0-9]+(?=\.js$)/, "");
        if ([...document.scripts].some(old => {
          const previous = new URL(old.src || location.href).pathname;
          return previous.replace(/\.[a-f0-9]+(?=\.js$)/, "") === file && previous !== path;
        })) throw new Error("New asset version");
      }
      if (controller.signal.aborted) return;
      const motion = document.documentElement.dataset.theme === "light" && !reduced.matches;
      const leaving = links.filter(link => link.getAttribute("aria-current") === "page");
      if (motion) {
        leaving.forEach(link => {
          link.classList.add("is-nav-leaving");
        });
        await pause(duration("--public-nav-collapse-time", 180) * 0.6);
      }
      if (controller.signal.aborted || panelOpen() || (!pop && overlay())) return;
      window.SwedeSweetsCatalog?.destroy();
      window.destroySmoothDetails?.(currentMain);
      const imported = document.importNode(nextMain, true);
      imported.querySelectorAll("script").forEach(script => script.remove());
      imported.setAttribute("aria-busy", "true");
      if (!pop) history.pushState({ publicPage: true }, "", destination.href);
      renderedURL = location.href;
      const nextLinks = [...page.querySelectorAll(".site-header .site-nav__link[href]")];
      links.forEach((link, index) => {
        const active = nextLinks[index].getAttribute("aria-current") === "page";
        link.classList.toggle("site-nav__link--active", active);
        if (active) { link.setAttribute("aria-current", "page"); if (motion) link.classList.add("is-nav-arriving"); }
        else link.removeAttribute("aria-current");
      });
      currentMain.replaceWith(imported);
      committed = true;
      const footer = document.querySelector("footer.site-footer");
      const nextFooter = page.querySelector("footer.site-footer");
      if (footer && nextFooter) footer.replaceWith(document.importNode(nextFooter, true));
      metadata(page);
      await dependencies(page);
      if (controller.signal.aborted) return;
      window.SwedeSweetsCatalog?.init();
      window.enhanceSelects?.(imported);
      window.SwedeSweetsTabs?.init(imported);
      window.enhanceSmoothDetails?.(imported);
      const position = pop ? positions.get(location.href) : null;
      window.scrollTo({ left: position?.[0] || 0, top: position?.[1] || 0, behavior: "instant" });
      const heading = imported.querySelector("h1");
      if (heading) { heading.setAttribute("tabindex", "-1"); heading.focus({ preventScroll: true }); }
      if (motion) {
        void imported.animate([{ opacity: 0.35 }, { opacity: 1 }], { duration: duration("--public-page-reveal-time", 160) }).finished.catch(() => {});
        setTimeout(() => { if (!controller.signal.aborted) resetAnimation(); }, duration("--public-nav-pop-time", 340));
      } else resetAnimation();
      document.dispatchEvent(new CustomEvent("public-page-ready", { detail: { page: surface()?.dataset.publicPage, pop, state } }));
    } catch (error) {
      if (!controller.signal.aborted) {
        if (pop) location.replace(url); else location.assign(url);
      }
    } finally {
      if (request === controller) {
        busy = false;
        if (!committed) resetAnimation();
        document.querySelector("main.site-main")?.removeAttribute("aria-busy");
      }
    }
  }

  document.addEventListener("click", event => {
    const link = event.target.closest(".site-header .site-nav__link[href]");
    if (!link || !isPageActive() || overlay() || event.defaultPrevented || event.button !== 0
      || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || link.download || (link.target && link.target !== "_self")
      || document.querySelector('[data-public-page] [data-state="adding"]')) return;
    const url = new URL(link.href);
    if (!allowed(url) || url.hash) return;
    event.preventDefault();
    if (url.pathname === new URL(renderedURL).pathname && !busy) return;
    void visit(url.href);
  });
  window.addEventListener("popstate", event => {
    if (!isPageActive() || document.querySelector("details[data-mobile-menu][open], dialog[open]")
      || event.state?.catalogProduct || event.state?.menuPanel) return;
    const url = new URL(location.href);
    if (!allowed(url) || url.pathname === new URL(renderedURL).pathname) return;
    event.stopImmediatePropagation();
    void visit(url.href, { pop: true, state: event.state });
  }, true);
  app.publicNavigation = { isPageActive, busy: () => busy };
})();
