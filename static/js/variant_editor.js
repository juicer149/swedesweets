/*
  The Variants tab of the product edit form
  (templates/ops_portal/products/includes/form_tab_variants.html).

  - The lock at the top. Never opened, the rows are disabled and nothing
    of them is sent. Opened, it turns green and the rows can be changed;
    from then on the tab is sent with "Update product". Locked again, the
    rows are only kept out of reach (what was changed is still saved);
    with nothing changed it goes back to sending nothing.
  - The trash asks, then the row flashes red and folds away (line_flash.js)
    and is marked for deletion on save; a row not saved yet just goes.
  - "Add variant" copies the template row as a new formset form.
  - Rows move by dragging the handle or with the arrows; the hidden
    positions are numbered 1, 2, 3 … so the server keeps the order.
*/
(function () {
  "use strict";

  function setUp(editor) {
    const fields = editor.querySelector("[data-variant-fields]");
    const rows = editor.querySelector("[data-variant-rows]");
    const template = editor.querySelector("[data-variant-template]");
    const lock = editor.querySelector("[data-variant-lock]");
    const unlockedFlag = editor.querySelector("[data-variant-unlocked]");
    const add = editor.querySelector("[data-variant-add]");
    const pending = editor.querySelector("[data-variant-pending]");
    const totalForms = editor.querySelector('input[name$="-TOTAL_FORMS"]');

    if (!fields || !rows || !template || !lock || !unlockedFlag || !totalForms) {
      return;
    }

    let open = !fields.disabled;
    let changedSinceOpen = open;
    let dragged = null;

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
      changedSinceOpen = true;
      renumber();
      // dirty_form.js listens for input on the form.
      fields.dispatchEvent(new Event("input", { bubbles: true }));
    }

    function showLock() {
      const label = open ? "Lock variants" : "Unlock to change variants";

      editor.classList.toggle("variant-editor--open", open);

      if (pending) {
        pending.hidden = !editor.classList.contains("variant-editor--held");
      }
      lock.setAttribute("aria-pressed", open ? "true" : "false");
      lock.setAttribute("aria-label", label);
      lock.title = label;
    }

    lock.addEventListener("click", () => {
      if (!open) {
        open = true;
        fields.disabled = false;
        fields.inert = false;
        unlockedFlag.disabled = false;
        editor.classList.remove("variant-editor--held");
        renumber();
      } else if (changedSinceOpen) {
        // Out of reach, but still sent: the changes wait for Save.
        open = false;
        fields.inert = true;
        editor.classList.add("variant-editor--held");
      } else {
        // Nothing changed: back to sending nothing at all.
        open = false;
        fields.disabled = true;
        unlockedFlag.disabled = true;
      }

      showLock();
    });

    fields.addEventListener("input", (event) => {
      if (event.isTrusted) {
        changedSinceOpen = true;
      }
    });

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

      if (handle && open) {
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

      if (!row || !open) {
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

    showLock();
    renumber();
  }

  document.querySelectorAll("[data-variant-editor]").forEach(setUp);
})();
