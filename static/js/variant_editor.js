/*
  Variants and offers on the product edit form
  (templates/ops_portal/products/includes/form_section_variants.html).

  - The EUR / SEK tabs: the editor shows that currency's prices (its
    data-currency; css/variants.css hides the other, still sent).
  - The price-per-variant button: shows the rows' price lines
    (data-individual).
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

    // Price per variant: on, each row's price line shows and the shared
    // line becomes "All variants", empty (what it held waits, and comes
    // back if switched off again); off, the shared line is the product's
    // price again.
    const individual = editor.querySelector("[data-individual-prices]");
    const shared = Array.from(
      editor.querySelectorAll(".variant-shared input[name]")
    );

    if (individual) {
      individual.addEventListener("change", () => {
        editor.dataset.individual = String(individual.checked);

        // Off with nothing waiting (the page came with prices per
        // variant): the first variant's prices become the product's, so
        // a save does not empty them all.
        const firstRow = visibleRows()[0];

        shared.forEach((input) => {
          if (individual.checked) {
            input.dataset.productPrice = input.value;
            input.value = "";
          } else if ("productPrice" in input.dataset) {
            input.value = input.dataset.productPrice;
          } else if (firstRow) {
            const key = input.name.replace(/^all_/, "");
            const own = firstRow.querySelector(`input[name$="-${key}"]`);

            input.value = own ? own.value : "";
          }
        });
      });
    }

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
  }

  document.querySelectorAll("[data-variant-editor]").forEach(setUp);
})();
