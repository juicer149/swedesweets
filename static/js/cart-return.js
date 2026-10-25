/* The top return goes to the browsing page; the bottom action always browses
   the channel's catalog. An order/payment POST is never cancelled or replayed. */
(() => {
  "use strict";
  const key = "swedesweets-cart-origin";
  const root = document.documentElement;
  function origin() {
    try {
      const value = JSON.parse(sessionStorage.getItem(key));
      const url = new URL(value.url);
      return url.origin === location.origin && Date.now() - value.time < 7200000 ? value : null;
    } catch { return null; }
  }
  function remember() {
    if (document.querySelector(".site-nav-cart[open]")) return;
    if (root.hasAttribute("data-checkout-flow") || !document.querySelector("[data-public-page], [data-landing], [data-product-page]")) return;
    try { sessionStorage.setItem(key, JSON.stringify({ url: location.href, time: Date.now(), scroll: [scrollX, scrollY] })); } catch {}
  }
  function update() {
    const trigger = document.querySelector(".site-nav-cart > summary");
    const backLabel = document.querySelector("[data-cart-return]")?.getAttribute("aria-label");
    if (trigger) {
      trigger.dataset.cartLabel ||= trigger.getAttribute("aria-label") || "";
      trigger.setAttribute("aria-label", root.hasAttribute("data-checkout-flow") && backLabel ? backLabel : trigger.dataset.cartLabel);
    }
    for (const link of document.querySelectorAll("[data-cart-return]")) {
      link.dataset.fallback ||= link.href;
      link.href = origin()?.url || link.dataset.fallback;
    }
  }
  document.addEventListener("click", event => {
    if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const summary = event.target.closest('.site-nav-cart > summary');
    const arrow = event.target.closest("[data-cart-return]");
    const bottom = event.target.closest("[data-continue-shopping]");
    const entry = event.target.closest(".landing__cart-link, a[href]");
    const cart = document.querySelector('.site-nav-cart[data-cart-page-url]');
    if (!root.hasAttribute("data-checkout-flow")) {
      if (summary || entry?.matches(".landing__cart-link") || (entry && new URL(entry.href).pathname === cart?.dataset.cartPageUrl)) remember();
    }
    const fullFlow = root.hasAttribute("data-checkout-flow");
    if ((!summary || !fullFlow) && !arrow && !bottom) return;
    if (window.SwedeSweets?.orderFlow?.busy()) { event.preventDefault(); event.stopImmediatePropagation(); return; }
    if (arrow && !fullFlow && cart?.open) {
      event.preventDefault(); event.stopImmediatePropagation();
      document.dispatchEvent(new CustomEvent("mobile-menu-request", { detail: { key: null, restoreFocus: true } }));
      return;
    }
    const saved = origin();
    const back = document.querySelector("[data-cart-return]");
    const destination = bottom?.href || saved?.url || back?.dataset.fallback || back?.href;
    if (!destination) return;
    event.preventDefault(); event.stopImmediatePropagation();
    window.SwedeSweetsHomeTravel?.cartReturn(destination, bottom ? null : saved?.scroll);
    location.assign(destination);
  }, true);
  document.addEventListener("DOMContentLoaded", update);
  document.addEventListener("order-flow-chrome", update);
  document.addEventListener("navbar-cart-refreshed", update);
  update();
})();
