document.addEventListener("DOMContentLoaded", () => {
  const orderLinesList = document.querySelector("[data-order-lines-list]");
  const orderLinesWrapper = document.querySelector(
    "[data-order-lines-wrapper]"
  );
  const emptyState = document.querySelector("[data-order-lines-empty]");
  const emptyFormTemplate = document.getElementById(
    "order-line-empty-form-template"
  );
  const addOfferSelect = document.querySelector(
    "[data-add-order-line-select]"
  );
  const totalFormsInput = document.querySelector(
    'input[name="lines-TOTAL_FORMS"]'
  );

  if (
    !orderLinesList ||
    !emptyFormTemplate ||
    !addOfferSelect ||
    !totalFormsInput
  ) {
    return;
  }

  function getOrderLines() {
    return Array.from(
      orderLinesList.querySelectorAll("[data-order-line]")
    );
  }

  function findOrderLineByOfferId(offerId) {
    return orderLinesList.querySelector(
      `[data-order-line][data-commercial-offer-id="${offerId}"]`
    );
  }

  function replaceFormIndex(value, index) {
    return value
      .replace(/lines-(\d+|__prefix__)-/g, `lines-${index}-`)
      .replace(/id_lines-(\d+|__prefix__)-/g, `id_lines-${index}-`);
  }

  function reindexOrderLine(orderLine, index) {
    orderLine.querySelectorAll("[name]").forEach((element) => {
      element.name = replaceFormIndex(element.name, index);
    });

    orderLine.querySelectorAll("[id]").forEach((element) => {
      element.id = replaceFormIndex(element.id, index);
    });

    orderLine.querySelectorAll("label[for]").forEach((label) => {
      label.htmlFor = replaceFormIndex(label.htmlFor, index);
    });

    const number = orderLine.querySelector("[data-order-line-number]");

    if (number) {
      number.textContent = String(index + 1);
    }
  }

  function syncFormsetIndexes() {
    const orderLines = getOrderLines();

    orderLines.forEach((orderLine, index) => {
      reindexOrderLine(orderLine, index);
    });

    totalFormsInput.value = String(orderLines.length);
  }

  function updateEmptyState() {
    const hasLines = getOrderLines().length > 0;

    if (orderLinesWrapper) {
      orderLinesWrapper.hidden = !hasLines;
    }

    if (emptyState) {
      emptyState.hidden = hasLines;
    }
  }

  function buildOrderLine(index) {
    const html = emptyFormTemplate.innerHTML
      .replaceAll("__prefix__", String(index))
      .replaceAll("__line_number__", String(index + 1));

    const wrapper = document.createElement("div");
    wrapper.innerHTML = html.trim();

    return wrapper.firstElementChild;
  }

  // A short green flash on the line just added, or the one that got
  // more (line_flash.js).
  function glowOrderLine(orderLine) {
    window.lineFlash?.added(orderLine);
  }

  function scrollOrderLineIntoView(orderLine) {
    orderLine.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }

  function incrementQuantity(orderLine, by = 1) {
    const input = orderLine.querySelector("[data-quantity-input]");

    if (!input) {
      return;
    }

    const current = Number(input.value);
    const next = Number.isFinite(current) ? current + by : by;

    input.value = String(next);

    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function clearAddOfferSelect() {
    const tomSelect = addOfferSelect.tomselect;

    if (tomSelect) {
      tomSelect.clear(true);
      return;
    }

    addOfferSelect.value = "";
  }

  // What a new line shows, drawn like the lines of a cart or an order:
  // the name, then the code and weight, then the offer when it is not
  // the standard one (order_line_form.html).
  function buildOfferView(data) {
    return {
      name: data.name || data.text || "",
      meta: [data.code, data.weight].filter(Boolean).join(" · "),
      offerDetail: data.offerDetail || "",
      image: data.image || "",
    };
  }

  // The line's empty picture circle becomes the product's picture.
  function setLineImage(orderLine, url) {
    const circle = orderLine.querySelector(".line__image");

    if (!circle || !url) {
      return;
    }

    const image = document.createElement("img");
    image.className = "line__image";
    image.src = url;
    image.alt = "";
    image.width = 48;
    image.height = 48;
    image.decoding = "async";

    circle.replaceWith(image);
  }

  function readSelectedOffer(value) {
    const tomSelect = addOfferSelect.tomselect;

    if (tomSelect) {
      const data = tomSelect.options[value];

      if (!data) {
        return null;
      }

      return {
        value,
        ...buildOfferView(data),
      };
    }

    const option = addOfferSelect.selectedOptions[0];

    if (!option || !option.value) {
      return null;
    }

    return {
      value: option.value,
      ...buildOfferView({
        code: option.dataset.code || "",
        name: option.dataset.name || "",
        weight: option.dataset.weight || "",
        offerDetail: option.dataset.offerDetail || "",
        image: option.dataset.image || "",
        text: option.textContent.trim(),
      }),
    };
  }

  // A new line for the offer, or more on its line. quantity: how many
  // (a previous order's own amount with "Order again"); scroll: whether
  // to bring it into view (only the first of several).
  function addOrIncrementLine(offer, { quantity = 1, scroll = true } = {}) {
    if (!offer || !offer.value) {
      return null;
    }

    const existingLine = findOrderLineByOfferId(offer.value);

    if (existingLine) {
      incrementQuantity(existingLine, quantity);
      clearAddOfferSelect();
      if (scroll) {
        scrollOrderLineIntoView(existingLine);
      }
      glowOrderLine(existingLine);
      return existingLine;
    }

    const index = getOrderLines().length;
    const orderLine = buildOrderLine(index);

    orderLine.dataset.commercialOfferId = offer.value;

    const offerInput = orderLine.querySelector(
      "[data-order-line-offer-input]"
    );
    const nameElement = orderLine.querySelector(
      "[data-order-line-name]"
    );
    const metaElement = orderLine.querySelector(
      "[data-order-line-meta]"
    );
    const offerElement = orderLine.querySelector(
      "[data-order-line-offer]"
    );
    const quantityInput = orderLine.querySelector(
      "[data-quantity-input]"
    );

    if (offerInput) {
      offerInput.value = offer.value;
    }

    if (nameElement) {
      nameElement.textContent = offer.name;
    }

    if (metaElement) {
      metaElement.textContent = offer.meta;
    }

    if (offerElement) {
      offerElement.textContent = offer.offerDetail;
      offerElement.hidden = !offer.offerDetail;
    }

    setLineImage(orderLine, offer.image);

    if (quantityInput) {
      quantityInput.value = String(quantity);
      quantityInput.dispatchEvent(new Event("input", { bubbles: true }));
    }

    orderLinesList.appendChild(orderLine);
    totalFormsInput.value = String(index + 1);

    clearAddOfferSelect();
    updateEmptyState();
    if (scroll) {
      scrollOrderLineIntoView(orderLine);
    }
    glowOrderLine(orderLine);
    return orderLine;
  }

  function handleOfferSelected(value) {
    if (!value) {
      return;
    }

    addOrIncrementLine(
      readSelectedOffer(value)
    );
  }

  if (addOfferSelect.tomselect) {
    addOfferSelect.tomselect.on(
      "change",
      handleOfferSelected
    );
  } else {
    addOfferSelect.addEventListener(
      "change",
      () => {
        handleOfferSelected(
          addOfferSelect.value
        );
      }
    );
  }

  /* The customer's previous orders (includes/orders/recent_orders.html,
     mode "form"): drawn on an edit; on a new order fetched when a
     customer is chosen. A product's "+" adds one; "Order again" adds each
     product it can, as many as that order had. */

  const recentOrdersSlot = document.querySelector(
    "[data-recent-orders-slot]"
  );

  function offerFromButton(button) {
    return {
      value: button.dataset.offerId,
      name: button.dataset.name || "",
      meta: button.dataset.meta || "",
      offerDetail: button.dataset.offerDetail || "",
      image: button.dataset.image || "",
    };
  }

  if (recentOrdersSlot) {
    recentOrdersSlot.addEventListener("click", (event) => {
      const add = event.target.closest("[data-recent-order-add]");

      if (add) {
        addOrIncrementLine(offerFromButton(add));
        return;
      }

      const repeat = event.target.closest("[data-recent-order-repeat]");
      const order = repeat && repeat.closest("[data-recent-order]");

      if (!order) {
        return;
      }

      order
        .querySelectorAll("[data-recent-order-add]")
        .forEach((button, index) => {
          addOrIncrementLine(offerFromButton(button), {
            quantity: Math.max(1, Number(button.dataset.quantity) || 1),
            scroll: index === 0,
          });
        });
    });

    const url = recentOrdersSlot.dataset.recentOrdersUrl;
    const customerSelect = document.querySelector('select[name="customer"]');
    let requested = 0;

    async function showCustomerOrders() {
      const customerId = customerSelect.value;
      const request = ++requested;

      if (!customerId) {
        recentOrdersSlot.replaceChildren();
        return;
      }

      try {
        const response = await fetch(
          `${url}?customer=${encodeURIComponent(customerId)}`,
          { credentials: "same-origin" }
        );

        if (!response.ok || request !== requested) {
          return;
        }

        recentOrdersSlot.innerHTML = await response.text();
        window.enhanceSmoothDetails?.(recentOrdersSlot);
      } catch {
        // Without them the form works as before.
      }
    }

    if (url && customerSelect) {
      customerSelect.addEventListener("change", showCustomerOrders);

      // Back with an error, the customer still chosen.
      if (customerSelect.value) {
        void showCustomerOrders();
      }
    }
  }

  orderLinesList.addEventListener("click", (event) => {
    const removeButton = event.target.closest(
      "[data-remove-order-line]"
    );

    if (!removeButton) {
      return;
    }

    const orderLine = removeButton.closest(
      "[data-order-line]"
    );

    if (!orderLine) {
      return;
    }

    orderLine.remove();

    syncFormsetIndexes();
    updateEmptyState();
  });

  updateEmptyState();
});
