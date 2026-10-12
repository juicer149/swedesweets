/*
  Variants and offers on the product edit form
  (templates/ops_portal/products/includes/form_section_variants.html).

  - The EUR / SEK tabs: the editor shows that currency's prices (its
    data-currency; css/variants.css hides the other, still sent).
  - A row's price tag: on, the row turns yellow and its own prices slide
    open (css/variants.css shows them; the slide is js/smooth-details.js's,
    same time and easing); switched on with none typed yet, they start
    from the product's price. Off, they slide shut.
  - Each row says what it sells at in the editor's currency: its own
    prices, or the product's; a channel it is not sold in dims.
  - The trash asks, then the row flashes red and folds away (line_flash.js)
    and is marked for deletion on save; a row not saved yet just goes.
  - "+ Add variant" copies the template row as a new formset form at the
    end of the list, so the button moves down under it.
  - The arrows move a row up or down; the hidden positions are numbered
    1, 2, 3 … so the server keeps the order. The first row's up and the
    last row's down are off.
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
    const signs = { eur: "€", sek: "kr" };
    // The slides running now, by panel.
    const slides = new Map();

    function ownPriceOn(row) {
      const toggle = row.querySelector("[data-variant-own-price]");

      return Boolean(toggle && toggle.checked);
    }

    // What a row sells at, per channel, in the editor's currency.
    function summarize(row) {
      const currency = editor.dataset.currency || "eur";
      const own = ownPriceOn(row);

      row.querySelectorAll("[data-summary-channel]").forEach((line) => {
        const channel = line.dataset.summaryChannel;
        const key = `${channel}_${currency}`;
        const input = own
          ? row.querySelector(`input[name$="-${key}"]`)
          : editor.querySelector(`input[name="product_${key}"]`);
        const value = input ? input.value.trim() : "";
        const sold = row.querySelector(`input[name$="-${channel}"][type="checkbox"]`);

        line.querySelector("[data-summary-value]").textContent = value
          ? `${value} ${signs[currency]}`
          : "—";
        line.classList.toggle("is-off", Boolean(sold && !sold.checked));
      });
    }

    function summarizeAll() {
      rows.querySelectorAll("[data-variant-row]").forEach(summarize);
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

    // The price tag: on, the row's own prices start from the product's
    // (unless it has some already) and slide open; off, they slide shut.
    rows.addEventListener("change", (event) => {
      const toggle = event.target.closest("[data-variant-own-price]");

      if (!toggle) {
        return;
      }

      const row = toggle.closest("[data-variant-row]");

      if (toggle.checked) {
        const own = Array.from(row.querySelectorAll("[data-variant-prices] input[name]"));

        if (!own.some((input) => input.value.trim())) {
          productPrices.forEach((input) => {
            const key = input.name.replace(/^product_/, "");
            const field = row.querySelector(`input[name$="-${key}"]`);

            if (field) {
              field.value = input.value;
            }
          });
        }
      }

      slide(row, toggle.checked);
    });

    editor.addEventListener("input", summarizeAll);
    editor.addEventListener("change", summarizeAll);

    currencyChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        editor.dataset.currency = chip.dataset.currencyChoice;

        currencyChips.forEach((other) => {
          const chosen = other === chip;

          other.setAttribute("aria-selected", String(chosen));
          other.classList.toggle("section-nav__link--active", chosen);
        });

        summarizeAll();
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
      // dirty_form.js listens for input on the form.
      rows.dispatchEvent(new Event("input", { bubbles: true }));
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

    function move(row, step) {
      const target = neighbour(row, step);

      if (!target) {
        return;
      }

      if (step < 0) {
        rows.insertBefore(row, target);
      } else {
        rows.insertBefore(target, row);
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
        summarize(row);

        if (window.lineFlash) {
          window.lineFlash.added(row);
        }

        const label = row.querySelector('input[name$="-label"]');

        if (label) {
          label.focus();
        }
      });
    }

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
    summarizeAll();
  }

  document.querySelectorAll("[data-variant-editor]").forEach(setUp);
})();
