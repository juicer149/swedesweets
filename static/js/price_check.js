/*
  Price changes on the product edit form
  (templates/ops_portal/products/includes/price_check_dialog.html): the
  server sent the page back with the dialog; it opens at once. "Go back"
  (or Escape) closes it and clears the password, so the next Save asks
  again.
*/
(function () {
  "use strict";

  const dialog = document.querySelector("[data-price-check]");

  if (!dialog || typeof dialog.showModal !== "function") {
    return;
  }

  const password = dialog.querySelector('input[type="password"]');

  function back() {
    if (password) {
      password.value = "";
    }

    if (dialog.open) {
      dialog.close();
    }
  }

  dialog.querySelector("[data-price-check-back]")?.addEventListener("click", back);
  dialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    back();
  });

  dialog.showModal();

  if (password) {
    password.focus();
  }
})();
