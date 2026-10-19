/* Only tagged cart confirmations expire; ordinary messages/errors remain. */
(() => {
  "use strict";
  for (const notice of document.querySelectorAll("[data-cart-notice]")) {
    // Mobile sheets inert the underlying main; confirmations remain readable.
    document.body.append(notice);
    function position() {
      const anchor = notice.hasAttribute("data-cart-flow-notice")
        ? document.querySelector("[data-order-progress]")
        : document.querySelector(".site-nav-cart__trigger");
      if (!anchor?.getClientRects().length) return;
      const rect = anchor.getBoundingClientRect();
      notice.style.top = `${Math.max(12, rect.bottom + 12)}px`;
      notice.style.right = `${Math.max(16, Math.min(innerWidth - notice.offsetWidth - 16, innerWidth - rect.right))}px`;
    }
    position();
    requestAnimationFrame(position);
    document.addEventListener("mobile-menu-settled", position);
    document.addEventListener("order-flow-ready", position);
    window.addEventListener("resize", position);
    window.addEventListener("scroll", position, { passive: true });
    window.visualViewport?.addEventListener("resize", position);
    window.setTimeout(() => {
      notice.classList.add("is-leaving");
      window.setTimeout(() => {
        notice.remove();
        document.removeEventListener("mobile-menu-settled", position);
        document.removeEventListener("order-flow-ready", position);
        window.removeEventListener("resize", position);
        window.removeEventListener("scroll", position);
        window.visualViewport?.removeEventListener("resize", position);
      }, 180);
    }, 2800);
  }
})();
