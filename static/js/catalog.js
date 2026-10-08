/*
  The catalog (includes/catalog/grid.html), shop and business portal alike:

  - the category tabs and the search hide the tiles that do not match;
  - a tile's "+ Add" first asks for a quantity (the stepper, the green
    tick and ×); the tick posts the form as JSON while only the status
    burst shows (status_burst.js: dots, then the crown or a red cross),
    then folds back to "+ Add" and tells the navbar cart, which refreshes
    and gives a little jump (cart-changed with bump).

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

  /* The line under the tools: read out by screen readers every time, seen
     only when something went wrong (success has the crown). */
  function setFeedback(message, { quiet = false } = {}) {
    if (feedback) {
      feedback.textContent = message;
      feedback.classList.toggle("visually-hidden", quiet);
    }
  }

  function parts(form) {
    return {
      buy: form.querySelector("[data-catalog-purchase-default]"),
      quantity: form.querySelector("[data-catalog-purchase-quantity]"),
      input: form.querySelector("[data-quantity-input]"),
      confirm: form.querySelector("[data-catalog-confirm-button]"),
      add: form.querySelector("[data-catalog-add-button]"),
      status: form.querySelector("[data-catalog-status]"),
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

    // On the stepper's +, the likeliest next press; the number can still
    // be typed (Tab back, or tap it).
    const increase = quantity.querySelector("[data-quantity-increase]");
    (increase || input).focus();
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

  async function postAdd(form) {
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

    return payload;
  }

  /* While the product is added only the status burst shows, centred where
     the quantity row was: the dots, then the crown (or a red cross).
     Without the burst script it simply posts and folds back. */
  async function addToCart(form) {
    const { quantity, status, confirm } = parts(form);

    if (!quantity || !status || form.dataset.adding === "true") {
      return;
    }

    form.dataset.adding = "true";
    quantity.hidden = true;
    status.hidden = false;

    const run = window.statusBurst
      ? window.statusBurst.run
      : async (_place, _name, request, options = {}) => {
          try {
            const value = await request();
            options.onMark?.(true);
            return { ok: true, value };
          } catch (error) {
            return { ok: false, error };
          }
        };

    // The navbar's cart catches the product while the green cart still
    // shows on the tile (a moment after it appears), so the two overlap.
    const catchIt = (added) => {
      if (added) {
        window.setTimeout(() => {
          document.dispatchEvent(
            new CustomEvent("cart-changed", {
              detail: { source: "catalog", bump: true },
            })
          );
        }, 250);
      }
    };

    const { ok, value, error } = await run(
      status,
      "default",
      () => postAdd(form),
      { onMark: catchIt }
    );

    status.hidden = true;
    delete form.dataset.adding;

    if (ok) {
      setFeedback(value.message || addedLabel, { quiet: true });
      foldBack(form);
      return;
    }

    // Back to the quantity, as it was, to try again.
    quantity.hidden = false;
    setFeedback(error instanceof Error ? error.message : fallbackErrorMessage);
    if (confirm) {
      confirm.focus();
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

      if (form.dataset.adding === "true") {
        return;
      }

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
