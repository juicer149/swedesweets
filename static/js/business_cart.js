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
 *     their buttons wait for the response, then added rows flash green;
 *   - the empty order shows when the trash (cart.js) took the last
 *     line.
 *
 * The lines and the empty order are both on the page; whichever fits is
 * shown. The navbar cart refreshes on "cart-changed". Without this script
 * the forms post and the page reloads, as before.
 */
(() => {
  const initialized = new WeakSet();
  const quickAddHandlers = new WeakMap();
  function initialize() {
    const root = document.querySelector("[data-current-order]");

    if (!root || initialized.has(root)) return;
    initialized.add(root);

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

    const glow = (line) => window.lineFlash?.added(line);

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

        showAddedLines([payload], payload);
        return true;
      } catch {
        return false;
      }
    }

    // Render confirmed server rows immediately; their green flash and the
    // navbar cart's bump are the feedback, without a separate loading burst.
    function showAddedLines(lines, payload) {
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
        payload,
      });
    }

    /* Resolve the live select when it changes. A journey return replaces the
       form, so no control keeps a handler attached to an earlier instance. */
    quickAddHandlers.set(root, async (form, select) => {
      if (!select.value || form.dataset.submitting) return;
      form.dataset.submitting = "true";
      form.classList.add("is-adding");
      select.tomselect?.close();
      select.tomselect?.blur();
      select.tomselect?.lock();
      if (!(await addOffer(form))) {
        // Native fallback retains server validation and its local notice.
        HTMLFormElement.prototype.submit.call(form);
        return;
      }
      delete form.dataset.submitting;
      form.classList.remove("is-adding");
      if (select.tomselect) {
        select.tomselect.unlock();
        select.tomselect.clear(true);
      } else select.value = "";
    });

    /* Previous-order actions keep their layout while awaiting the server.
       Refusals and unavailable products are reported beside that order. */

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

    async function runAdd(form, request, onAdded) {
      const button = form.querySelector("[data-cart-add-button]");
      if (button) button.disabled = true;
      form.setAttribute("aria-busy", "true");
      try {
        onAdded(await request());
        return true;
      } catch (error) {
        setNote(form, [error instanceof Error ? error.message : ""]);
        return false;
      } finally {
        if (button) button.disabled = false;
        form.removeAttribute("aria-busy");
      }
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
        await runAdd(
          form,
          async () => {
            const { response, payload } = await postForm(form);

            if (!response.ok || !payload.ok || !payload.line_html) {
              throw new Error(payload.message || "");
            }

            return payload;
          },
          (payload) => showAddedLines([payload], payload)
        );
      } else {
        await runAdd(
          form,
          async () => {
            const { payload } = await postForm(form);
            const lines = Array.isArray(payload.lines) ? payload.lines : [];
            const notes = Array.isArray(payload.notes) ? payload.notes : [];

            if (!lines.length) {
              throw new Error(notes.join(" "));
            }

            return { ...payload, lines, notes };
          },
          (payload) => {
            showAddedLines(payload.lines, payload);
            setNote(form, payload.notes);
          }
        );
      }

      delete form.dataset.adding;
    });

    // The trash is cart.js's (both carts): when a line has gone, the empty
    // order shows if it was the last.
    root.addEventListener("cart-line-removed", updateEmptyState);
  }
  function quickAdd(select) {
    if (!select) return;
    initialize();
    const root = select.closest("[data-current-order]");
    const form = select.closest("[data-cart-quick-add]");
    void quickAddHandlers.get(root)?.(form, select);
  }
  document.addEventListener("change", event => {
    if (event.target.matches?.("[data-cart-quick-add] select")) quickAdd(event.target);
  });
  document.addEventListener("submit", event => {
    if (!event.target.matches?.("[data-cart-quick-add]")) return;
    event.preventDefault();
    quickAdd(event.target.querySelector("select"));
  });
  document.addEventListener("DOMContentLoaded", initialize);
  document.addEventListener("cart-editor-ready", initialize);
  initialize();
})();
