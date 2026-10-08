/*
  A catalog product's page (includes/catalog/product.html):

  - when the buyer picks another offer chip, the price and the stock line
    follow it;
  - Add is sent in the background, as on a catalog tile: the quantity and
    the button give way to the status burst (the dots, then the green
    cart), the navbar's cart jumps, and the buyer stays on the page. A
    problem is said under it.

  Without JavaScript the form is sent as usual (and the catalog opens).
*/
(() => {
  "use strict";

  const offers = Array.from(
    document.querySelectorAll(
      ".product__offers input[name='commercial_price_id']"
    )
  );
  const price = document.querySelector("[data-product-price]");
  const stock = document.querySelector("[data-product-stock]");

  if (offers.length === 0) {
    return;
  }

  function render() {
    const chosen = offers.find((offer) => offer.checked);

    if (!chosen) {
      return;
    }

    if (price) {
      price.textContent = chosen.dataset.priceLabel || "";
      price.hidden = !chosen.dataset.priceLabel;
    }

    if (stock) {
      const low = chosen.dataset.stockLow === "true";
      stock.textContent = chosen.dataset.stockLabel || "";
      stock.classList.toggle("status-text--warning", low);
      stock.classList.toggle("status-text--success", !low);
    }
  }

  for (const offer of offers) {
    offer.addEventListener("change", render);
  }

  render();
})();

(() => {
  "use strict";

  const form = document.querySelector("[data-product-add-form]");

  if (!form || !window.fetch || !window.statusBurst) {
    return;
  }

  const add = form.querySelector("[data-product-add]");
  const status = form.querySelector("[data-product-status]");
  const feedback = form.querySelector("[data-product-feedback]");

  if (!add || !status) {
    return;
  }

  async function post() {
    const response = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { Accept: "application/json" },
      credentials: "same-origin",
    });

    let payload = {};
    try {
      payload = await response.json();
    } catch (error) {
      // not JSON: an error page
    }

    if (!response.ok || !payload.ok) {
      throw new Error(payload.message || "");
    }

    return payload;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (form.dataset.adding === "true") {
      return;
    }

    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    form.dataset.adding = "true";
    if (feedback) {
      feedback.textContent = "";
    }

    add.hidden = true;
    status.hidden = false;

    const { ok, value, error } = await window.statusBurst.run(status, "default", post);

    status.hidden = true;
    add.hidden = false;
    delete form.dataset.adding;

    if (ok) {
      if (feedback) {
        // Said for screen readers; the cart was the answer for the eye.
        feedback.classList.add("visually-hidden");
        feedback.textContent = value.message || "";
      }

      document.dispatchEvent(
        new CustomEvent("cart-changed", {
          detail: { source: "product", bump: true },
        })
      );
      return;
    }

    if (feedback) {
      feedback.classList.remove("visually-hidden");
      feedback.textContent = error?.message || form.dataset.errorMessage || "";
    }

    form.querySelector(".product__submit")?.focus();
  });
})();
