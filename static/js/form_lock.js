/*
  Locks that keep hands off a part of a form (includes/ui/lock_button.html):
  the product's data, each saved variant. A lock sits in a [data-lock-scope]
  with the part it guards, [data-lockable]. Closed, that part is inert:
  nothing in it can be focused or changed, but its fields are still sent as
  they were, so saving leaves it as it is. Opened, the lock turns green and
  the cursor goes to the part's first field.
*/
(function () {
  "use strict";

  function setOpen(button, open) {
    const scope = button.closest("[data-lock-scope]");
    const part = scope && scope.querySelector("[data-lockable]");

    if (!part) {
      return;
    }

    const what = button.dataset.lockWhat || "this";
    const label = open ? `Lock ${what}` : `Unlock to change ${what}`;

    part.inert = !open;
    scope.classList.toggle("is-unlocked", open);
    button.setAttribute("aria-pressed", String(open));
    button.setAttribute("aria-label", label);
    button.title = label;

    if (open) {
      const field = part.querySelector(
        "input:not([type=hidden]):not([readonly]), select, textarea"
      );

      if (field) {
        field.focus({ preventScroll: true });
      }
    }
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-lock-button]");

    if (!button) {
      return;
    }

    setOpen(button, button.getAttribute("aria-pressed") !== "true");
  });
})();
