"use strict";


(() => {
  if (
    window.__swedeSweetsQuantityStepperInitialized
  ) {
    return;
  }

  window.__swedeSweetsQuantityStepperInitialized = true;


  function parseOptionalNumber(
    value,
    fallback
  ) {
    if (
      value === null
      || value === undefined
      || String(value).trim() === ""
    ) {
      return fallback;
    }

    const parsed = Number(
      value
    );

    return Number.isFinite(parsed)
      ? parsed
      : fallback;
  }


  function getStepper(element) {
    return element.closest(
      "[data-quantity-stepper]"
    );
  }


  function getInput(stepper) {
    return stepper.querySelector(
      "[data-quantity-input]"
    );
  }


  function getMinimum(input) {
    return parseOptionalNumber(
      input.min,
      1
    );
  }


  function getMaximum(input) {
    return parseOptionalNumber(
      input.max,
      Number.POSITIVE_INFINITY
    );
  }


  function getStep(input) {
    const step = parseOptionalNumber(
      input.step,
      1
    );

    return step > 0
      ? step
      : 1;
  }


  function readQuantity(input) {
    const rawValue = input.value.trim();

    if (!rawValue) {
      return null;
    }

    const quantity = Number(
      rawValue
    );

    if (
      !Number.isFinite(quantity)
      || !Number.isInteger(quantity)
    ) {
      return null;
    }

    return quantity;
  }


  function renderState(stepper) {
    const input = getInput(
      stepper
    );

    if (!input) {
      return;
    }

    const quantity = readQuantity(
      input
    );

    const minimum = getMinimum(
      input
    );

    const maximum = getMaximum(
      input
    );

    const decreaseButton = (
      stepper.querySelector(
        "[data-quantity-decrease]"
      )
    );

    const increaseButton = (
      stepper.querySelector(
        "[data-quantity-increase]"
      )
    );

    if (decreaseButton) {
      decreaseButton.disabled = (
        quantity === null
        || (quantity <= minimum && !stepper.hasAttribute("data-remove-at-min"))
      );
      const removing = quantity !== null && quantity <= minimum && stepper.hasAttribute("data-remove-at-min");
      stepper.classList.toggle("is-minimum", removing);
      if (decreaseButton.dataset.removeLabel) decreaseButton.setAttribute("aria-label", removing ? decreaseButton.dataset.removeLabel : decreaseButton.dataset.decreaseLabel);
    }

    if (increaseButton) {
      increaseButton.disabled = (
        quantity !== null
        && quantity >= maximum
      );
    }
  }


  function setQuantity(
    stepper,
    quantity
  ) {
    const input = getInput(
      stepper
    );

    if (!input) {
      return;
    }

    input.value = String(
      quantity
    );

    /*
     * Keep the same browser contract as the original
     * quantity stepper.
     *
     * "input" lets presentation code react immediately.
     * "change" lets mutation code persist the new value.
     */
    input.dispatchEvent(
      new Event(
        "input",
        {
          bubbles: true,
        }
      )
    );

    input.dispatchEvent(
      new Event(
        "change",
        {
          bubbles: true,
        }
      )
    );
  }


  /*
   * A small hop of the number when − or + changed it (not when a script
   * resets it), up for +, down for −, so the change is seen.
   */
  function bumpNumber(
    stepper,
    direction
  ) {
    const input = getInput(
      stepper
    );

    if (!input) {
      return;
    }

    const className = `quantity-stepper__input--bump-${direction}`;

    input.classList.remove(
      "quantity-stepper__input--bump-up",
      "quantity-stepper__input--bump-down"
    );
    void input.offsetWidth; // restart the animation
    input.classList.add(
      className
    );
    input.addEventListener(
      "animationend",
      () => input.classList.remove(className),
      { once: true }
    );
  }


  function decreaseQuantity(button) {
    const stepper = getStepper(
      button
    );

    if (!stepper) {
      return;
    }

    const input = getInput(
      stepper
    );

    if (!input) {
      return;
    }

    const quantity = readQuantity(
      input
    );

    const minimum = getMinimum(
      input
    );

    const step = getStep(
      input
    );

    if (quantity !== null && quantity <= minimum && stepper.hasAttribute("data-remove-at-min")) {
      stepper.closest(".cart-line")?.querySelector(".line__remove-button, .site-nav-cart-line__remove-button")?.click();
      return;
    }

    if (
      quantity === null
      || quantity <= minimum
    ) {
      return;
    }

    setQuantity(
      stepper,
      Math.max(
        minimum,
        quantity - step
      )
    );

    bumpNumber(
      stepper,
      "down"
    );
  }


  function increaseQuantity(button) {
    const stepper = getStepper(
      button
    );

    if (!stepper) {
      return;
    }

    const input = getInput(
      stepper
    );

    if (!input) {
      return;
    }

    const quantity = readQuantity(
      input
    );

    const minimum = getMinimum(
      input
    );

    const maximum = getMaximum(
      input
    );

    const step = getStep(
      input
    );

    const nextQuantity = (
      quantity === null
        ? minimum
        : quantity + step
    );

    setQuantity(
      stepper,
      Math.min(
        maximum,
        nextQuantity
      )
    );

    bumpNumber(
      stepper,
      "up"
    );
  }


  document.addEventListener(
    "click",
    (event) => {
      const decreaseButton = (
        event.target.closest(
          "[data-quantity-decrease]"
        )
      );

      if (decreaseButton) {
        decreaseQuantity(
          decreaseButton
        );

        return;
      }

      const increaseButton = (
        event.target.closest(
          "[data-quantity-increase]"
        )
      );

      if (increaseButton) {
        increaseQuantity(
          increaseButton
        );
      }
    }
  );


  document.addEventListener(
    "input",
    (event) => {
      if (
        !event.target.matches(
          "[data-quantity-input]"
        )
      ) {
        return;
      }

      const stepper = getStepper(
        event.target
      );

      if (stepper) {
        renderState(
          stepper
        );
      }
    }
  );


  document.addEventListener(
    "change",
    (event) => {
      if (
        !event.target.matches(
          "[data-quantity-input]"
        )
      ) {
        return;
      }

      const stepper = getStepper(
        event.target
      );

      if (stepper) {
        renderState(
          stepper
        );
      }
    }
  );


  document.addEventListener("navbar-cart-refreshed", () => {
    document.querySelectorAll("[data-quantity-stepper]").forEach(renderState);
  });
  // Every cart uses the server-confirmed amount, including unpriced B2B lines.
  document.addEventListener("cart-changed", event => {
    const { lineId, payload } = event.detail || {};
    if (!Number.isInteger(Number(lineId)) || !payload || payload.line_total_label == null) return;
    for (const total of document.querySelectorAll(`[data-cart-line-total="${Number(lineId)}"]`)) {
      total.textContent = payload.line_total_label;
    }
  });

  document
    .querySelectorAll(
      "[data-quantity-stepper]"
    )
    .forEach(
      renderState
    );
})();
