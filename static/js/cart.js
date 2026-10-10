(() => {
  const root = document.querySelector(
    "[data-current-order]"
  );

  if (!root) {
    return;
  }

  const fallbackErrorMessage = (
    root.dataset.currentOrderErrorMessage
    || "Could not update quantity."
  );

  function notifyCartChanged(
    {
      lineId,
      quantity,
      payload = null,
    }
  ) {
    document.dispatchEvent(
      new CustomEvent(
        "cart-changed",
        {
          detail: {
            source: "current-order",
            lineId,
            quantity,
            payload,
          },
        }
      )
    );
  }

  async function updateQuantity(form) {
    const input = form.querySelector(
      "[data-quantity-input]"
    );

    const status = form.querySelector(
      "[data-current-order-quantity-status]"
    );

    if (!input) {
      return;
    }

    const requestedQuantity = Number(
      input.value
    );

    const confirmedQuantity = Number(
      form.dataset.confirmedQuantity
    );

    if (
      !Number.isInteger(
        requestedQuantity
      )
      || requestedQuantity < 1
    ) {
      input.value = String(
        confirmedQuantity || 1
      );

      return;
    }

    if (
      requestedQuantity
      === confirmedQuantity
    ) {
      return;
    }

    if (
      form.dataset.updateInProgress
      === "true"
    ) {
      form.dataset.pendingQuantity = String(
        requestedQuantity
      );

      return;
    }

    form.dataset.updateInProgress = "true";
    form.dataset.pendingQuantity = "";

    try {
      const formData = new FormData(
        form
      );

      formData.set(
        "quantity",
        String(requestedQuantity)
      );

      const response = await fetch(
        form.action,
        {
          method: "POST",
          body: formData,
          headers: {
            Accept: "application/json",
          },
          credentials: "same-origin",
        }
      );

      const payload = await response.json();

      // The cart is locked by an open payment, usually because this page
      // was restored from history. Reload so the buyer sees the locked
      // cart and the way back to the payment.
      if (response.status === 409) {
        form.dataset.pendingQuantity = "";
        window.location.reload();
        return;
      }

      if (
        !response.ok
        || !payload.ok
      ) {
        throw new Error(
          payload.message
          || fallbackErrorMessage
        );
      }

      const savedQuantity = Number(
        payload.quantity
      );

      form.dataset.confirmedQuantity = String(
        savedQuantity
      );

      input.value = String(
        savedQuantity
      );

      if (status) {
        status.textContent = (
          payload.message || ""
        );
      }

      const lineId = (
        extractLineId(
          form.action
        )
      );

      notifyCartChanged({
        lineId,
        quantity: savedQuantity,
        payload,
      });
    } catch (error) {
      input.value = (
        form.dataset.confirmedQuantity
        || "1"
      );

      if (status) {
        status.textContent = (
          error instanceof Error
            ? error.message
            : fallbackErrorMessage
        );
      }
    } finally {
      form.dataset.updateInProgress = "false";

      const pendingQuantity = Number(
        form.dataset.pendingQuantity
      );

      form.dataset.pendingQuantity = "";

      if (
        Number.isInteger(
          pendingQuantity
        )
        && pendingQuantity >= 1
        && pendingQuantity !== Number(
          form.dataset.confirmedQuantity
        )
      ) {
        input.value = String(
          pendingQuantity
        );

        void updateQuantity(
          form
        );
      }
    }
  }

  function extractLineId(url) {
    const match = url.match(
      /\/lines\/(\d+)\/quantity\/?$/
    );

    if (!match) {
      return null;
    }

    return Number(
      match[1]
    );
  }

  root.addEventListener(
    "change",
    (event) => {
      const input = event.target.closest(
        "[data-current-order-quantity-form] [data-quantity-input]"
      );

      if (!input) {
        return;
      }

      const form = input.closest(
        "[data-current-order-quantity-form]"
      );

      if (!form) {
        return;
      }

      void updateQuantity(
        form
      );
    }
  );

  root.addEventListener(
    "submit",
    (event) => {
      const form = event.target.closest(
        "[data-current-order-quantity-form]"
      );

      if (!form) {
        return;
      }

      event.preventDefault();

      void updateQuantity(
        form
      );
    }
  );

  document.addEventListener(
    "cart-changed",
    (event) => {
      if (
        event.detail?.source
        !== "navbar-cart"
      ) {
        return;
      }

      const lineId = Number(
        event.detail.lineId
      );

      const quantity = Number(
        event.detail.quantity
      );

      if (
        !Number.isInteger(
          lineId
        )
        || !Number.isInteger(
          quantity
        )
      ) {
        return;
      }

      const forms = (
        root.querySelectorAll(
          "[data-current-order-quantity-form]"
        )
      );

      const form = Array.from(
        forms
      ).find(
        (candidate) => (
          extractLineId(
            candidate.action
          ) === lineId
        )
      );

      if (!form) {
        return;
      }

      const input = form.querySelector(
        "[data-quantity-input]"
      );

      if (!input) {
        return;
      }

      form.dataset.confirmedQuantity = String(
        quantity
      );

      input.value = String(
        quantity
      );
    }
  );

  /* The trash (a shop's cart and the retail cart): after its question
     (confirm_action.js) the line goes red and its trash spins while the
     removal is under way, then it fades and folds away (line_flash.js);
     the subtotal and the navbar cart catch up. When the last line has
     gone, a page that has its empty order on it shows it (cart-line-
     removed, business_cart.js); one that has not comes back as the empty
     cart. If it does not go through, the form posts the plain way and the
     page comes back with the reason. */

  root.addEventListener(
    "submit",
    async (event) => {
      const form = event.target.closest(
        "[data-current-order-remove]"
      );

      if (!form) {
        return;
      }

      event.preventDefault();

      const line = form.closest("[data-cart-line-id]");

      if (!line || line.dataset.removing) {
        return;
      }

      line.dataset.removing = "true";

      const request = async () => {
        const response = await fetch(
          form.action,
          {
            method: "POST",
            body: new FormData(form),
            headers: {
              Accept: "application/json",
            },
            credentials: "same-origin",
          }
        );

        // The cart is locked (an open payment): show it as it is.
        if (response.status === 409) {
          window.location.reload();
          throw new Error("locked");
        }

        const payload = await response.json();

        if (!response.ok || !payload.ok) {
          throw new Error(payload.message || "");
        }

        return payload;
      };

      let payload;

      try {
        payload = window.lineFlash
          ? await window.lineFlash.remove(line, request)
          : await request();
      } catch (error) {
        if (error instanceof Error && error.message === "locked") {
          return;
        }

        HTMLFormElement.prototype.submit.call(form);
        return;
      }

      const lineId = Number(line.dataset.cartLineId);
      line.remove();

      document.dispatchEvent(
        new CustomEvent(
          "cart-changed",
          {
            detail: {
              source: "current-order",
              lineId,
              quantity: 0,
              payload,
            },
          }
        )
      );

      const linesLeft = root.querySelector("[data-cart-line-id]");

      if (root.querySelector("[data-cart-empty]")) {
        root.dispatchEvent(new CustomEvent("cart-line-removed"));
      } else if (!linesLeft) {
        window.location.reload();
      }
    }
  );
})();
