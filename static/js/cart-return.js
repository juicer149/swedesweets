/* The current cart icon returns to the browsing page; the bottom action browses
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
    const backLabel = document.querySelector("[data-continue-shopping]")?.textContent.trim();
    if (trigger) {
      trigger.dataset.cartLabel ||= trigger.getAttribute("aria-label") || "";
      trigger.setAttribute("aria-label", root.hasAttribute("data-checkout-flow") && backLabel ? backLabel : trigger.dataset.cartLabel);
    }
  }
  document.addEventListener("click", event => {
    if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const summary = event.target.closest('.site-nav-cart > summary');
    const bottom = event.target.closest("[data-continue-shopping]");
    const entry = event.target.closest(".landing__cart-link, a[href]");
    const cart = document.querySelector('.site-nav-cart[data-cart-page-url]');
    if (!root.hasAttribute("data-checkout-flow")) {
      if (summary || entry?.matches(".landing__cart-link") || (entry && new URL(entry.href).pathname === cart?.dataset.cartPageUrl)) remember();
    }
    const fullFlow = root.hasAttribute("data-checkout-flow");
    if ((!summary || !fullFlow) && !bottom) return;
    if (window.SwedeSweets?.orderFlow?.busy()) { event.preventDefault(); event.stopImmediatePropagation(); return; }
    const saved = origin();
    const fallback = document.querySelector("[data-cart-return-url]")?.dataset.cartReturnUrl || cart?.dataset.cartPageUrl;
    const destination = bottom?.href || saved?.url || fallback;
    if (!destination) return;
    event.preventDefault(); event.stopImmediatePropagation();
    const handled = window.SwedeSweetsHomeTravel?.cartReturn(destination, bottom ? null : saved?.scroll);
    if (!handled) location.assign(destination);
  }, true);
  document.addEventListener("cart-navigation-start", remember);
  document.addEventListener("DOMContentLoaded", update);
  document.addEventListener("order-flow-chrome", update);
  document.addEventListener("navbar-cart-refreshed", update);
  update();
})();
