/* Login/reset share their real header. Only GET form navigation is enhanced;
   submission and validation retain their existing server-owned handlers. */
(() => {
  "use strict";
  let busy = false;
  let currentPath = location.pathname;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  async function navigate(url, push) {
    if (busy) return;
    busy = true;
    const main = document.querySelector("main.site-main");
    const old = main?.querySelector(".screen");
    if (!old) { location.assign(url); return; }
    main.setAttribute("aria-busy", "true");
    try {
      const response = await fetch(url, { credentials: "same-origin", headers: { Accept: "text/html" } });
      if (!response.ok || new URL(response.url).origin !== location.origin) throw new Error("auth navigation");
      const doc = new DOMParser().parseFromString(await response.text(), "text/html");
      const next = doc.querySelector("main.site-main .screen");
      if (!next?.querySelector("[data-auth-link]")) throw new Error("unexpected form");
      // Resolve before insertion: the fetched document has no useful base URL.
      const form = next.querySelector("form");
      form.action = new URL(form.getAttribute("action") || response.url, response.url).href;
      const height = old.getBoundingClientRect().height;
      const positions = [".form-grid", ".page__actions"].map(selector => ({
        selector, top: old.querySelector(selector)?.getBoundingClientRect().top,
      }));
      if (!reduced.matches) await old.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 120, fill: "forwards" }).finished;
      old.replaceWith(next);
      window.passwordToggles?.(next);
      document.title = doc.title;
      currentPath = new URL(response.url).pathname;
      if (push) history.pushState({ ...(history.state || {}), authPage: true }, "", response.url);
      if (!reduced.matches) {
        const targetHeight = next.getBoundingClientRect().height;
        const movements = positions.flatMap(({ selector, top }) => {
          const element = next.querySelector(selector);
          if (!element || !Number.isFinite(top)) return [];
          return [element.animate([
            { transform: `translateY(${top - element.getBoundingClientRect().top}px)` },
            { transform: "none" },
          ], { duration: 240, easing: "ease-out" }).finished];
        });
        await Promise.all([
          ...movements,
          next.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 180 }).finished,
          next.animate([{ height: `${height}px` }, { height: `${targetHeight}px` }], { duration: 240, easing: "ease-out" }).finished,
        ]);
      }
      next.querySelector("input:not([type=hidden])")?.focus({ preventScroll: true });
    } catch { location.assign(url); }
    finally { busy = false; main.removeAttribute("aria-busy"); }
  }
  document.addEventListener("click", event => {
    const link = event.target.closest?.("a[data-auth-link]");
    if (!link || event.defaultPrevented || event.button || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    if (new URL(link.href).origin !== location.origin) return;
    event.preventDefault(); void navigate(link.href, true);
  });
  window.addEventListener("popstate", event => {
    if (location.pathname !== currentPath && document.querySelector("[data-auth-link]") && !event.state?.menuPanel) void navigate(location.href, false);
  });
})();
