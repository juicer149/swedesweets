/**
 * The cart's quick add (business_portal/orders/cart.html): choosing a
 * product in the search field posts it at once; the page comes back with
 * the product in the order. Without this script a button posts it.
 */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-cart-quick-add]").forEach((form) => {
    const select = form.querySelector("select");

    if (!select) {
      return;
    }

    select.addEventListener("change", () => {
      if (!select.value || form.dataset.submitting) {
        return;
      }

      form.dataset.submitting = "true";
      form.classList.add("is-adding");

      if (select.tomselect) {
        select.tomselect.close();
        select.tomselect.blur();
        select.tomselect.lock();
      }

      form.requestSubmit();
    });
  });
});
