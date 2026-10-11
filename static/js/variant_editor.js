/*
  The Variants tab of the product edit form
  (templates/ops_portal/products/includes/form_tab_variants.html).

  - "Change variants" opens the lock: the fieldset is enabled, so its rows
    (and the "unlocked" flag) are sent with the form's Save.
  - "Add variant" copies the template row as a new formset form.
  - Rows move by dragging or with the arrows; every move numbers the
    hidden positions 1, 2, 3 … so the server keeps the order.
*/
(function () {
  "use strict";

  function setUp(editor) {
    const fields = editor.querySelector("[data-variant-fields]");
    const rows = editor.querySelector("[data-variant-rows]");
    const template = editor.querySelector("[data-variant-template]");
    const unlock = editor.querySelector("[data-variant-unlock]");
    const add = editor.querySelector("[data-variant-add]");
    const totalForms = editor.querySelector('input[name$="-TOTAL_FORMS"]');

    if (!fields || !rows || !template || !totalForms) {
      return;
    }

    let dragged = null;

    function renumber() {
      rows.querySelectorAll("[data-variant-row]").forEach((row, index) => {
        const position = row.querySelector("[data-variant-position]");

        if (position) {
          position.value = String(index + 1);
        }
      });
    }

    function changed() {
      renumber();
      // dirty_form.js listens for input on the form.
      fields.dispatchEvent(new Event("input", { bubbles: true }));
    }

    function move(row, step) {
      const target =
        step < 0 ? row.previousElementSibling : row.nextElementSibling;

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

    if (unlock) {
      unlock.addEventListener("click", () => {
        fields.disabled = false;
        unlock.hidden = true;
        renumber();

        const first = fields.querySelector('input[type="text"]');

        if (first) {
          first.focus();
        }
      });
    }

    if (add) {
      add.addEventListener("click", () => {
        const index = Number(totalForms.value);
        const html = template.innerHTML.replace(/__prefix__/g, String(index));
        const holder = document.createElement("div");

        holder.innerHTML = html.trim();

        const row = holder.firstElementChild;

        rows.appendChild(row);
        totalForms.value = String(index + 1);
        changed();

        const label = row.querySelector('input[type="text"]');

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
      } else if (event.target.closest("[data-variant-drop]")) {
        // A row not saved yet: just take it away. TOTAL_FORMS keeps its
        // count; the server skips the missing index.
        row.remove();
        changed();
      }
    });

    // Only the handle starts a drag, so text in the fields still selects.
    rows.addEventListener("pointerdown", (event) => {
      const handle = event.target.closest("[data-variant-handle]");

      if (handle && !fields.disabled) {
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

      if (!row || fields.disabled) {
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
