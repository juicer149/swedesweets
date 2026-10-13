/*
  The catalog (includes/catalog/grid.html), shop and business portal alike:

  - the category tabs and the search hide the tiles that do not match;
  - a tile's size dropdown shows the size big once picked; its quantity
    box lists 1-9 on the first tap and lets you type on the second;
  - the cart button posts the form as JSON while only the status burst
    shows in the row's middle (status_burst.js: the scoop, then our bag,
    the label green; or a cross, the label red), then the row comes back
    as it started and the navbar cart refreshes with a little jump
    (cart-changed with bump).

  Without JavaScript the dropdowns are plain and the cart button posts
  the form.
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


  /* Size, how many, then add ------------------------------------------ */

  /* The line under the tools: read out by screen readers every time, seen
     only when something went wrong (success has the bag). */
  function setFeedback(message, { quiet = false } = {}) {
    if (feedback) {
      feedback.textContent = message;
      feedback.classList.toggle("visually-hidden", quiet);
    }
  }

  /* The size dropdown is the native one (the phone's own picker), laid
     unseen over its face: "Choose size", then "Size" and the size, big. */
  function setUpSize(form) {
    const select = form.querySelector("[data-size-select]");

    if (!select) {
      return () => {};
    }

    const empty = form.querySelector("[data-size-empty]");
    const chosen = form.querySelector("[data-size-chosen]");
    const value = form.querySelector("[data-size-value]");

    const show = () => {
      const option = select.selectedOptions[0];
      const label = option && option.value ? option.dataset.sizeLabel : "";

      if (value) {
        value.textContent = label || "";
      }
      if (empty) {
        empty.hidden = Boolean(label);
      }
      if (chosen) {
        chosen.hidden = !label;
      }
    };

    select.addEventListener("change", show);
    show();

    return () => {
      select.value = "";
      show();
    };
  }

  /* How many: the first tap lists 1-9 (no keyboard: the box is read-only
     while the list is open), the second lets you type. From the keyboard
     it is a plain number box; ArrowDown opens the list. */
  function setUpQuantity(form) {
    const input = form.querySelector("[data-quantity-input]");
    const list = form.querySelector("[data-quantity-list]");

    if (!input || !list) {
      return () => {};
    }

    const options = Array.from(list.querySelectorAll("[data-quantity-option]"));

    const mark = () => {
      for (const option of options) {
        option.setAttribute(
          "aria-selected",
          String(option.dataset.quantityOption === input.value)
        );
      }
    };

    const open = () => {
      mark();
      list.hidden = false;
      input.setAttribute("aria-expanded", "true");
    };

    const close = () => {
      list.hidden = true;
      input.readOnly = false;
      input.setAttribute("aria-expanded", "false");
    };

    input.setAttribute("aria-haspopup", "listbox");
    input.setAttribute("aria-expanded", "false");

    input.addEventListener("pointerdown", () => {
      if (list.hidden) {
        // Read-only as it takes the focus, so no keyboard comes up.
        input.readOnly = true;
        open();
      } else {
        // The second tap: type.
        close();
        window.setTimeout(() => input.select(), 0);
      }
    });

    input.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown" && list.hidden) {
        event.preventDefault();
        open();
        (options.find((o) => o.getAttribute("aria-selected") === "true")
          || options[0])?.focus();
      } else if (event.key === "Escape" && !list.hidden) {
        event.preventDefault();
        close();
      }
    });

    for (const option of options) {
      // Keep the focus on the box while a number is picked.
      option.addEventListener("pointerdown", (event) => event.preventDefault());

      option.addEventListener("click", () => {
        input.value = option.dataset.quantityOption;
        close();
        input.focus();
      });

      option.addEventListener("keydown", (event) => {
        const index = options.indexOf(option);

        if (event.key === "ArrowDown" || event.key === "ArrowUp") {
          event.preventDefault();
          const next = index + (event.key === "ArrowDown" ? 1 : -1);
          options[Math.max(0, Math.min(options.length - 1, next))].focus();
        } else if (event.key === "Escape") {
          event.preventDefault();
          close();
          input.focus();
        }
      });
    }

    form.addEventListener("focusout", (event) => {
      if (!form.querySelector("[data-catalog-quantity]").contains(event.relatedTarget)) {
        close();
      }
    });

    document.addEventListener("pointerdown", (event) => {
      if (!list.hidden && !form.querySelector("[data-catalog-quantity]").contains(event.target)) {
        close();
      }
    });

    return () => {
      close();
      input.value = "1";
    };
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

  /* While the product is added the row gives way to the burst in its
     middle (the scoop); when the mark comes the label turns green and our
     bag pops up, or red with a cross; then the row comes back, as it
     started after an add, as it was after a failure (to try again). */
  async function addToCart(form, reset) {
    const status = form.querySelector("[data-catalog-status]");

    if (!status || form.dataset.state) {
      return;
    }

    form.dataset.state = "adding";
    status.hidden = false;

    const run = window.statusBurst
      ? window.statusBurst.run
      : async (_place, _name, request, options = {}) => {
          try {
            const value = await request();
            options.onMark?.(true);
            return { ok: true, value };
          } catch (error) {
            options.onMark?.(false);
            return { ok: false, error };
          }
        };

    // The navbar's cart catches the product while the bag still shows on
    // the tile (almost half a second after it appears), so the two overlap
    // a little.
    const onMark = (added) => {
      form.dataset.state = added ? "done" : "failed";

      if (added) {
        window.setTimeout(() => {
          document.dispatchEvent(
            new CustomEvent("cart-changed", {
              detail: { source: "catalog", bump: true },
            })
          );
        }, 450);
      }
    };

    const { ok, value, error } = await run(
      status,
      "default",
      () => postAdd(form),
      { onMark }
    );

    status.hidden = true;
    delete form.dataset.state;

    if (ok) {
      setFeedback(value.message || addedLabel, { quiet: true });
      reset();
      return;
    }

    setFeedback(error instanceof Error ? error.message : fallbackErrorMessage);
    form.querySelector("[data-catalog-add-button]")?.focus();
  }

  for (const form of catalog.querySelectorAll("[data-catalog-add-form]")) {
    form.dataset.enhanced = "";

    const resetSize = setUpSize(form);
    const resetQuantity = setUpQuantity(form);
    const reset = () => {
      resetSize();
      resetQuantity();
    };

    form.addEventListener("submit", (event) => {
      event.preventDefault();

      if (form.dataset.state) {
        return;
      }

      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }

      void addToCart(form, reset);
    });
  }
})();
