/*
  Add batch: a product with several variants (sizes, weights) shows its
  variants as chips under the product
  (templates/ops_portal/inventory/includes/form_tab_batch.html). Until one
  is chosen the other fields of the tab wait, muted and out of reach; a
  product with one variant goes straight on as before.

  The product select (Tom Select) dispatches a native change event.
*/
(function () {
  "use strict";

  function setUp(grid) {
    const product = grid.querySelector('select[name="product"]');
    const choice = grid.querySelector("[data-batch-variant]");

    if (!product || !choice) {
      return;
    }

    const groups = Array.from(
      choice.querySelectorAll("[data-batch-variant-for]")
    );
    const waiting = Array.from(grid.children).filter(
      (field) =>
        field !== choice
        && !field.contains(product)
        && field.classList.contains("form-field")
    );

    function activeGroup() {
      return groups.find(
        (group) => group.dataset.batchVariantFor === product.value
      );
    }

    function update() {
      const group = activeGroup();

      groups.forEach((other) => {
        const shown = other === group;

        other.hidden = !shown;

        if (!shown) {
          other.querySelectorAll("input").forEach((input) => {
            input.checked = false;
          });
        }
      });

      choice.hidden = !group;

      const chosen = group && group.querySelector("input:checked");
      const wait = Boolean(group) && !chosen;

      waiting.forEach((field) => {
        field.classList.toggle("batch-form__waiting", wait);
        field.inert = wait;
      });
    }

    product.addEventListener("change", update);
    choice.addEventListener("change", update);
    update();
  }

  document.querySelectorAll("[data-batch-form]").forEach(setUp);
})();
