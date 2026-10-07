/*
  The catalog (includes/catalog/grid.html), shop and business portal alike:

  - the category tabs and the search hide the tiles that do not match;
  - a tile's "+" first asks for a quantity (the stepper, Add and ×), then
    Add posts the form as JSON, says "Added" for a moment, tells the
    navbar cart (cart-changed) and folds back to the "+".

  Without JavaScript the "+" simply posts the form: one of the tile's offer.
*/
(() => {
  "use strict";

  const catalog = document.querySelector(".catalog");

  if (!catalog) {
    return;
  }

  const tiles = Array.from(
    catalog.querySelectorAll("[data-catalog-product]")
  );
  const categoryButtons = Array.from(
    catalog.querySelectorAll("[data-catalog-category]")
  );
  const searchInput = catalog.querySelector("[data-catalog-search]");
  const noResults = catalog.querySelector("[data-catalog-no-results]");
  const feedback = catalog.querySelector("[data-catalog-feedback]");

  const addedLabel = catalog.dataset.catalogAddedLabel || "Added";
  const fallbackErrorMessage =
    catalog.dataset.catalogErrorMessage || "Could not add product.";

  const filter = {
    category: "all",
    query: "",
  };


  /* Filters ---------------------------------------------------------- */

  function normalize(value) {
    return String(value || "").trim().toLocaleLowerCase();
  }

  function tileMatches(tile) {
    const inCategory = (
      filter.category === "all"
      || tile.dataset.productCategory === filter.category
    );

    const inSearch = (
      !filter.query
      || normalize(tile.dataset.productSearch).includes(filter.query)
    );

    return inCategory && inSearch;
  }

  function applyFilters() {
    let visible = 0;

    for (const tile of tiles) {
      const show = tileMatches(tile);
      tile.hidden = !show;
      visible += show ? 1 : 0;
    }

    if (noResults) {
      noResults.hidden = visible !== 0;
    }

    for (const button of categoryButtons) {
      const active = button.dataset.catalogCategory === filter.category;
      button.classList.toggle("section-nav__link--active", active);
      button.setAttribute("aria-pressed", String(active));
    }
  }

  for (const button of categoryButtons) {
    button.addEventListener("click", () => {
      filter.category = button.dataset.catalogCategory || "all";
      applyFilters();
    });
  }

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      filter.query = normalize(searchInput.value);
      applyFilters();
    });
  }

  applyFilters();


  /* Quantity, then add ------------------------------------------------ */

  function setFeedback(message) {
    if (feedback) {
      feedback.textContent = message;
    }
  }

  function parts(form) {
    return {
      buy: form.querySelector("[data-catalog-purchase-default]"),
      quantity: form.querySelector("[data-catalog-purchase-quantity]"),
      input: form.querySelector("[data-quantity-input]"),
      confirm: form.querySelector("[data-catalog-confirm-button]"),
      add: form.querySelector("[data-catalog-add-button]"),
    };
  }

  function isAsking(form) {
    const { quantity } = parts(form);
    return Boolean(quantity && !quantity.hidden);
  }

  function askQuantity(form) {
    const { buy, quantity, input } = parts(form);

    if (!buy || !quantity || !input) {
      return;
    }

    buy.hidden = true;
    quantity.hidden = false;
    input.focus();
    input.select();
  }

  function foldBack(form) {
    const { buy, quantity, input, add } = parts(form);

    if (!buy || !quantity) {
      return;
    }

    if (input) {
      input.value = "1";
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
    }

    quantity.hidden = true;
    buy.hidden = false;

    if (add && quantity.contains(document.activeElement)) {
      add.focus();
    }
  }

  async function addToCart(form) {
    const { confirm } = parts(form);

    if (!confirm) {
      return;
    }

    const label = confirm.textContent.trim();
    confirm.disabled = true;

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });

      const payload = await response.json();

      if (!response.ok || !payload.ok) {
        throw new Error(payload.message || fallbackErrorMessage);
      }

      setFeedback(payload.message);
      confirm.textContent = addedLabel;

      document.dispatchEvent(
        new CustomEvent("cart-changed", { detail: { source: "catalog" } })
      );

      window.setTimeout(() => {
        confirm.textContent = label;
        confirm.disabled = false;
        foldBack(form);
      }, 700);
    } catch (error) {
      confirm.textContent = label;
      confirm.disabled = false;
      setFeedback(
        error instanceof Error ? error.message : fallbackErrorMessage
      );
    }
  }

  for (const form of catalog.querySelectorAll("[data-catalog-add-form]")) {
    const cancel = form.querySelector("[data-catalog-cancel-button]");

    if (cancel) {
      cancel.addEventListener("click", () => foldBack(form));
    }

    form.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && isAsking(form)) {
        foldBack(form);
      }
    });

    form.addEventListener("submit", (event) => {
      event.preventDefault();

      if (!isAsking(form)) {
        askQuantity(form);
        return;
      }

      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }

      void addToCart(form);
    });
  }
})();
