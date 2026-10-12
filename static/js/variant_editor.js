/*
  Variants and offers on the product edit form
  (templates/ops_portal/products/includes/form_section_variants.html).

  - The EUR / SEK tabs: the editor shows that currency's prices (its
    data-currency; css/variants.css hides the other, still sent).
  - A row's price tag: on, the yellow tab with its own prices slides out
    under the card (css/variants.css shows it; the slide is
    js/smooth-details.js's, same time and easing); off, it slides back.
    Each own price field shows the product's price as its placeholder: left
    empty, that is the price.
  - The trash asks, then the row flashes red and folds away (line_flash.js)
    and is marked for deletion on save; a row not saved yet just goes.
  - "+ Add variant" copies the template row as a new formset form at the
    end of the list, so the button moves down under it.
  - The arrows move a row up or down, gliding: it passes over its
    neighbour, which slides under it into its place. Or the grip between
    the arrows: drag the row to its place. The hidden positions are
    numbered 1, 2, 3 … so the server keeps the order. The first row's up
    and the last row's down are off.
*/
(function () {
  "use strict";

  function setUp(editor) {
    const rows = editor.querySelector("[data-variant-rows]");
    const template = editor.querySelector("[data-variant-template]");
    const add = editor.querySelector("[data-variant-add]");
    const totalForms = editor.querySelector('input[name$="-TOTAL_FORMS"]');
    const currencyChips = editor.querySelectorAll("[data-currency-choice]");

    if (!rows || !template || !totalForms) {
      return;
    }

    // The product's price fields (product_retail_eur …).
    const productPrices = Array.from(
      editor.querySelectorAll(".variant-shared input[name]")
    );

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    // The slides running now, by panel.
    const slides = new Map();

    // Each own price field shows the product's price: empty, that is it.
    function placeholders(row) {
      productPrices.forEach((input) => {
        const key = input.name.replace(/^product_/, "");
        const field = row.querySelector(`[data-variant-prices] input[name$="-${key}"]`);

        if (field) {
          field.placeholder = input.value.trim() || "0.00";
        }
      });
    }

    function placeholdersAll() {
      rows.querySelectorAll("[data-variant-row]").forEach(placeholders);
    }

    // The row's own prices slide open or shut (as js/smooth-details.js).
    function slide(row, open) {
      const panel = row.querySelector("[data-variant-prices]");

      if (!panel || reducedMotion.matches) {
        return;
      }

      // Turned back mid-slide: on from where it got to.
      const running = slides.get(panel);
      const from = running ? panel.getBoundingClientRect().height : null;

      if (running) {
        slides.delete(panel);
        running.cancel();
      }

      // Shutting: kept shown until the slide ends (the CSS hides it at once).
      panel.classList.toggle("is-closing", !open);

      const full = panel.scrollHeight;
      const start = from ?? (open ? 0 : full);
      const animation = panel.animate(
        [
          { height: `${start}px`, opacity: open ? 0 : 1 },
          { height: `${open ? full : 0}px`, opacity: open ? 1 : 0 },
        ],
        { duration: 280, easing: "cubic-bezier(0.2, 0, 0, 1)" },
      );

      slides.set(panel, animation);
      panel.style.overflow = "hidden";
      animation.onfinish = () => {
        if (slides.get(panel) !== animation) {
          return;
        }

        slides.delete(panel);
        panel.style.overflow = "";
        panel.classList.remove("is-closing");
      };
    }

    // The price tag: the tab slides out (on) or back (off).
    rows.addEventListener("change", (event) => {
      const toggle = event.target.closest("[data-variant-own-price]");

      if (toggle) {
        slide(toggle.closest("[data-variant-row]"), toggle.checked);
      }
    });

    editor.addEventListener("input", placeholdersAll);

    currencyChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        editor.dataset.currency = chip.dataset.currencyChoice;

        currencyChips.forEach((other) => {
          const chosen = other === chip;

          other.setAttribute("aria-selected", String(chosen));
          other.classList.toggle("section-nav__link--active", chosen);
        });
      });
    });

    function visibleRows() {
      return Array.from(rows.querySelectorAll("[data-variant-row]")).filter(
        (row) => !row.hidden
      );
    }

    function renumber() {
      const visible = visibleRows();

      visible.forEach((row, index) => {
        const position = row.querySelector("[data-variant-position]");
        const up = row.querySelector("[data-variant-up]");
        const down = row.querySelector("[data-variant-down]");

        if (position) {
          position.value = String(index + 1);
        }

        if (up) {
          up.disabled = index === 0;
        }

        if (down) {
          down.disabled = index === visible.length - 1;
        }
      });
    }

    function changed() {
      renumber();
      // dirty_form.js compares the fields again (the positions and the
      // delete marks are tracked hidden fields).
      const form = editor.closest("form");

      if (form) {
        form.dispatchEvent(new Event("dirty-form:refresh"));
      }
    }

    function isNewRow(row) {
      const id = row.querySelector("[data-variant-id]");

      return !id || !id.value;
    }

    function rowName(row) {
      const label = row.querySelector('input[name$="-label"]');

      return (
        row.dataset.variantName
        || (label && label.value.trim())
        || "this variant"
      );
    }

    async function trash(row) {
      if (!isNewRow(row) && window.confirmDialog) {
        const sure = await window.confirmDialog(
          `Delete ${rowName(row)}? It goes when you save the product.`,
          {
            title: "Delete variant",
            confirmLabel: "Delete",
            cancelLabel: "Keep it",
          }
        );

        if (!sure) {
          return;
        }
      }

      if (window.lineFlash) {
        await window.lineFlash.remove(row);
      }

      if (isNewRow(row)) {
        // Not saved yet: just take it away. TOTAL_FORMS keeps its count;
        // the server skips the missing index.
        row.remove();
      } else {
        const remove = row.querySelector("[data-variant-delete]");

        if (remove) {
          remove.value = "on";
        }

        row.hidden = true;
      }

      changed();
    }

    function neighbour(row, step) {
      let next = step < 0 ? row.previousElementSibling : row.nextElementSibling;

      while (next && next.hidden) {
        next = step < 0 ? next.previousElementSibling : next.nextElementSibling;
      }

      return next;
    }

    // Rows that changed place glide there from where they were (FLIP):
    // `mutate` moves them in the list; `skip` is left as it is (the row
    // being dragged, which follows the pointer).
    const GLIDE = { duration: 220, easing: "cubic-bezier(0.2, 0, 0, 1)" };

    function glide(mutate, skip = null) {
      const before = new Map(
        visibleRows().map((row) => [row, row.getBoundingClientRect().top])
      );

      mutate();

      if (reducedMotion.matches) {
        return;
      }

      before.forEach((top, row) => {
        const dy = top - row.getBoundingClientRect().top;

        if (row === skip || Math.abs(dy) <= 0.5) {
          return;
        }

        row.animate(
          [{ transform: `translateY(${dy}px)` }, { transform: "none" }],
          GLIDE
        );

        // A neighbour making way casts a light shadow of its own; the row
        // that moves (variant-row--moving) is lifted over it.
        if (!row.classList.contains("variant-row--moving")) {
          row.classList.add("variant-row--gliding");
          window.setTimeout(
            () => row.classList.remove("variant-row--gliding"),
            GLIDE.duration
          );
        }
      });
    }

    function swap(row, step) {
      const target = neighbour(row, step);

      if (!target) {
        return false;
      }

      if (step < 0) {
        rows.insertBefore(row, target);
      } else {
        rows.insertBefore(target, row);
      }

      return true;
    }

    // An arrow: the row glides over its neighbour, which glides under it
    // into its place.
    function move(row, step) {
      let moved = false;

      row.classList.add("variant-row--moving");
      glide(() => {
        moved = swap(row, step);
      });
      window.setTimeout(
        () => row.classList.remove("variant-row--moving"),
        GLIDE.duration
      );

      if (!moved) {
        return;
      }

      changed();

      // Moving the row drops the focus: back on the same arrow, or on the
      // other one once this one is off (the row reached an end).
      const same = row.querySelector(step < 0 ? "[data-variant-up]" : "[data-variant-down]");
      const other = row.querySelector(step < 0 ? "[data-variant-down]" : "[data-variant-up]");
      const focus = same && !same.disabled ? same : other;

      if (focus) {
        focus.focus();
      }
    }

    if (add) {
      add.addEventListener("click", () => {
        const index = Number(totalForms.value);
        const holder = document.createElement("div");

        holder.innerHTML = template.innerHTML
          .replace(/__prefix__/g, String(index))
          .trim();

        const row = holder.firstElementChild;

        rows.appendChild(row);
        totalForms.value = String(index + 1);
        changed();
        placeholders(row);

        if (window.lineFlash) {
          window.lineFlash.added(row);
        }

        const label = row.querySelector('input[name$="-label"]');

        if (label) {
          label.focus();
        }
      });
    }

    // The grip between the arrows: the row lifts and follows the pointer;
    // passing a neighbour's middle, they change places (the neighbour
    // glides); let go, it settles into its place.
    let drag = null;

    function dragOffset(event) {
      return event.clientY - drag.startY;
    }

    rows.addEventListener("pointerdown", (event) => {
      const grip = event.target.closest("[data-variant-grip]");

      if (!grip || event.button !== 0) {
        return;
      }

      event.preventDefault();
      grip.setPointerCapture(event.pointerId);

      const row = grip.closest("[data-variant-row]");

      drag = {
        row,
        grip,
        pointerId: event.pointerId,
        startY: event.clientY,
        order: visibleRows(),
      };
      row.classList.add("variant-row--dragging");
    });

    rows.addEventListener("pointermove", (event) => {
      if (!drag || event.pointerId !== drag.pointerId) {
        return;
      }

      // Layout places (offsetTop), not what shows: a neighbour still
      // gliding would otherwise look unpassed and swap straight back.
      // They change places once the row's middle passes the neighbour's.
      const { row } = drag;
      const middle = row.offsetTop + dragOffset(event) + row.offsetHeight / 2;

      for (const step of [-1, 1]) {
        const other = neighbour(row, step);

        if (!other) {
          continue;
        }

        const otherMiddle = other.offsetTop + other.offsetHeight / 2;
        const passed = step < 0 ? middle < otherMiddle : middle > otherMiddle;

        if (passed) {
          // Keep the row under the pointer as its place in the list moves.
          const place = row.offsetTop;

          glide(() => swap(row, step), row);
          drag.startY += row.offsetTop - place;
          break;
        }
      }

      row.style.transform = `translateY(${dragOffset(event)}px)`;
    });

    function drop(event) {
      if (!drag || event.pointerId !== drag.pointerId) {
        return;
      }

      const { row, order } = drag;
      const offset = dragOffset(event);

      drag = null;
      row.style.transform = "";

      if (!reducedMotion.matches && offset) {
        row.animate(
          [{ transform: `translateY(${offset}px)` }, { transform: "none" }],
          GLIDE
        );
      }

      window.setTimeout(
        () => row.classList.remove("variant-row--dragging"),
        reducedMotion.matches ? 0 : GLIDE.duration
      );

      const now = visibleRows();

      if (now.some((each, index) => each !== order[index])) {
        changed();
      }
    }

    rows.addEventListener("pointerup", drop);
    rows.addEventListener("pointercancel", drop);

    rows.addEventListener("click", (event) => {
      const row = event.target.closest("[data-variant-row]");

      if (!row) {
        return;
      }

      if (event.target.closest("[data-variant-up]")) {
        move(row, -1);
      } else if (event.target.closest("[data-variant-down]")) {
        move(row, 1);
      } else if (event.target.closest("[data-variant-trash]")) {
        trash(row);
      }
    });

    renumber();
    placeholdersAll();
  }

  document.querySelectorAll("[data-variant-editor]").forEach(setUp);
})();
