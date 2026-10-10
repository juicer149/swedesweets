/**
 * A shop's cart (business_portal/orders/cart.html) without reloading:
 *
 *   - the quick add: choosing a product posts it (Accept: JSON); the
 *     answer carries the line drawn by the server, which goes in at the
 *     end of the lines (or replaces the line, one more, when the product
 *     is already there) with a short green glow;
 *   - a previous order's "+" on one of its products does the same, and
 *     its "Order again" puts all the lines it added in place (and says
 *     beside the order which products were left out, and why), both with
 *     the catalog's burst while they run (scoop, then bag);
 *   - the trash: after its question (confirm_action.js) the line is
 *     removed in place.
 *
 * The lines and the empty order are both on the page; whichever fits is
 * shown. The navbar cart refreshes on "cart-changed". Without this script
 * the forms post and the page reloads, as before.
 */
document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector("[data-current-order]");

  if (!root) {
    return;
  }

  const list = root.querySelector("ul[data-cart-lines]");

  function updateEmptyState() {
    const hasLines = Boolean(
      list && list.querySelector("[data-cart-line-id]")
    );

    root.querySelectorAll("[data-cart-lines]").forEach((element) => {
      element.hidden = !hasLines;
    });

    root.querySelectorAll("[data-cart-empty]").forEach((element) => {
      element.hidden = hasLines;
    });
  }

  function notifyCartChanged(detail) {
    document.dispatchEvent(
      new CustomEvent("cart-changed", {
        detail: {
          source: "current-order",
          ...detail,
        },
      })
    );
  }

  const glow = (line) => window.glowLine?.(line);

  function placeLine(html, cartLineId) {
    const template = document.createElement("template");
    template.innerHTML = html.trim();

    const line = template.content.firstElementChild;

    if (!line || !list) {
      return null;
    }

    const existing = list.querySelector(
      `[data-cart-line-id="${cartLineId}"]`
    );

    if (existing) {
      existing.replaceWith(line);
    } else {
      list.appendChild(line);
    }

    // The new stepper draws its state (its minus greyed out at 1).
    const input = line.querySelector("[data-quantity-input]");

    if (input) {
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }

    return line;
  }

  async function postForm(form) {
    const response = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { Accept: "application/json" },
      credentials: "same-origin",
    });

    let payload = {};

    try {
      payload = await response.json();
    } catch {
      payload = {};
    }

    return { response, payload };
  }

  // Post an add form; put its line in place. False when it did not work.
  async function addOffer(form) {
    try {
      const { response, payload } = await postForm(form);

      if (!response.ok || !payload.ok || !payload.line_html) {
        return false;
      }

      showAddedLines([payload]);
      return true;
    } catch {
      return false;
    }
  }

  // As in the catalog (catalog.js): the navbar's cart catches the product
  // a moment after the bag appears, so the two overlap a little.
  const CART_CATCH_DELAY = 450;

  // Lines the server drew ({cart_line_id, quantity, line_html}) go in
  // place; each glows, the first scrolled into view, and the navbar cart
  // catches them. With the burst all of it waits catchDelay ms
  // (CART_CATCH_DELAY) after the bag appears: spin, bag, then the page
  // moves, the line glows and the cart jumps together.
  function showAddedLines(lines, { catchDelay = 0 } = {}) {
    const show = () => {
      const placed = lines
        .map((item) => placeLine(item.line_html, item.cart_line_id))
        .filter(Boolean);

      updateEmptyState();

      if (placed.length) {
        placed[0].scrollIntoView({ behavior: "smooth", block: "nearest" });
        placed.forEach(glow);
      }

      notifyCartChanged({
        lineId: lines.length === 1 ? lines[0].cart_line_id : null,
        quantity: lines.length === 1 ? lines[0].quantity : null,
        bump: true,
      });
    };

    if (catchDelay > 0) {
      window.setTimeout(show, catchDelay);
    } else {
      show();
    }
  }

  /* Quick add */

  root.querySelectorAll("[data-cart-quick-add]").forEach((form) => {
    const select = form.querySelector("select");

    if (!select) {
      return;
    }

    function reset() {
      delete form.dataset.submitting;
      form.classList.remove("is-adding");

      if (select.tomselect) {
        select.tomselect.unlock();
        select.tomselect.clear(true);
      } else {
        select.value = "";
      }
    }

    select.addEventListener("change", async () => {
      if (!select.value || form.dataset.submitting) {
        return;
      }

      form.dataset.submitting = "true";
      form.classList.add("is-adding");

      if (select.tomselect) {
        select.tomselect.close();
        select.tomselect.blur();
        select.tomselect.lock();
      }

      if (!(await addOffer(form))) {
        // Not added: post it the plain way, so the page comes back with
        // the reason (the same refusal, as a message).
        HTMLFormElement.prototype.submit.call(form);
        return;
      }

      reset();
    });
  });

  /* A previous order's "+" and "Order again": while the post runs the
     button gives way to the catalog's burst (the scoop spins, then the
     bag pops up, or a cross); the lines go in as the bag appears. What
     was left out, or went wrong, is said beside the order. */

  function setNote(form, notes) {
    const order = form.closest("[data-recent-order]");
    const note = order && order.querySelector("[data-recent-order-note]");

    if (!note) {
      return;
    }

    const text = notes.filter(Boolean).join(" ");
    note.textContent = text;
    note.hidden = text === "";
  }

  async function runWithBurst(form, request, onAdded) {
    const button = form.querySelector("[data-cart-burst-button]");
    const status = form.querySelector("[data-cart-burst]");
    let added = null;

    const tracked = async () => {
      added = await request();
      return added;
    };

    if (!window.statusBurst || !button || !status) {
      try {
        await tracked();
        onAdded(added);
        return true;
      } catch (error) {
        setNote(form, [error instanceof Error ? error.message : ""]);
        return false;
      }
    }

    button.hidden = true;
    status.hidden = false;

    const { ok, error } = await window.statusBurst.run(
      status,
      "default",
      tracked,
      {
        onMark: (worked) => {
          if (worked) {
            onAdded(added);
          }
        },
      }
    );

    status.hidden = true;
    button.hidden = false;

    if (!ok) {
      setNote(form, [error instanceof Error ? error.message : ""]);
    }

    return ok;
  }

  root.addEventListener("submit", async (event) => {
    const form = event.target.closest(
      "[data-cart-add-offer], [data-cart-repeat]"
    );

    if (!form) {
      return;
    }

    event.preventDefault();

    if (form.dataset.adding === "true") {
      return;
    }

    form.dataset.adding = "true";
    setNote(form, []);

    if (form.matches("[data-cart-add-offer]")) {
      await runWithBurst(
        form,
        async () => {
          const { response, payload } = await postForm(form);

          if (!response.ok || !payload.ok || !payload.line_html) {
            throw new Error(payload.message || "");
          }

          return payload;
        },
        (payload) => showAddedLines(
          [payload],
          { catchDelay: CART_CATCH_DELAY }
        )
      );
    } else {
      await runWithBurst(
        form,
        async () => {
          const { payload } = await postForm(form);
          const lines = Array.isArray(payload.lines) ? payload.lines : [];
          const notes = Array.isArray(payload.notes) ? payload.notes : [];

          if (!lines.length) {
            throw new Error(notes.join(" "));
          }

          return { lines, notes };
        },
        ({ lines, notes }) => {
          showAddedLines(lines, { catchDelay: CART_CATCH_DELAY });
          setNote(form, notes);
        }
      );
    }

    delete form.dataset.adding;
  });

  /* Trash: remove the line in place (after confirm_action.js's yes). */

  root.addEventListener("submit", async (event) => {
    const form = event.target.closest("[data-current-order-remove]");

    if (!form) {
      return;
    }

    event.preventDefault();

    const line = form.closest("[data-cart-line-id]");

    if (!line || line.dataset.removing) {
      return;
    }

    line.dataset.removing = "true";
    line.classList.add("line--removing");

    try {
      const { response, payload } = await postForm(form);

      // The cart is locked (an open payment): reload to show it.
      if (response.status === 409) {
        window.location.reload();
        return;
      }

      if (!response.ok || !payload.ok) {
        throw new Error(payload.message || "");
      }
    } catch {
      // Post it the plain way: the page comes back with the reason.
      HTMLFormElement.prototype.submit.call(form);
      return;
    }

    line.remove();
    updateEmptyState();

    notifyCartChanged({
      lineId: Number(line.dataset.cartLineId),
      quantity: 0,
    });
  });
});
