// The product's picture on its edit form (form_section_product.html): the
// round button opens the file picker; the chosen picture shows in the
// circle at once and a small cross undoes the choice (the old picture
// back, nothing sent). Saved with the product, replacing the old one.
(() => {
  document.querySelectorAll("[data-product-picture]").forEach((picture) => {
    const input = picture.querySelector("[data-product-picture-input]");
    const image = picture.querySelector("[data-product-picture-image]");
    const empty = picture.querySelector("[data-product-picture-empty]");
    const undo = picture.querySelector("[data-product-picture-undo]");

    if (!input || !image || !undo) {
      return;
    }

    const original = image.dataset.originalSrc || "";
    let preview = null;

    function show(src) {
      if (preview) {
        URL.revokeObjectURL(preview);
        preview = null;
      }

      image.src = src;
      image.hidden = !src;

      if (empty) {
        empty.hidden = Boolean(src);
      }
    }

    input.addEventListener("change", () => {
      const file = input.files && input.files[0];

      if (!file) {
        show(original);
        undo.hidden = true;
        return;
      }

      show("");
      preview = URL.createObjectURL(file);
      image.src = preview;
      image.hidden = false;

      if (empty) {
        empty.hidden = true;
      }

      undo.hidden = false;
    });

    undo.addEventListener("click", () => {
      input.value = "";
      show(original);
      undo.hidden = true;
      // dirty_form.js compares the field again (empty: as it came).
      input.dispatchEvent(new Event("change", { bubbles: true }));
    });
  });
})();
