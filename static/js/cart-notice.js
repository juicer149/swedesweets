/* Only tagged cart confirmations expire; ordinary messages/errors remain. */
(() => {
  "use strict";
  for (const notice of document.querySelectorAll("[data-cart-notice]")) {
    // Mobile sheets inert the underlying main; confirmations remain readable.
    document.body.append(notice);
    function position() {
      const anchor = document.querySelector(".site-nav-cart__trigger");
      if (!anchor?.getClientRects().length) return;
      const rect = anchor.getBoundingClientRect();
      notice.style.top = `${Math.max(12, rect.bottom + 12)}px`;
      notice.style.right = `${Math.max(16, Math.min(innerWidth - notice.offsetWidth - 16, innerWidth - rect.right))}px`;
    }
    position();
    window.addEventListener("resize", position);
    window.addEventListener("scroll", position, { passive: true });
    window.visualViewport?.addEventListener("resize", position);
    window.setTimeout(() => {
      notice.classList.add("is-leaving");
      window.setTimeout(() => {
        notice.remove();
        window.removeEventListener("resize", position);
        window.removeEventListener("scroll", position);
        window.visualViewport?.removeEventListener("resize", position);
      }, 180);
    }, 2800);
  }
})();
