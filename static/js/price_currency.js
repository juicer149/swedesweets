/*
 * A price field with EUR / SEK chips (ops_portal/products/includes/
 * price_field.html): the pressed chip's field shows, the other hides. It
 * opens on a currency whose price has an error, else on the first (EUR). A
 * chip whose currency has a price gets a dot, so a hidden price is not
 * forgotten.
 */
(() => {
  for (const field of document.querySelectorAll("[data-price-field]")) {
    const chips = [...field.querySelectorAll("[data-price-currency]")];
    const boxes = [...field.querySelectorAll("[data-price-input]")];

    const inputFor = (currency) => (
      boxes
        .find((box) => box.dataset.priceInput === currency)
        ?.querySelector("input")
    );

    function show(currency) {
      for (const box of boxes) {
        box.hidden = box.dataset.priceInput !== currency;
      }

      for (const chip of chips) {
        chip.setAttribute(
          "aria-pressed",
          String(chip.dataset.priceCurrency === currency)
        );
      }
    }

    function markPricedChips() {
      for (const chip of chips) {
        chip.classList.toggle(
          "price-field__currency--priced",
          Boolean(inputFor(chip.dataset.priceCurrency)?.value.trim())
        );
      }
    }

    for (const chip of chips) {
      chip.addEventListener("click", () => {
        show(chip.dataset.priceCurrency);
        inputFor(chip.dataset.priceCurrency)?.focus();
      });
    }

    field.addEventListener("input", markPricedChips);

    const withError = boxes.find((box) => box.hasAttribute("data-has-error"));

    show(withError?.dataset.priceInput ?? chips[0].dataset.priceCurrency);
    markPricedChips();
  }
})();
