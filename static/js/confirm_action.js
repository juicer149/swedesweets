"use strict";

/*
 * Ask before a button does something that is easy to hit by mistake
 * (the trash at the end of a product line, next to the + of the
 * quantity stepper). Any button with data-confirm="message" opens the
 * calm confirm dialog (confirm_dialog.js) first; only "yes" lets the
 * click through, to its form or to the page's own script.
 *
 *   data-confirm          the question
 *   data-confirm-title    dialog title
 *   data-confirm-label    the red button ("Remove")
 *   data-confirm-cancel   the quiet way back ("Keep")
 *
 * Without JavaScript, or without the dialog script, the click just
 * happens as before.
 */

(() => {
  document.addEventListener(
    "click",
    async (event) => {
      const button = event.target.closest("[data-confirm]");

      if (!button || !window.confirmDialog) {
        return;
      }

      if (button.dataset.confirmed === "true") {
        delete button.dataset.confirmed;
        return;
      }

      // Capture phase: stop the click before the form or any page script
      // sees it, and replay it once the answer is yes.
      event.preventDefault();
      event.stopImmediatePropagation();

      const confirmed = await window.confirmDialog(button.dataset.confirm, {
        title: button.dataset.confirmTitle,
        confirmLabel: button.dataset.confirmLabel,
        cancelLabel: button.dataset.confirmCancel,
      });

      if (confirmed) {
        button.dataset.confirmed = "true";
        button.click();
      }
    },
    true
  );
})();
