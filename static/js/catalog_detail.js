/*
  A catalog product's page (includes/catalog/product.html): when the buyer
  picks another offer chip, the price and the stock line follow it.
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
