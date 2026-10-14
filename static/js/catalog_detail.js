/*
  A catalog product's page (includes/catalog/product.html), in the catalog
  card's design:

  - the size dropdown is the native one, laid unseen over its face
    ("Choose size", then the size); choosing one sets the price tag and
    the stock to it, and shows its special offer when it has one;
  - ticking the offer sets them to the offer (its tick box posts it in the
    size's place);
  - the cart button sends the form in the background while only the
    status burst shows in the white (status_burst.js: the scoop, then our
    bag, the label green; or a cross, the label red, then why until
    tapped); once added the badge counts them, the navbar cart jumps and
    the catalog opens (data-done-url), as without JavaScript;
  - the badge follows the navbar cart whenever it refreshes.
*/
(() => {
  "use strict";

  const form = document.querySelector("[data-product-add-form]");

  if (!form) {
    return;
  }

  form.dataset.enhanced = "";

  /* Back to the catalog the way one came: the browser's own back, so the
     catalog is where it was left (its scroll) and its card is the one
     the page floats back to. Opened from elsewhere: the link as it is. */
  const cameFromCatalog = (() => {
    try {
      const from = new URL(document.referrer);
      const catalog = new URL(form.dataset.doneUrl || "", window.location.href);
      return from.origin === window.location.origin
        && from.pathname === catalog.pathname;
    } catch (error) {
      return false;
    }
  })();

  for (const link of document.querySelectorAll(".product__back-top, .product .page__back a")) {
    link.addEventListener("click", (event) => {
      if (cameFromCatalog && window.history.length > 1) {
        event.preventDefault();
        window.history.back();
      }
    });
  }

  const select = form.querySelector("[data-size-select]");
  const onlyOffer = form.querySelector("[data-only-offer]");
  const empty = form.querySelector("[data-size-empty]");
  const chosen = form.querySelector("[data-size-chosen]");
  const dealBox = form.querySelector("[data-product-deal]");
  const dealInput = form.querySelector("[data-deal-input]");
  const dealText = form.querySelector("[data-deal-text]");
  const stock = form.querySelector("[data-product-stock]");
  const stockText = form.querySelector("[data-product-stock-text]");
  const tag = document.querySelector("[data-product-tag]");
  const tagPrice = document.querySelector("[data-product-price]");
  const tagNote = document.querySelector("[data-product-tag-note]");
  const badge = document.querySelector("[data-in-cart]");
  const badgeCount = badge?.querySelector("[data-in-cart-count]");
  const feedback = form.querySelector("[data-product-feedback]");
  const status = form.querySelector("[data-product-status]");
  const errorBox = form.querySelector("[data-product-error]");
  const quantity = form.querySelector("[data-quantity-input]");


  /* What is shown: the tag, the stock and the offer follow the choice. */

  function setStock(source) {
    if (!stock || !stockText) {
      return;
    }

    const label = source?.dataset.stockLabel || "";
    const low = source?.dataset.stockLow === "true";

    stockText.textContent = label;
    stockText.classList.toggle("status-text--warning", low);
    stockText.classList.toggle("status-text--success", !low);
    stock.hidden = !label;
  }

  function setTag(priceLabel, note) {
    if (!tag || !tagPrice) {
      return;
    }

    tagPrice.textContent = priceLabel || "";
    tag.hidden = !priceLabel;

    if (tagNote) {
      tagNote.textContent = note || "";
      tagNote.hidden = !note;
    }
  }

  function chosenOption() {
    const option = select?.selectedOptions[0];
    return option && option.value ? option : null;
  }

  function render() {
    const option = select ? chosenOption() : onlyOffer;
    const dealOn = Boolean(dealInput && !dealInput.disabled && dealInput.checked);

    if (select) {
      const label = option?.dataset.sizeLabel || "";

      if (chosen) {
        chosen.textContent = label;
        chosen.hidden = !label;
      }
      if (empty) {
        empty.hidden = Boolean(label);
      }
    }

    if (!option) {
      // Nothing chosen yet: the cheapest price ("from"), no stock line.
      setTag(tagPrice?.dataset.initial || "", "");
      setStock(null);
      return;
    }

    if (dealOn) {
      setTag(dealInput.dataset.priceLabel, dealInput.dataset.dealLabel || "");
      setStock(dealInput);
    } else {
      setTag(option.dataset.priceLabel, "");
      setStock(option);
    }
  }

  /* A size's special offer, when it has one: shown unticked. */
  function showDealFor(option) {
    if (!select || !dealBox || !dealInput) {
      return;
    }

    const dealId = option?.dataset.dealId;

    dealInput.checked = false;
    dealInput.disabled = !dealId;
    dealBox.hidden = !dealId;

    if (!dealId) {
      return;
    }

    dealInput.value = dealId;
    dealInput.dataset.priceLabel = option.dataset.dealPriceLabel || "";
    dealInput.dataset.stockLabel = option.dataset.dealStockLabel || "";
    dealInput.dataset.stockLow = option.dataset.dealStockLow || "false";
    dealInput.dataset.dealLabel = option.dataset.dealLabel || "";

    if (dealText) {
      const price = option.dataset.dealPriceLabel;
      dealText.replaceChildren();
      const name = document.createElement("b");
      name.textContent = option.dataset.dealLabel || "";
      dealText.append(name);
      if (price) {
        dealText.append(` · ${price}`);
      }
    }
  }

  if (dealInput && !select) {
    // One size: its offer is in the page already.
    dealInput.dataset.dealLabel =
      dealText?.querySelector("b")?.textContent || "";
  }

  select?.addEventListener("change", () => {
    showDealFor(chosenOption());
    render();
  });
  dealInput?.addEventListener("change", render);
  render();


  /* The badge: how many the cart holds; anew whenever the navbar cart
     refreshes (the server's cart, not our sums). */

  function setBadge(units) {
    if (!badge || !badgeCount) {
      return;
    }

    badgeCount.textContent = String(units);
    badge.hidden = units <= 0;
  }

  document.addEventListener("navbar-cart-refreshed", (event) => {
    const productId = form.dataset.productId;
    const lines = (event.detail?.container || document).querySelectorAll(
      "[data-navbar-cart-line][data-product-id]"
    );
    let units = 0;

    for (const line of lines) {
      if (line.dataset.productId === productId) {
        units += Number(line.dataset.quantity) || 0;
      }
    }

    setBadge(units);
  });


  /* Adding. */

  if (!window.fetch || !status) {
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
      throw new Error(payload.message || form.dataset.errorMessage || "");
    }

    return payload;
  }

  function showError(message) {
    if (!errorBox) {
      delete form.dataset.state;
      return;
    }

    errorBox.textContent = message;
    errorBox.hidden = false;

    let timer = 0;
    const done = () => {
      window.clearTimeout(timer);
      errorBox.removeEventListener("click", done);
      errorBox.hidden = true;
      delete form.dataset.state;
      form.querySelector("[data-product-add-button]")?.focus();
    };

    errorBox.addEventListener("click", done);
    timer = window.setTimeout(done, 4000);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (form.dataset.state) {
      return;
    }

    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    const added = Number(quantity?.value) || 0;

    form.dataset.state = "adding";
    status.hidden = false;
    if (feedback) {
      feedback.textContent = "";
    }

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

    // The navbar's cart catches the product while the bag still shows,
    // so the two overlap a little.
    const onMark = (ok) => {
      form.dataset.state = ok ? "done" : "failed";

      if (ok) {
        setBadge((Number(badgeCount?.textContent) || 0) + added);
        window.setTimeout(() => {
          document.dispatchEvent(
            new CustomEvent("cart-changed", {
              detail: { source: "product", bump: true },
            })
          );
        }, 450);
      }
    };

    const { ok, value, error } = await run(status, "default", post, { onMark });

    status.hidden = true;

    if (ok) {
      if (feedback) {
        feedback.textContent = value.message || "";
      }

      // Added: on to the catalog, as without JavaScript.
      if (form.dataset.doneUrl) {
        window.location.assign(form.dataset.doneUrl);
        return;
      }

      delete form.dataset.state;
      return;
    }

    const message = error?.message || form.dataset.errorMessage || "";
    if (feedback) {
      feedback.textContent = message;
    }
    form.dataset.state = "failed";
    showError(message);
  });
})();
