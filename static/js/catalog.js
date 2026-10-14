/*
  The catalog (includes/catalog/grid.html), shop and business portal alike:

  - the category tabs and the search hide the tiles that do not match;
  - a tile's size dropdown shows "Choose size", then the size; how many
    is typed;
  - the cart button posts the form as JSON while only the status burst
    shows in the row's middle (status_burst.js: the scoop, then our bag,
    the label green; or a cross, the label red, then why); then the row
    comes back as it started, the picture's in-cart badge counts them,
    and the navbar cart refreshes with a little jump (cart-changed with
    bump).

  Without JavaScript the size dropdown is plain and the cart button
  posts the form.
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
     unseen over its face: "Choose size", then the size. */
  function setUpSize(form) {
    const select = form.querySelector("[data-size-select]");

    if (!select) {
      return () => {};
    }

    const empty = form.querySelector("[data-size-empty]");
    const chosen = form.querySelector("[data-size-chosen]");

    const show = () => {
      const option = select.selectedOptions[0];
      const label = option && option.value ? option.dataset.sizeLabel : "";

      if (chosen) {
        chosen.textContent = label || "";
        chosen.hidden = !label;
      }
      if (empty) {
        empty.hidden = Boolean(label);
      }
    };

    select.addEventListener("change", show);
    show();

    return () => {
      select.value = "";
      show();
    };
  }

  /* How many: typed; back to 1 after an add. */
  function setUpQuantity(form) {
    const input = form.querySelector("[data-quantity-input]");

    return () => {
      if (input) {
        input.value = "1";
      }
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

  /* The badge on the picture: how many the cart holds. */
  function countIn(form, added) {
    const tile = form.closest("[data-catalog-product]");
    const badge = tile?.querySelector("[data-in-cart]");
    const count = badge?.querySelector("[data-in-cart-count]");

    if (!badge || !count || !(added > 0)) {
      return;
    }

    count.textContent = String((Number(count.textContent) || 0) + added);
    badge.hidden = false;
  }

  /* Why it did not work, in the red where the row was, until tapped or a
     few seconds have passed; then the row, as it was, to try again. */
  function showError(form, message) {
    const error = form.querySelector("[data-catalog-error]");

    if (!error) {
      delete form.dataset.state;
      return;
    }

    error.textContent = message;
    error.hidden = false;

    let timer = 0;
    const done = () => {
      window.clearTimeout(timer);
      error.removeEventListener("click", done);
      error.hidden = true;
      delete form.dataset.state;
      form.querySelector("[data-catalog-add-button]")?.focus();
    };

    error.addEventListener("click", done);
    timer = window.setTimeout(done, 4000);
  }

  /* While the product is added the row gives way to the burst in its
     middle (the scoop); when the mark comes the label turns green and our
     bag pops up, or red with a cross; then the row comes back as it
     started after an add (the badge counting them), and after a failure
     the reason shows in the red first. */
  async function addToCart(form, reset) {
    const status = form.querySelector("[data-catalog-status]");

    if (!status || form.dataset.state) {
      return;
    }

    form.dataset.state = "adding";
    status.hidden = false;

    const quantity = Number(form.querySelector("[data-quantity-input]")?.value) || 0;

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
        // Counted at once; the navbar cart's refresh just after counts
        // every badge anew from the cart itself.
        countIn(form, quantity);

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

    if (ok) {
      delete form.dataset.state;
      setFeedback(value.message || addedLabel, { quiet: true });
      reset();
      return;
    }

    const message = error instanceof Error ? error.message : fallbackErrorMessage;
    setFeedback(message, { quiet: true });
    form.dataset.state = "failed";
    showError(form, message);
  }

  /* After any change to the cart (the navbar's refresh, here or after an
     add), every badge counts the navbar cart's lines anew: the server's
     cart, not our sums. */
  document.addEventListener("navbar-cart-refreshed", (event) => {
    const lines = (event.detail?.container || document).querySelectorAll(
      "[data-navbar-cart-line][data-product-id]"
    );
    const units = new Map();

    for (const line of lines) {
      const id = line.dataset.productId;
      units.set(id, (units.get(id) || 0) + (Number(line.dataset.quantity) || 0));
    }

    for (const tile of tiles) {
      const badge = tile.querySelector("[data-in-cart]");
      const count = badge?.querySelector("[data-in-cart-count]");
      const held = units.get(tile.dataset.productId) || 0;

      if (badge && count) {
        count.textContent = String(held);
        badge.hidden = held === 0;
      }
    }
  });

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


  /* A card's page, over the catalog ------------------------------------

     Opening a card (its picture or name) brings its page over the wall,
     its own address in the bar (so it can be linked, and the browser's
     back closes it), the wall where it was underneath. On a computer, with
     motion: the card's label folds to its yellow band (the cart button
     riding up to it), the picture, tag, badge and band float to their
     places on the page (a view transition, the same names on both), and
     there the label unfolds with what the page adds. Closing is the same
     backwards. A phone, reduced motion or a browser without view
     transitions: the page just shows. The page is the product's own page,
     fetched; failing that, the browser goes there. */

  const detail = catalog.querySelector("[data-catalog-detail]");
  const FOLD_MS = 220;
  const PARTS = {
    picture: ".tile__image",
    tag: ".tile__tag",
    "in-cart": ".tile__in-cart",
    label: ".tile__label",
  };

  const opened = {
    tile: null,
    url: "",
    title: "",
    busy: false,
  };

  function wait(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  function withMotion() {
    return Boolean(
      document.startViewTransition
      && !window.matchMedia("(max-width: 767px)").matches
      && !window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  function nameTile(tile, on) {
    const id = tile.dataset.productId;

    for (const [part, selector] of Object.entries(PARTS)) {
      const element = tile.querySelector(selector);

      if (element) {
        element.style.viewTransitionName = on ? `product-${id}-${part}` : "";
      }
    }
  }

  function tileFor(url) {
    const path = new URL(url, window.location.href).pathname;

    return tiles.find((tile) => {
      const link = tile.querySelector(".tile__media");
      return link && new URL(link.href).pathname === path;
    }) || null;
  }

  async function fetchPage(url) {
    const response = await fetch(url, {
      headers: { Accept: "text/html" },
      credentials: "same-origin",
    });

    if (!response.ok) {
      throw new Error("not found");
    }

    const page = new DOMParser().parseFromString(await response.text(), "text/html");
    const article = page.querySelector("[data-product-page]");

    if (!article) {
      throw new Error("not a product");
    }

    return {
      section: article.closest(".page-section") || article,
      title: page.title,
    };
  }

  /* The page's label is the card's, bigger: the same width-to-text ratio,
     so the name breaks the same way. */
  function scaleLabel(article, tile) {
    const tileLabel = tile?.querySelector(".tile__label");
    const main = article.querySelector(".product__main");
    const media = article.querySelector(".product__media");
    const side = article.querySelector(".product__side");

    if (!tileLabel || !main || !media || !side) {
      return;
    }

    const gap = parseFloat(getComputedStyle(main).columnGap) || 0;
    const tileWidth = tileLabel.offsetWidth;
    const room = Math.min(main.clientWidth - media.offsetWidth - gap, 24 * 16);

    if (tileWidth > 0 && room > 0) {
      side.style.setProperty("--tile-label-width", `${tileWidth}px`);
      side.style.setProperty("--label-scale", String(room / tileWidth));
    }
  }

  function show(section, tile) {
    detail.replaceChildren(section);
    detail.style.setProperty(
      "--detail-top",
      `${document.querySelector(".site-header")?.getBoundingClientRect().bottom || 0}px`
    );
    detail.hidden = false;
    document.documentElement.classList.add("catalog--detail-open");

    if (!window.matchMedia("(max-width: 767px)").matches) {
      scaleLabel(section.querySelector("[data-product-page]") || section, tile);
    }
  }

  function hide() {
    detail.hidden = true;
    detail.replaceChildren();
    document.documentElement.classList.remove("catalog--detail-open");
  }

  async function openProduct(tile, url, { push = true, keyboard = false } = {}) {
    if (!detail || opened.busy || opened.tile) {
      return;
    }

    opened.busy = true;
    const motion = withMotion();
    const loading = fetchPage(url);

    if (motion && tile) {
      tile.classList.add("tile--folded");
    }

    let page;
    try {
      [page] = await Promise.all([loading, motion ? wait(FOLD_MS) : null]);
    } catch (error) {
      window.location.assign(url);
      return;
    }

    const article = page.section.querySelector("[data-product-page]") || page.section;

    opened.tile = tile;
    opened.url = url;
    opened.title = document.title;

    if (push) {
      window.history.pushState({ catalogProduct: url }, "", url);
    }
    document.title = page.title || document.title;

    if (motion && tile) {
      article.classList.add("product--folded");
      nameTile(tile, true);

      const transition = document.startViewTransition(() => {
        nameTile(tile, false);
        show(page.section, tile);
      });

      await transition.finished.catch(() => {});
      // Then the label unfolds with what the page adds.
      void article.offsetWidth;
      article.classList.remove("product--folded");
    } else {
      show(page.section, tile);
    }

    window.SwedeSweetsTabs?.init(page.section);
    window.SwedeSweetsProduct?.init(article, {
      onClose: () => window.history.back(),
      onAdded: () => window.history.back(),
    });
    // From the keyboard, on to the page's ×; a click leaves the focus be.
    if (keyboard) {
      article.querySelector("[data-product-close]")?.focus({ preventScroll: true });
    }

    opened.busy = false;
  }

  async function closeProduct() {
    if (!detail || !opened.url || opened.busy) {
      return;
    }

    opened.busy = true;
    const tile = opened.tile;
    const article = detail.querySelector("[data-product-page]");
    const motion = withMotion() && tile && tile.classList.contains("tile--folded");

    if (motion && article) {
      article.classList.add("product--folded");
      await wait(FOLD_MS);

      const transition = document.startViewTransition(() => {
        hide();
        nameTile(tile, true);
      });

      await transition.finished.catch(() => {});
      nameTile(tile, false);
    } else {
      hide();
    }

    if (tile) {
      tile.classList.remove("tile--folded");
      tile.querySelector(".tile__name a")?.focus({ preventScroll: true, focusVisible: false });
    }

    document.title = opened.title || document.title;
    opened.tile = null;
    opened.url = "";
    opened.busy = false;
  }

  if (detail) {
    catalog.addEventListener("click", (event) => {
      const link = event.target.closest(".tile__media, .tile__name a");

      if (
        !link
        || event.defaultPrevented
        || event.button !== 0
        || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey
      ) {
        return;
      }

      event.preventDefault();
      void openProduct(link.closest("[data-catalog-product]"), link.href, {
        keyboard: event.detail === 0,
      });
    });

    // The browser's back closes it; forward opens it again.
    window.addEventListener("popstate", (event) => {
      const url = event.state?.catalogProduct;

      if (opened.url && !url) {
        void closeProduct();
      } else if (url && !opened.url) {
        void openProduct(tileFor(url), url, { push: false });
      }
    });
  }
})();
