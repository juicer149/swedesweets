/*
  Variants and prices on the product edit form
  (templates/ops_portal/products/includes/form_section_variants.html).

  - The EUR / SEK chips: the table shows that currency's prices (the
    editor's data-currency; css/variants.css hides the other, still sent).
  - Each saved row's lock is form_lock.js's; a row's trash sits behind it.
  - The trash asks, then the row flashes red and folds away (line_flash.js)
    and is marked for deletion on save; a row not saved yet just goes.
  - "Add variant" copies the template row as a new formset form, open.
  - Rows move by dragging the handle or with the arrows; the hidden
    positions are numbered 1, 2, 3 … so the server keeps the order.
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

    let dragged = null;

    currencyChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        editor.dataset.currency = chip.dataset.currencyChoice;

        currencyChips.forEach((other) => {
          other.setAttribute("aria-pressed", String(other === chip));
        });
      });
    });

    function visibleRows() {
      return Array.from(rows.querySelectorAll("[data-variant-row]")).filter(
        (row) => !row.hidden
      );
    }

    function renumber() {
      visibleRows().forEach((row, index) => {
        const position = row.querySelector("[data-variant-position]");

        if (position) {
          position.value = String(index + 1);
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

    // Only the handle starts a drag, so text in the fields still selects.
    rows.addEventListener("pointerdown", (event) => {
      const handle = event.target.closest("[data-variant-handle]");

      if (handle) {
        handle.closest("[data-variant-row]").draggable = true;
      }
    });

    document.addEventListener("pointerup", () => {
      rows.querySelectorAll("[data-variant-row]").forEach((row) => {
        if (row !== dragged) {
          row.draggable = false;
        }
      });
    });

    rows.addEventListener("dragstart", (event) => {
      const row = event.target.closest("[data-variant-row]");

      if (!row) {
        event.preventDefault();
        return;
      }

      dragged = row;
      row.classList.add("variant-row--dragging");
      event.dataTransfer.effectAllowed = "move";
    });

    rows.addEventListener("dragover", (event) => {
      if (!dragged) {
        return;
      }

      event.preventDefault();

      const over = event.target.closest("[data-variant-row]");

      if (!over || over === dragged) {
        return;
      }

      const box = over.getBoundingClientRect();
      const after = event.clientY > box.top + box.height / 2;

      rows.insertBefore(dragged, after ? over.nextElementSibling : over);
    });

    rows.addEventListener("dragend", () => {
      if (dragged) {
        dragged.classList.remove("variant-row--dragging");
        dragged.draggable = false;
        dragged = null;
        changed();
      }
    });

    renumber();
  }

  document.querySelectorAll("[data-variant-editor]").forEach(setUp);
})();
