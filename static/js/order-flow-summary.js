/* The order flow's summary row (includes/cart/summary.html in the cart
   pages, shown as the phone sheet's fixed row): keeps "N products" right
   as lines come and go. The retail subtotal is kept by storefront-cart.js
   ([data-cart-subtotal]). */
(() => {
  "use strict";
  function update() {
    for (const count of document.querySelectorAll(".order-flow-summary [data-cart-summary-count]")) {
      const page = count.closest(".cart-page");
      const lines = page?.querySelectorAll(".lines[data-cart-lines] > li, .cart-products > .cart-line").length || 0;
      const text = lines === 1 ? count.dataset.one : count.dataset.many.replace(/\d+/, String(lines));
      if (count.textContent !== text) count.textContent = text;
    }
  }
  new MutationObserver(update).observe(document.body, { childList: true, subtree: true });
  document.addEventListener("cart-changed", update);
  update();
})();
