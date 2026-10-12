/*
  Help dialogs (templates/includes/ui/help.html): the "?" opens its dialog;
  "Got it", Escape or a click outside it closes it.
*/
(function () {
  "use strict";

  document.addEventListener("click", (event) => {
    const open = event.target.closest("[data-help-open]");

    if (open) {
      const dialog = document.getElementById(open.dataset.helpOpen);

      if (dialog && typeof dialog.showModal === "function") {
        dialog.showModal();
      }

      return;
    }

    const dialog = event.target.closest("dialog.help-dialog");

    if (!dialog) {
      return;
    }

    // "Got it", or the backdrop (the dialog itself, outside its card).
    if (event.target.closest("[data-help-close]") || event.target === dialog) {
      dialog.close();
    }
  });
})();
