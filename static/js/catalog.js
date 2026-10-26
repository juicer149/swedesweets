/*
  The catalog (includes/catalog/grid.html), shop and business portal alike:

  - the category tabs and the search hide the tiles that do not match;
  - a tile's size dropdown shows "Choose size", then the size; how many
    is typed;
  - the cart button posts the form as JSON while only the status burst
    shows in the row's middle (status_burst.js: the spinning cart button, then the cart mark,
    the label green; or a cross, the label red, then why); then the row
    comes back as it started, the picture's in-cart badge counts them,
    and the navbar cart refreshes with a little jump (cart-changed with
    bump).

  Without JavaScript the size dropdown is plain and the cart button
  posts the form.
*/
(() => {
  "use strict";

  if (window.SwedeSweetsCatalog) return;
  let dispose = () => {};
function initCatalog() {
  const catalog = document.querySelector(".catalog");

  if (!catalog || catalog.dataset.navigationReady) {
    return;
  }

  dispose();
  catalog.dataset.navigationReady = "true";
  const controller = new AbortController();
  const cleanups = [];
  const listen = (target, name, handler) => target.addEventListener(name, handler, { signal: controller.signal });
  dispose = () => {
    controller.abort();
    cleanups.forEach(cleanup => cleanup());
    window.SwedeSweetsProduct?.destroy(catalog);
    catalog.querySelectorAll("select").forEach(select => select.tomselect?.destroy());
    document.documentElement.classList.remove("catalog--detail-open");
    delete catalog.dataset.navigationReady;
    dispose = () => {};
  };

  const tiles = Array.from(
    catalog.querySelectorAll("[data-catalog-product]")
  );
  const categoryButtons = Array.from(
    catalog.querySelectorAll("[data-catalog-category]")
  );
  const searchInput = catalog.querySelector("[data-catalog-search]");
  const noResults = catalog.querySelector("[data-catalog-no-results]");
  const more = catalog.querySelector("[data-catalog-more]");
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

  const PAGE_SIZE = Number(catalog.dataset.catalogPageSize) || 12;
  const batchURL = new URL(location.href);
  const grid = catalog.querySelector(".tiles");
  const indexNode = catalog.querySelector("#catalog-search-index");
  const index = indexNode ? JSON.parse(indexNode.textContent) : tiles.map(tile => ({
    id: Number(tile.dataset.productId), category: tile.dataset.productCategory, search: tile.dataset.productSearch,
  }));
  const loaded = new Map(tiles.map(tile => [Number(tile.dataset.productId), tile]));
  const unavailable = new Set();
  let limit = PAGE_SIZE;
  let generation = 0;
  let pending = null;
  let loadingMore = false;
  let loadFailed = false;
  const matches = () => index.filter(item => !unavailable.has(item.id)
    && (filter.category === "all" || item.category === filter.category)
    && (!filter.query || normalize(item.search).includes(filter.query)));
  catalog.querySelector("[data-catalog-pagination]")?.setAttribute("hidden", "");
  cleanups.push(() => pending?.abort());

  async function applyFilters({ keepPage = false } = {}) {
    const version = ++generation;
    loadFailed = false;
    pending?.abort();
    pending = new AbortController();
    if (!keepPage) limit = PAGE_SIZE;
    const selected = matches().slice(0, limit);
    const desired = new Set(selected.map(item => item.id));
    for (const tile of tiles) tile.hidden = !desired.has(Number(tile.dataset.productId));
    for (const button of categoryButtons) {
      const active = button.dataset.catalogCategory === filter.category;
      button.classList.toggle("section-nav__link--active", active);
      button.setAttribute("aria-pressed", String(active));
    }
    catalog.setAttribute("aria-busy", "true");
    try {
      const missing = selected.filter(item => !loaded.has(item.id));
      for (let offset = 0; offset < missing.length; offset += PAGE_SIZE) {
        const requested = missing.slice(offset, offset + PAGE_SIZE).map(item => item.id);
        const url = new URL(batchURL);
        url.search = ""; url.searchParams.set("catalog_cards", "1"); url.searchParams.set("ids", requested.join(","));
        const response = await fetch(url, { credentials: "same-origin", signal: pending.signal, headers: { Accept: "application/json" } });
        if (response.redirected) { location.assign(response.url); return; }
        if (!response.ok) throw new Error("Catalog unavailable");
        const payload = await response.json();
        if (version !== generation || !catalog.isConnected) return;
        const fragment = document.createElement("template"); fragment.innerHTML = payload.html;
        const added = [...fragment.content.querySelectorAll("[data-catalog-product]")];
        for (const tile of added) {
          const id = Number(tile.dataset.productId);
          if (!requested.includes(id) || loaded.has(id)) continue;
          loaded.set(id, tile); tiles.push(tile); grid.append(tile);
          initializeTile(tile); window.enhanceSelects?.(tile);
        }
        const returned = new Set(added.map(tile => Number(tile.dataset.productId)));
        requested.filter(id => !returned.has(id)).forEach(id => unavailable.add(id));
      }
      if (version !== generation) return;
      for (const item of selected) if (loaded.has(item.id)) grid.append(loaded.get(item.id));
      if (noResults) noResults.hidden = matches().length !== 0;
      if (more) more.hidden = matches().length <= limit;
      setFeedback("", { quiet: true });
    } catch (error) {
      if (error.name === "AbortError" || version !== generation) return;
      loadFailed = true;
      setFeedback(catalog.dataset.catalogLoadError || "Could not load products. Try again.");
      if (more) more.hidden = false;
    } finally {
      if (version === generation) catalog.removeAttribute("aria-busy");
    }
  }
  for (const button of categoryButtons) listen(button, "click", () => {
    filter.category = button.dataset.catalogCategory || "all"; void applyFilters();
  });
  if (searchInput) listen(searchInput, "input", () => { filter.query = normalize(searchInput.value); void applyFilters(); });
  const isAtFoot = () => more && !more.hidden && more.getBoundingClientRect().top < innerHeight + 120;
  async function showMore() {
    if (loadFailed) { await applyFilters({ keepPage: true }); return; }
    if (!catalog.isConnected || loadingMore || catalog.hasAttribute("aria-busy") || matches().length <= limit) return;
    loadingMore = true; limit += PAGE_SIZE;
    await applyFilters({ keepPage: true });
    loadingMore = false;
  }
  const moreButton = catalog.querySelector("[data-catalog-load-more]");
  if (moreButton) listen(moreButton, "click", () => void showMore());
  if (more && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting) && isAtFoot()) void showMore();
    }, { rootMargin: "0px 0px 120px 0px" });
    observer.observe(more); cleanups.push(() => observer.disconnect());
  }
  void applyFilters();

  /* Size, how many, then add ------------------------------------------ */

  /* The line under the tools: read out by screen readers every time, seen
     only when something went wrong (success has the cart mark). */
  function setFeedback(message, { quiet = false } = {}) {
    if (feedback) {
      feedback.textContent = message;
      feedback.classList.toggle("visually-hidden", quiet);
    }
  }

  /* The size dropdown is the site's own (enhanced_selects.js). */
  function setUpSize(form) {
    const select = form.querySelector("[data-size-select]");

    if (!select) {
      return () => {};
    }

    // Back to "Choose size" after an add.
    return () => {
      if (select.tomselect) {
        select.tomselect.setValue("", true);
      } else {
        select.value = "";
      }
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

    listen(error, "click", done);
    timer = window.setTimeout(done, 4000);
  }

  /* The button cart spins while adding, then gives way to a green cart
     burst (or an error cross) inside the label. The row returns after a
     success; on failure its reason is shown before trying again. */
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

    // The navbar's cart catches the product while the green cart still shows on
    // the tile (almost half a second after it appears), so the two overlap
    // a little.
    let confirmedPayload = null;
    const onMark = (added) => {
      form.dataset.state = added ? "done" : "failed";

      if (added) {
        // Counted at once; the navbar cart's refresh just after counts
        // every badge anew from the cart itself.
        countIn(form, quantity);

        window.setTimeout(() => {
          document.dispatchEvent(
            new CustomEvent("cart-changed", {
              detail: { source: "catalog", bump: true, payload: confirmedPayload },
            })
          );
        }, 450);
      }
    };

    const { ok, value, error } = await run(
      status,
      "default",
      async () => { confirmedPayload = await postAdd(form); return confirmedPayload; },
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
  listen(document, "navbar-cart-refreshed", (event) => {
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

  function initializeTile(tile) {
    /* A narrow card says "Size", not "Choose size" (before the site's
       dropdown takes the select over, on DOMContentLoaded). */
    for (const select of tile.querySelectorAll("[data-size-select]")) {
      const empty = select.querySelector('option[value=""][data-short]');
      const label = select.closest(".tile__label");

      if (empty && label && label.offsetWidth < 200) {
        empty.textContent = empty.dataset.short;
      }
    }

    for (const form of tile.querySelectorAll("[data-catalog-add-form]")) {
      form.dataset.enhanced = "";
      // The checks are ours (below): the size's select is hidden behind the
      // site's dropdown, which the browser could not point at.
      form.noValidate = true;

      const resetSize = setUpSize(form);
      const resetQuantity = setUpQuantity(form);
      const reset = () => {
        resetSize();
        resetQuantity();
      };

      listen(form, "submit", (event) => {
        event.preventDefault();

        if (form.dataset.state) {
          return;
        }

        // No size yet: its list opens.
        const size = form.querySelector("[data-size-select]");
        if (size && !size.value) {
          if (size.tomselect) {
            size.tomselect.focus();
            size.tomselect.open();
          } else {
            size.focus();
          }
          return;
        }

        if (!form.checkValidity()) {
          form.reportValidity();
          return;
        }

        void addToCart(form, reset);
      });
    }

  }
  tiles.forEach(initializeTile);

  /* A card's page, over the catalog ------------------------------------

     Opening a card (its picture or name) brings its page over the wall,
     its own address in the bar (so it can be linked, and the browser's
     back closes it), the wall where it was underneath. With motion, on a
     computer and a phone alike: the card's label folds to its yellow band
     (the cart button riding up to it), the picture, tag, badge, band and
     button float to their places on the page (a view transition, the same
     names on both), and there the label unfolds with what the page adds.
     Closing is the same backwards. Reduced motion or a browser without
     view transitions: the page just shows. The page is the product's own page,
     fetched; failing that, the browser goes there. */

  const detail = catalog.querySelector("[data-catalog-detail]");
  const mobileDetail = matchMedia("(max-width: 767px)");
  const catalogURL = new URL(location.href);
  const catalogWasInert = catalog.inert;

  // Out of the catalog's page (its own stacking context) and straight
  // under the body, so it lies over everything on the page, the footer
  // too, and under the site's header and phone bar only.
  if (detail) {
    document.body.append(detail);
    cleanups.push(() => {
      window.SwedeSweetsProduct?.destroy(detail);
      detail.remove();
      catalog.inert = catalogWasInert;
    });
  }
  const FOLD_MS = 220;
  const PARTS = {
    picture: ".tile__image",
    tag: ".tile__tag",
    "in-cart": ".tile__in-cart",
    label: ".tile__label",
    // Its own, so it grows from the card's size to the page's as it goes.
    button: ".tile__add",
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

  /* Unfold: clipped while it grows (data-unfolding), then open again so
     the size list can spill out of it. */
  function unfold(element, foldedClass) {
    element.dataset.unfolding = "";
    element.classList.remove(foldedClass);
    window.setTimeout(() => delete element.dataset.unfolding, 320);
  }

  function withMotion() {
    return Boolean(
      document.startViewTransition
      && !window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  // The mounted header is captured separately from the page crossfade.
  let productMotion = null;
  const transitionRoot = document.documentElement;
  cleanups.push(() => {
    productMotion?.skipTransition();
    transitionRoot.classList.remove("catalog-product-transition");
  });
  async function productTransition(update) {
    transitionRoot.classList.add("catalog-product-transition");
    try {
      const transition = document.startViewTransition(update);
      productMotion = transition;
      transition.ready.catch(() => {});
      await transition.finished.catch(() => {});
    } finally {
      productMotion = null;
      transitionRoot.classList.remove("catalog-product-transition");
    }
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
      signal: controller.signal,
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

  let labelResizeObserver = null;
  cleanups.push(() => labelResizeObserver?.disconnect());

  /* Scale the actual name area, not an estimate of the grid's spare room.
     Keep it in sync when the viewport, browser zoom or source card changes. */
  function scaleLabel(article, tile) {
    labelResizeObserver?.disconnect();
    labelResizeObserver = null;
    const tileName = tile?.querySelector(".tile__name");
    const band = article.querySelector(".product__band");
    const name = article.querySelector(".product__name");
    const side = article.querySelector(".product__side");

    if (!tileName || !band || !name || !side) {
      return;
    }

    const update = () => {
      if (!band.isConnected || !tileName.isConnected) {
        return;
      }
      const source = getComputedStyle(tileName);
      const sourceWidth = parseFloat(source.width);
      const textWidth = sourceWidth - parseFloat(source.paddingLeft)
        - parseFloat(source.paddingRight);
      const bandWidth = parseFloat(getComputedStyle(band).width);

      if (textWidth <= 0 || bandWidth <= 0) {
        return;
      }

      side.style.setProperty("--label-scale", String(bandWidth / sourceWidth));
      const available = parseFloat(getComputedStyle(name).width);
      const fontSize = parseFloat(source.fontSize) * available / textWidth;
      side.style.setProperty("--product-name-size", `${fontSize}px`);
    };

    update();
    if ("ResizeObserver" in window) {
      // Updating the font can change band height; do it outside observer
      // delivery so a resize never creates a ResizeObserver loop warning.
      labelResizeObserver = new ResizeObserver(() => requestAnimationFrame(update));
      labelResizeObserver.observe(tileName, { box: "border-box" });
      labelResizeObserver.observe(band, { box: "border-box" });
    }
  }

  function show(section, tile) {
    detail.replaceChildren(section);
    window.enhanceSelects?.(section);
    detail.style.setProperty(
      "--detail-top",
      `${document.querySelector(".site-header")?.getBoundingClientRect().bottom || 0}px`
    );
    detail.hidden = false;
    document.documentElement.classList.add("catalog--detail-open");
    catalog.inert = true;

    scaleLabel(section.querySelector("[data-product-page]") || section, tile);
  }

  function hide() {
    window.SwedeSweetsProduct?.destroy(detail);
    labelResizeObserver?.disconnect();
    labelResizeObserver = null;
    detail.hidden = true;
    detail.replaceChildren();
    document.documentElement.classList.remove("catalog--detail-open");
    catalog.inert = catalogWasInert;
  }

  let pendingHistory = false;
  function syncProductHistory(event) {
    if (opened.busy) { pendingHistory = true; return; }
    const url = event.state?.catalogProduct;
    if (opened.url && !url) void closeProduct();
    else if (url && !opened.url) void openProduct(tileFor(url), url, { push: false });
  }
  function historySettled() {
    if (pendingHistory && !controller.signal.aborted) {
      pendingHistory = false;
      syncProductHistory({ state: window.history.state });
    }
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
      if (controller.signal.aborted) return;
      window.location.assign(url);
      return;
    }

    if (controller.signal.aborted) return;
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

      await productTransition(() => {
        nameTile(tile, false);
        show(page.section, tile);
      });
      if (controller.signal.aborted) return;
      // Then the label unfolds with what the page adds (clipped while it
      // does).
      void article.offsetWidth;
      unfold(article, "product--folded");
    } else {
      show(page.section, tile);
    }

    window.SwedeSweetsTabs?.init(page.section);
    window.SwedeSweetsProduct?.init(article, {
      onClose: () => { if (!opened.busy) window.history.back(); },
      onAdded: () => window.history.back(),
    });
    // From the keyboard, on to the page's ×; a click leaves the focus be.
    if (keyboard) {
      article.querySelector("[data-product-close]")?.focus({ preventScroll: true });
    }

    opened.busy = false;
    historySettled();
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
      if (controller.signal.aborted) return;

      await productTransition(() => {
        hide();
        nameTile(tile, true);
      });
      if (controller.signal.aborted) return;
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
    historySettled();
  }

  if (detail) {
    // The mobile header cloud and bottom cross return through the same
    // history entry, preserving the catalog's filters, scroll and tile.
    listen(document, "click", event => {
      if (!mobileDetail.matches || !opened.url || event.defaultPrevented || event.button !== 0
        || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = event.target.closest(".site-header .site-nav__link[aria-current='page'][href], [data-product-close]");
      if (!link || (link.matches("[data-product-close]") && !detail.contains(link))
        || link.download || (link.target && link.target !== "_self")) return;
      const destination = new URL(link.href, location.href);
      if (destination.origin !== catalogURL.origin || destination.pathname !== catalogURL.pathname || destination.hash) return;
      event.preventDefault();
      if (!opened.busy) window.history.back();
    });
    listen(catalog, "click", (event) => {
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
    listen(window, "popstate", syncProductHistory);
  }
}
  window.SwedeSweetsCatalog = { init: initCatalog, destroy: () => dispose() };
  initCatalog();
})();
