/*
  The password once more (templates/includes/ui/password_again_dialog.html,
  accounts/password_again.py): the server sent the page back with the
  dialog; it opens at once. "Go back" (or Escape) closes it and clears the
  password, so the next try asks again.
*/
(function () {
  "use strict";

  const dialog = document.querySelector("[data-password-again]");

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

  dialog.querySelector("[data-password-again-back]")?.addEventListener("click", back);
  dialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    back();
  });

  dialog.showModal();

  if (password) {
    password.focus();
  }
})();
